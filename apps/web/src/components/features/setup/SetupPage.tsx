import { useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { useNavigate } from "react-router"
import { useLocalStorage } from "usehooks-ts"
import { useFrappeGetCall, useFrappePostCall } from "frappe-react-sdk"
import { Progress } from "@components/ui/progress"
import { useWorkspaces } from "@hooks/useWorkspaces"
import { isHRInstalled } from "@lib/apps"
import { hasRole } from "@lib/permissions"
import _ from "@lib/translate"
import { markSetupDoneLocally } from "@utils/setup"
import { getSetupSteps, getSetupStepTitle, type SetupStepName, type StepStatus, type StepStatuses } from "./steps"
import { ChannelStep } from "./steps/ChannelStep"
import { HRStep } from "./steps/HRStep"
import { TeamStep } from "./steps/TeamStep"
import { WorkspaceStep } from "./steps/WorkspaceStep"
import type { SetupState, SetupStepBodyProps, SiteUser } from "./types"

const ALL_STEPS: SetupStepName[] = ["workspace", "channel", "team", "hr"]

/**
 * First-admin setup: a full page with one step at a time. Covers the app, which can't
 * take focus meanwhile (its chat composer focuses itself on load).
 */
const SetupPage = ({ onFinished }: { onFinished: () => void }) => {
    const navigate = useNavigate()
    const { data, isLoading } = useFrappeGetCall<{ message: SiteUser[] }>("raven.api.setup.get_users_without_workspace", undefined, undefined, {
        revalidateOnFocus: false,
        revalidateIfStale: false,
    })
    const siteUsers = data?.message ?? []

    // Kept across reloads, so a refresh mid-setup doesn't offer to make a second workspace or channel.
    // Per user, so another admin on the same browser starts their own.
    const [saved, setSaved, clearSaved] = useLocalStorage<{ setup: SetupState; statuses: StepStatuses }>(`raven_setup_progress:${window.frappe?.boot?.user?.name}`, {
        setup: { invited: [], addedSiteUsers: [] },
        statuses: {},
    })
    const { setup, statuses } = saved
    const [current, setCurrent] = useState<SetupStepName>(() => ALL_STEPS.find((step) => !saved.statuses[step]) ?? "workspace")
    const [finishing, setFinishing] = useState(false)
    const { call: completeSetup } = useFrappePostCall("raven.api.setup.complete_setup")

    // Email invites create users, so they need System Manager; anyone can add people already in Raven.
    const hasTeamStep = hasRole("System Manager") || siteUsers.length > 0 || setup.addedSiteUsers.length > 0
    const steps = getSetupSteps({ hasTeamStep, hrInstalled: isHRInstalled() })
    // A step can drop out once the data loads (no one to add); land on the next one still to do.
    const step = steps.includes(current) ? current : steps.find((name) => !statuses[name]) ?? steps[steps.length - 1]
    const index = steps.indexOf(step)
    const isLast = index === steps.length - 1

    // No saved progress here (another device, cleared storage) but setup already made the
    // workspace: on a fresh site the one workspace this admin runs is setup's. Checked once.
    const { workspaces, isLoading: workspacesLoading } = useWorkspaces()
    const checkedWorkspaces = useRef(false)
    useEffect(() => {
        if (workspacesLoading || checkedWorkspaces.current) return
        checkedWorkspaces.current = true
        if (saved.setup.workspace) return
        const administered = workspaces.filter((workspace) => workspace.workspace_member_name && workspace.is_admin)
        if (administered.length !== 1) return
        setSaved({ setup: { ...saved.setup, workspace: administered[0].name }, statuses: { ...saved.statuses, workspace: "completed" } })
        setCurrent((name) => (name === "workspace" ? "channel" : name))
    }, [workspacesLoading]) // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        const app = document.getElementById("root")
        app?.setAttribute("inert", "")
        // The app's shortcuts listen on document and would still open the command menu or
        // settings over this page; keys stop at body. The page's own handlers run before.
        const stop = (event: KeyboardEvent) => event.stopPropagation()
        document.body.addEventListener("keydown", stop)
        document.body.addEventListener("keyup", stop)
        return () => {
            app?.removeAttribute("inert")
            document.body.removeEventListener("keydown", stop)
            document.body.removeEventListener("keyup", stop)
        }
    }, [])

    const finish = (finalSetup: SetupState, finalStatuses: StepStatuses) => {
        setFinishing(true)
        const withStatus = (status: StepStatus) => steps.filter((name) => finalStatuses[name] === status)
        // The local flag ends the flow even if this save fails.
        completeSetup({ completed_steps: withStatus("completed"), skipped_steps: withStatus("skipped") })
            .catch(() => { })
            .finally(() => {
                markSetupDoneLocally()
                clearSaved()
                if (finalSetup.workspace) {
                    const workspace = `/${encodeURIComponent(finalSetup.workspace)}`
                    navigate(finalSetup.channel ? `${workspace}/${encodeURIComponent(finalSetup.channel.id)}` : workspace)
                }
                onFinished()
            })
    }

    const settle = (status: StepStatus, patch?: Partial<SetupState>) => {
        const nextSetup = patch ? { ...setup, ...patch } : setup
        // A step finished before stays finished when skipped on a revisit.
        const nextStatuses = statuses[step] === "completed" ? statuses : { ...statuses, [step]: status }
        setSaved({ setup: nextSetup, statuses: nextStatuses })
        if (isLast) finish(nextSetup, nextStatuses)
        else setCurrent(steps[index + 1])
    }

    const props: SetupStepBodyProps = {
        setup,
        completed: statuses[step] === "completed",
        isLast,
        finishing,
        onBack: index > 0 ? () => setCurrent(steps[index - 1]) : undefined,
        onDone: (patch) => settle("completed", patch),
        onSkip: () => settle("skipped"),
        onSave: (patch) => setSaved((current) => ({ ...current, setup: { ...current.setup, ...patch } })),
    }

    return createPortal(
        // Pinned from the top so the header stays put whatever each step's height.
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-surface-base px-4 pt-[12vh] pb-10">
            {/* Whether there's a team step depends on this list; wait so the step count doesn't jump. */}
            {!isLoading && (
                <div
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="setup-title"
                    className="flex h-fit w-full max-w-md flex-col gap-6"
                >
                    <div className="flex flex-col gap-3">
                        <span className="text-base text-ink-gray-5">{_("Step {0} of {1}", [String(index + 1), String(steps.length)])}</span>
                        <Progress value={(index / steps.length) * 100} intervals={steps.length} size="md" ariaLabel={_("Setup progress")} />
                    </div>
                    <div className="flex flex-col gap-2">
                        <h1 id="setup-title" className="text-2xl-semibold text-ink-gray-9">
                            {getSetupStepTitle(step)}
                        </h1>
                        {step === "workspace" ? (
                            <WorkspaceStep key={step} {...props} />
                        ) : step === "channel" ? (
                            <ChannelStep key={step} {...props} />
                        ) : step === "team" ? (
                            <TeamStep key={step} {...props} siteUsers={siteUsers} canInvite={hasRole("System Manager")} />
                        ) : (
                            <HRStep key={step} {...props} />
                        )}
                    </div>
                </div>
            )}
        </div>,
        document.body,
    )
}

export default SetupPage
