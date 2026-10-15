import _ from "@lib/translate"

export type SetupStepName = "invite" | "workspace" | "channel" | "hr"

export type StepStatus = "completed" | "skipped"

/**
 * Workspace and channel first, so invitees are added straight into them. Invites
 * only for admins who can create users (System Manager). HR maps companies to workspaces.
 */
export const getSetupSteps = ({ canInvite, hrInstalled }: { canInvite: boolean; hrInstalled: boolean }): SetupStepName[] => [
    "workspace",
    "channel",
    ...(canInvite ? ["invite" as const] : []),
    ...(hrInstalled ? ["hr" as const] : []),
]

export const getSetupStepTitle = (step: SetupStepName): string => {
    switch (step) {
        case "invite":
            return _("Invite your team")
        case "workspace":
            return _("Create your workspace")
        case "channel":
            return _("Create your first channel")
        case "hr":
            return _("Connect Frappe HR")
    }
}
