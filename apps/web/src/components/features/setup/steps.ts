import _ from "@lib/translate"

export type SetupStepName = "workspace" | "channel" | "team" | "hr"

export type StepStatus = "completed" | "skipped"

export type StepStatuses = Partial<Record<SetupStepName, StepStatus>>

/**
 * Workspace and channel first, so the team is added straight into them.
 * HR maps companies to workspaces, so it comes last.
 */
export const getSetupSteps = ({ hasTeamStep, hrInstalled }: { hasTeamStep: boolean; hrInstalled: boolean }): SetupStepName[] => [
    "workspace",
    "channel",
    ...(hasTeamStep ? ["team" as const] : []),
    ...(hrInstalled ? ["hr" as const] : []),
]

/** The next step still to do: after `after` first, then any left earlier. */
export const getNextOpenStep = (steps: SetupStepName[], statuses: StepStatuses, after: SetupStepName): SetupStepName | null => {
    const later = steps.slice(steps.indexOf(after) + 1)
    return later.find((step) => !statuses[step]) ?? steps.find((step) => !statuses[step]) ?? null
}

/** A skipped step needs no more doing, so it fills the bar, but it isn't counted as done. */
export const getSetupProgress = (steps: SetupStepName[], statuses: StepStatuses) => {
    const done = steps.filter((step) => statuses[step] === "completed").length
    const skipped = steps.filter((step) => statuses[step] === "skipped").length
    return { done, skipped, settled: done + skipped, total: steps.length }
}

/** Same bands as Frappe's onboarding greeting; the small hours are still the evening before. */
export const getGreetingPeriod = (hour: number): "morning" | "afternoon" | "evening" => {
    if (hour >= 5 && hour < 12) return "morning"
    if (hour >= 12 && hour < 17) return "afternoon"
    return "evening"
}

export const getSetupStepTitle = (step: SetupStepName): string => {
    switch (step) {
        case "workspace":
            return _("Create your workspace")
        case "channel":
            return _("Create your first channel")
        case "team":
            return _("Add your team")
        case "hr":
            return _("Connect Frappe HR")
    }
}
