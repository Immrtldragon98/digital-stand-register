import os
import resource
import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.user import User

router = APIRouter()
PROCESS_STARTED = time.time()


@router.get("/status")
def system_status(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    database_bytes = int(db.execute(text("SELECT pg_database_size(current_database())")).scalar() or 0)
    counts = {}
    for key, table in {
        "stands": "stand_assets",
        "installations": "stand_installations",
        "stand_events": "stand_campaign_events",
        "component_preparations": "stand_component_preparations",
        "spares": "inventory_items",
        "users": "users",
        "knowledge_documents": "knowledge_documents",
    }.items():
        try:
            counts[key] = int(db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
        except Exception:
            db.rollback()
            counts[key] = None

    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports ru_maxrss in KiB. Render runs Linux containers.
    memory_bytes = int(rss_kb * 1024)
    return {
        "api": "OK",
        "database": "OK",
        "database_bytes": database_bytes,
        "process_peak_memory_bytes": memory_bytes,
        "process_uptime_seconds": int(max(0, time.time() - PROCESS_STARTED)),
        "pid": os.getpid(),
        "counts": counts,
        "note": "Memory is backend process peak RSS, not total Render host memory.",
    }
