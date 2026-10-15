import { useFrappePostCall, useSWRConfig } from "frappe-react-sdk"
import { useSetAtom } from "jotai"
import { useNavigate } from "react-router-dom"
import { lastChannelAtom, lastWorkspaceAtom } from "@utils/lastVisitedAtoms"
import { markSetupDoneLocally } from "@utils/setup"
import type { SetupContext, SetupStepName, StepStatus } from "./steps"

/** Ends the setup flow and opens what it created. */
export const useFinishSetup = () => {
    const { call } = useFrappePostCall("raven.api.setup.complete_setup")
    const { mutate } = useSWRConfig()
    const navigate = useNavigate()
    const setLastWorkspace = useSetAtom(lastWorkspaceAtom)
    const setLastChannel = useSetAtom(lastChannelAtom)

    return async (status: Partial<Record<SetupStepName, StepStatus>>, context: SetupContext) => {
        const withStatus = (value: StepStatus) => Object.keys(status).filter((step) => status[step as SetupStepName] === value)

        // The local flag ends the flow even if this save fails.
        await call({ completed_steps: withStatus("completed"), skipped_steps: withStatus("skipped") }).catch(() => { })
        markSetupDoneLocally()
        // Fresh lists let the new workspace resolve; a failed refresh must not strand the admin here.
        await Promise.all([mutate("workspaces_list"), mutate("channel_list")]).catch(() => { })

        if (!context.workspace) {
            navigate("/", { replace: true })
            return
        }
        setLastWorkspace(context.workspace)
        setLastChannel(context.channel ?? "")
        const workspace = `/${encodeURIComponent(context.workspace)}`
        navigate(context.channel ? `${workspace}/${encodeURIComponent(context.channel)}` : workspace, { replace: true })
    }
}
