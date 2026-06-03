"""演示 step_config 与 render_step_prompt"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.prompts.loader import render_step_prompt
from app.graph.step_config import (
    assert_step_requirements,
    get_step_config_sync,
    list_planning_steps,
)


def main() -> None:
    state = {
        "user_requirement": {
            "departure_date": "2025-10-01",
            "travel_days": 5,
            "adult_count": 2,
            "children_count": 0,
            "budget_min": 3000,
            "budget_max": 6000,
            "budget_level": "comfort",
            "travel_styles": ["culture", "food"],
        },
        "selected_destination": "成都",
        "selected_transport": "flight",
        "selected_accommodation_types": ["economy_hotel"],
        "selected_food_types": ["specialty", "local"],
        "budget": {"total": 12500},
    }

    print("=== 步骤列表 ===")
    for item in list_planning_steps():
        print(f"  {item['order']}. {item['step']} ({item['label']})")

    print("\n=== STEP_CONFIG keys ===")
    print(list(get_step_config_sync().keys()))

    print("\n=== assert_step_requirements('plan_transport') ===")
    print(assert_step_requirements("plan_transport", state))

    print("\n=== render_step_prompt('plan_destination') 前 400 字 ===")
    prompt = render_step_prompt("plan_destination", state)
    print(prompt[:400])
    print("...")

    print("\n=== render_step_prompt('build_itinerary') 前 300 字 ===")
    print(render_step_prompt("build_itinerary", state)[:300])
    print("...")


if __name__ == "__main__":
    main()
