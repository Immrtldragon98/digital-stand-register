"""knowledge documents for RAG

Revision ID: 20260906_knowledge_docs
Revises: 20260906_spare_life
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260906_knowledge_docs"
down_revision = "20260906_spare_life"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("uploaded_by", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_knowledge_documents_category", "knowledge_documents", ["category"])
    op.create_index("ix_knowledge_documents_content_hash", "knowledge_documents", ["content_hash"], unique=True)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"])


def downgrade():
    op.drop_index("ix_knowledge_chunks_document_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_index("ix_knowledge_documents_content_hash", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_category", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
