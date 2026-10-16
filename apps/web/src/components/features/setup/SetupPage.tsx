import { useEffect, useRef, useState } from "react"
import { ArrowLeft } from "lucide-react"
import { createPortal } from "react-dom"
import { useNavigate } from "react-router"
import { useLocalStorage } from "usehooks-ts"
import { useFrappeGetCall, useFrappePostCall } from "frappe-react-sdk"
import { Button } from "@components/ui/button"
import { Progress } from "@components/ui/progress"
import { useWorkspaces } from "@hooks/useWorkspaces"
import { isHRInstalled } from "@lib/apps"
import { hasRole } from "@lib/permissions"
import _ from "@lib/translate"
import { cn } from "@lib/utils"
import { markSetupDoneLocally } from "@utils/setup"
import { getSetupSteps, getSetupStepTitle, type SetupStepName, type StepStatus, type StepStatuses } from "./steps"
import { ChannelStep } from "./steps/ChannelStep"
import { HRStep } from "./steps/HRStep"
import { TeamStep } from "./steps/TeamStep"
import { WorkspaceStep } from "./steps/WorkspaceStep"
import type { SetupState, SetupStepBodyProps, SiteUser } from "./types"
import { prefersReducedMotion, useStepTransition } from "./useStepTransition"

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
    // Fades the page out before it closes onto the app.
    const [leaving, setLeaving] = useState(false)
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
                setLeaving(true)
                window.setTimeout(onFinished, prefersReducedMotion() ? 0 : 250)
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

    const { shown, phase } = useStepTransition(step)
    // A step still fading out can't settle anything, even from an in-flight save.
    const shownProps = shown === step ? props : { ...props, onDone: () => { }, onSkip: () => { } }

    return createPortal(
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="setup-title"
            className={cn("fixed inset-0 z-50 flex bg-surface-base", leaving && "animate-setup-fade-out")}
        >
            {/* The live preview. Decorative, so hidden from assistive tech. */}
            <aside aria-hidden className="hidden min-w-0 overflow-hidden bg-surface-gray-2 lg:flex lg:w-1/2" />
            <main className="relative flex w-full min-w-0 flex-col overflow-y-auto lg:w-1/2 border-s border-outline-gray-1 bg-surface-base px-6 pb-8 lg:px-12">
                <div className="h-14 shrink-0 pt-4">
                    {props.onBack && (
                        <Button variant="ghost" size="md" onClick={props.onBack} disabled={finishing}>
                            <ArrowLeft />
                            {_("Back")}
                        </Button>
                    )}
                </div>
                {/* Whether there's a team step depends on the people list; wait so the steps don't jump. */}
                {!isLoading && (
                    <div className="mx-auto flex w-full max-w-sm flex-1 flex-col gap-6 pt-[12vh] animate-setup-open-late">
                        {steps.length > 1 && (
                            <Progress
                                value={((index + 1) / steps.length) * 100}
                                intervals={steps.length}
                                size="md"
                                ariaLabel={_("Setup progress")}
                            />
                        )}
                        <div
                            key={shown}
                            // A step fading out can't be clicked, typed into or submitted again.
                            inert={phase === "out"}
                            className={cn("flex flex-col gap-2", phase === "out" ? "animate-setup-step-out" : "animate-setup-step-in")}
                        >
                            <h1 id="setup-title" className="text-2xl-semibold text-ink-gray-9">
                                {getSetupStepTitle(shown)}
                            </h1>
                            {shown === "workspace" ? (
                                <WorkspaceStep {...shownProps} />
                            ) : shown === "channel" ? (
                                <ChannelStep {...shownProps} />
                            ) : shown === "team" ? (
                                <TeamStep {...shownProps} siteUsers={siteUsers} canInvite={hasRole("System Manager")} />
                            ) : (
                                <HRStep {...shownProps} />
                            )}
                        </div>
                    </div>
                )}
            </main>
        </div>,
        document.body,
    )
}

export default SetupPage
