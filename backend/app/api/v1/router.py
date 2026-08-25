from fastapi import APIRouter
from app.api.routes import auth, dashboard, operations, stands, entry_guides, activity, reports, inventory, import_report

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(operations.router, prefix="/operations", tags=["Operations"])
api_router.include_router(stands.router, prefix="/stands", tags=["Stands"])
api_router.include_router(entry_guides.router, prefix="/entry-guides", tags=["Entry Guides"])
api_router.include_router(activity.router, prefix="/activity", tags=["Activity Logs"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(import_report.router, prefix="/import-report", tags=["Import Report"])
