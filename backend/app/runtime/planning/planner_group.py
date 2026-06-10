"""Domain planner group orchestration."""

from __future__ import annotations

from app.runtime.planning.destination_planner import DestinationPlanner
from app.runtime.planning.route_transport_activity_planner import RouteTransportActivityPlanner
from app.runtime.planning.schemas import PlanProposal
from app.runtime.planning.stay_food_planner import StayFoodPlanner
from app.runtime.state import RuntimeState


class DomainPlannerGroup:
    """Run V1 domain planners in destination-first order."""

    def __init__(
        self,
        *,
        destination_planner: DestinationPlanner | None = None,
        route_transport_activity_planner: RouteTransportActivityPlanner | None = None,
        stay_food_planner: StayFoodPlanner | None = None,
    ) -> None:
        self._destination_planner = destination_planner or DestinationPlanner()
        self._route_planner = route_transport_activity_planner or RouteTransportActivityPlanner()
        self._stay_food_planner = stay_food_planner or StayFoodPlanner()

    def run(self, state: RuntimeState) -> list[PlanProposal]:
        destination_proposal = self._destination_planner.plan(state)
        route_proposal = self._route_planner.plan(state)
        stay_food_proposal = self._stay_food_planner.plan(state)
        return [destination_proposal, route_proposal, stay_food_proposal]
