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
