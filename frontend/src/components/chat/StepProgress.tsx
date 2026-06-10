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

/** Map V1 PlanningRuntime stage ids to legacy graph step ids for the progress bar. */
const RUNTIME_STAGE_TO_STEP_ID: Record<string, (typeof STEPS)[number]["id"]> = {
  collect: "collect_requirements",
  prepare_base_context: "collect_requirements",
  retrieve_evidence: "plan_destination",
  tool_enrich: "plan_destination",
  domain_plan: "plan_destination",
  integrate: "build_itinerary",
  verify: "build_itinerary",
  approve_or_revise: "approval_node",
  finalize: "final_response",
};

function resolveStepId(currentStep: string): string {
  return RUNTIME_STAGE_TO_STEP_ID[currentStep] ?? currentStep;
}

type StepProgressProps = {
  currentStep: string | null;
};

export function StepProgress({ currentStep }: StepProgressProps) {
  if (!currentStep || currentStep === "inject_user_memory") {
    return null;
  }

  const activeIndex = STEPS.findIndex((step) => step.id === resolveStepId(currentStep));

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
