const STEPS = [
  { id: "collect_requirements", label: "需求" },
  { id: "plan_destination", label: "目的地" },
  { id: "plan_transport", label: "交通" },
  { id: "plan_stay_and_food", label: "食宿" },
  { id: "plan_activities", label: "活动" },
  { id: "build_itinerary", label: "行程" },
  { id: "approval_node", label: "确认" },
  { id: "final_response", label: "完成" },
] as const;

type StepProgressProps = {
  currentStep: string | null;
};

export function StepProgress({ currentStep }: StepProgressProps) {
  if (!currentStep || currentStep === "inject_user_memory") {
    return null;
  }

  const activeIndex = STEPS.findIndex((step) => step.id === currentStep);

  return (
    <nav className="step-progress" aria-label="规划进度">
      <ol className="step-progress-list">
        {STEPS.map((step, index) => {
          const status =
            activeIndex === -1
              ? "pending"
              : index < activeIndex
                ? "done"
                : index === activeIndex
                  ? "active"
                  : "pending";
          return (
            <li
              key={step.id}
              className={`step-progress-item step-progress-item--${status}`}
            >
              <span className="step-progress-dot" aria-hidden />
              <span className="step-progress-label">{step.label}</span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
