"""Graph 条件路由"""

from app.graph.routers.destination_router import (
    create_destination_router,
    run_destination_router,
)

__all__ = ["create_destination_router", "run_destination_router"]
