from fastapi import APIRouter
from app.api.routes import auth, dashboard, operations, stands, entry_guides, activity, reports, inventory, import_report, knowledge, historical, planning

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(operations.router, prefix="/operations", tags=["Operations"])
api_router.include_router(stands.router, prefix="/stands", tags=["Stands"])
api_router.include_router(entry_guides.router, prefix="/entry-guides", tags=["Entry Guides"])
api_router.include_router(activity.router, prefix="/activity", tags=["Activity Logs"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Spare Life"])
api_router.include_router(import_report.router, prefix="/import-report", tags=["Import Report"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge / RAG"])
api_router.include_router(historical.router, prefix="/historical", tags=["Historical Reliability"])
api_router.include_router(planning.router, prefix="/planning", tags=["Planning"])
