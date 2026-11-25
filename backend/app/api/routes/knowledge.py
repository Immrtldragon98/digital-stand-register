import csv
import hashlib
import io
import re
import zipfile
from pathlib import Path

from docx import Document as DocxDocument
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
from fastapi import Query
from starlette.concurrency import run_in_threadpool

from app.auth.dependencies import require_admin, require_operator
from app.database.session import get_db
from app.models.knowledge_document import KnowledgeChunk, KnowledgeDocument
from app.models.user import User

router = APIRouter()

ALLOWED_CATEGORIES = {"ROD_QUALITY", "EMULSION", "SPARE_USAGE", "FMEA_RCA", "SHIFT_REPORT", "OTHER"}
ALLOWED_SUFFIXES = {".txt", ".md", ".csv", ".xlsx", ".pdf", ".docx"}
MAX_BYTES = 12 * 1024 * 1024
MAX_TEXT = 2_000_000
MAX_ROWS = 100_000
MAX_EXPANDED = 40 * 1024 * 1024


def _bounded_join(parts):
    result=[]; total=0
    for count,part in enumerate(parts,1):
        total+=len(part)+1
        if count>MAX_ROWS or total>MAX_TEXT: raise HTTPException(413,'Document exceeds text processing limits')
        result.append(part)
    return '\n'.join(result)


def _extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type {suffix}. Use TXT, MD, CSV, XLSX, PDF or DOCX.")

    if suffix in {".xlsx", ".docx"}:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            files=archive.infolist()
            if len(files)>5000 or sum(x.file_size for x in files)>MAX_EXPANDED:
                raise HTTPException(413,"Document archive expands beyond processing limits")
    if suffix in {".txt", ".md"}:
        text=data.decode("utf-8", errors="ignore")
        if len(text)>MAX_TEXT: raise HTTPException(413,"Document text exceeds processing limit")
        return text

    if suffix == ".csv":
        text = data.decode("utf-8", errors="ignore")
        rows = csv.reader(io.StringIO(text))
        return _bounded_join(" | ".join(cell.strip() for cell in row) for row in rows)

    if suffix == ".xlsx":
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        try:
            def sheet_lines():
                count = 0
                for ws in wb.worksheets:
                    yield f"SHEET: {ws.title}"
                    for row in ws.iter_rows(values_only=True):
                        count += 1
                        if count > MAX_ROWS:
                            raise HTTPException(413, "Spreadsheet row limit exceeded")
                        values = [str(v).strip() if v is not None else "" for v in row]
                        if any(values):
                            yield " | ".join(values)
            return _bounded_join(sheet_lines())
        finally:
            wb.close()


    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages)>400: raise HTTPException(413,"PDF page limit exceeded")
        return _bounded_join((page.extract_text() or "") for page in reader.pages)

    if suffix == ".docx":
        doc = DocxDocument(io.BytesIO(data))
        return _bounded_join(p.text for p in doc.paragraphs)

    return ""


def _chunks(text: str, size: int = 1600, overlap: int = 250):
    clean = re.sub(r"\r\n?", "\n", text)
    clean = re.sub(r"[ \t]+", " ", clean).strip()
    if not clean:
        return []
    out = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        out.append(clean[start:end])
        if end == len(clean):
            break
        start = max(start + 1, end - overlap)
    return out


@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(KnowledgeDocument,func.count(KnowledgeChunk.id)).outerjoin(KnowledgeChunk).group_by(KnowledgeDocument.id).order_by(KnowledgeDocument.created_at.desc()).limit(1000).all()
    return [{"id": d.id, "filename": d.filename, "category": d.category, "uploaded_by": d.uploaded_by, "created_at": d.created_at, "chunks": count} for d,count in docs]


@router.post("/upload", status_code=201)
async def upload_document(
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    category = category.strip().upper()
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(400, "Unknown document category")
    data = await file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(400, "File is empty")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File is larger than 12 MB")

    return await run_in_threadpool(_index_document, category, file.filename or 'document.txt', data, db, user.username)


def _index_document(category, filename, data, db, username):
    digest = hashlib.sha256(data).hexdigest()
    existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.content_hash == digest).first()
    if existing:
        raise HTTPException(409, f"This document is already imported as {existing.filename}")

    try:
        text = _extract_text(filename, data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Document could not be read. Check the file format.") from None
    chunks = _chunks(text)
    if not chunks:
        raise HTTPException(400, "No readable text was found in the document")

    doc = KnowledgeDocument(filename=filename, category=category, content_hash=digest, uploaded_by=username)
    db.add(doc)
    try:
        db.flush()
        for idx, content in enumerate(chunks):
            db.add(KnowledgeChunk(document_id=doc.id, chunk_index=idx, content=content))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This document was imported concurrently; refresh the document list.") from None
    db.refresh(doc)
    return {"id": doc.id, "filename": doc.filename, "category": doc.category, "chunks": len(chunks), "message": "Document indexed for retrieval"}


@router.get("/search")
def search_knowledge(q: str = Query(...,min_length=1,max_length=1000), limit: int = 8, db: Session = Depends(get_db), _: User = Depends(require_operator)):
    terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_.-]+", q) if len(t) > 2][:16]
    if not terms:
        return []
    chunks = db.query(KnowledgeChunk).options(joinedload(KnowledgeChunk.document)).filter(or_(*[KnowledgeChunk.content.ilike(f"%{term}%") for term in terms])).order_by(KnowledgeChunk.id.desc()).limit(2000).all()
    ranked = []
    for chunk in chunks:
        lower = chunk.content.lower()
        score = sum(lower.count(term) for term in terms)
        if score:
            ranked.append((score, chunk))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [{"score": score, "document_id": c.document_id, "filename": c.document.filename, "category": c.document.category, "chunk_index": c.chunk_index, "content": c.content} for score, c in ranked[:max(1, min(limit, 20))]]


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    doc = db.get(KnowledgeDocument, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "id": document_id}
