"""
Dashboard API endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard/stats", response_model=dict)
async def get_dashboard_stats():
    """
    Get dashboard statistics
    """
    # TODO: Implement dashboard stats in Phase 3
    return {
        "total_cameras": 0,
        "active_alerts": 0,
        "total_people": 0
    }

