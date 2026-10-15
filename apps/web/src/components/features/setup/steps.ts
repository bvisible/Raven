import _ from "@lib/translate"

export type SetupStepName = "invite" | "workspace" | "channel" | "hr"

export type StepStatus = "completed" | "skipped"

/** Filled in as steps finish; later steps read it. */
export type SetupContext = {
    workspace?: string
    channel?: string
}

export type SetupStepProps = {
    context: SetupContext
    /** The last step's primary action finishes setup */
    isLast: boolean
    /** Finishing is in flight */
    finishing: boolean
    onDone: (patch?: Partial<SetupContext>) => void
    onSkip: () => void
}

/** Invites first; HR last since its company → workspace mapping needs a workspace. */
export const getSetupSteps = ({ hrInstalled }: { hrInstalled: boolean }): SetupStepName[] =>
    hrInstalled ? ["invite", "workspace", "channel", "hr"] : ["invite", "workspace", "channel"]

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
