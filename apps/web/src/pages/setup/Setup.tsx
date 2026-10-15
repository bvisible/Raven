import { useEffect, useState } from "react"
import { Navigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { Stepper } from "@components/common/Stepper"
import { SetupPreview } from "@components/features/setup/SetupPreview"
import { SetupStepPlaceholder } from "@components/features/setup/SetupStepPlaceholder"
import { getSetupSteps, getSetupStepTitle, type SetupContext, type SetupStepName, type StepStatus } from "@components/features/setup/steps"
import { useFinishSetup } from "@components/features/setup/useFinishSetup"
import { Button } from "@components/ui/button"
import { Progress } from "@components/ui/progress"
import { isHRInstalled } from "@lib/apps"
import _ from "@lib/translate"
import { isSetupPending } from "@utils/setup"

/** First-admin setup. Only while boot flags it; Frappe's own setup wizard runs first. */
const Setup = () => {
    if (!isSetupPending()) return <Navigate to="/" replace />
    if (!window.frappe?.boot?.setup_complete) return <FrappeSetupRedirect />
    return <SetupFlow />
}

/** Desk sends the user on to Frappe's setup wizard while that's incomplete. */
const FrappeSetupRedirect = () => {
    useEffect(() => window.location.replace("/app"), [])
    return null
}

const SetupFlow = () => {
    const [steps] = useState(() => getSetupSteps({ hrInstalled: isHRInstalled() }))
    const [current, setCurrent] = useState(0)
    const [status, setStatus] = useState<Partial<Record<SetupStepName, StepStatus>>>({})
    const [context, setContext] = useState<SetupContext>({})
    const [finishing, setFinishing] = useState(false)
    const finishSetup = useFinishSetup()

    const step = steps[current]
    const isLast = current === steps.length - 1
    const completed = steps.filter((name) => status[name] === "completed").length

    const finish = (nextStatus: typeof status, nextContext: SetupContext) => {
        setFinishing(true)
        finishSetup(nextStatus, nextContext).finally(() => setFinishing(false))
    }

    const advance = (nextStatus: typeof status, nextContext: SetupContext) => {
        setStatus(nextStatus)
        setContext(nextContext)
        if (isLast) finish(nextStatus, nextContext)
        else setCurrent(current + 1)
    }

    const onDone = (patch?: Partial<SetupContext>) =>
        advance({ ...status, [step]: "completed" }, { ...context, ...patch })

    // A step finished earlier stays completed when skipped on a revisit.
    const onSkip = () =>
        advance(status[step] === "completed" ? status : { ...status, [step]: "skipped" }, context)

    const stepProps = { context, isLast, finishing, onDone, onSkip }

    return (
        <div className="flex min-h-dvh flex-col bg-surface-gray-1">
            {/* Outside AppShell, so DocumentTitle doesn't run here */}
            <title>{`${_("Set up Raven")} | ${(window as { app_name?: string }).app_name || "Raven"}`}</title>
            <header className="flex items-center justify-between gap-4 px-6 py-4">
                <img src="/assets/raven/raven_logo.svg" alt="Raven" className="size-8 shrink-0" />
                <div className="hidden sm:block">
                    <Stepper steps={steps.map((name, index) => ({ id: index + 1, title: getSetupStepTitle(name) }))} currentStep={current} />
                </div>
                {/* Skipping needs a workspace to land in; the last step has its own finish. */}
                {context.workspace && !isLast ? (
                    <Button variant="ghost" size="md" onClick={() => finish(status, context)} disabled={finishing}>
                        {_("Skip setup")}
                    </Button>
                ) : (
                    <span className="w-20" />
                )}
            </header>

            <main className="flex flex-1 justify-center pb-10 sm:items-center sm:px-4">
                <div className="grid w-full max-w-5xl overflow-hidden bg-surface-base sm:rounded-2xl sm:shadow-sm lg:grid-cols-2">
                    <section className="flex min-h-[600px] flex-col gap-6 p-8 sm:p-10">
                        <Progress
                            value={(completed / steps.length) * 100}
                            intervals={steps.length}
                            ariaLabel={_("Setup progress")}
                            hintText={<span className="text-base text-ink-gray-5">{_("Step {0} of {1}", [String(current + 1), String(steps.length)])}</span>}
                        />
                        {current > 0 && (
                            <Button variant="ghost" size="sm" className="self-start" onClick={() => setCurrent(current - 1)} disabled={finishing}>
                                <ArrowLeft />
                                {_("Back")}
                            </Button>
                        )}
                        <SetupStepPlaceholder key={step} step={step} {...stepProps} />
                    </section>
                    <SetupPreview step={step} />
                </div>
            </main>
        </div>
    )
}

export default Setup
