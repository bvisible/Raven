import { Button } from "@components/ui/button"
import _ from "@lib/translate"

/** Title + description at the top of every setup step. */
export const SetupStepHeader = ({ title, description }: { title: string; description: string }) => (
    <div className="flex flex-col gap-2">
        <h1 className="text-2xl-semibold text-ink-gray-9">{title}</h1>
        <p className="text-p-base text-ink-gray-6">{description}</p>
    </div>
)

/** Pinned to the bottom of the step: the primary action, then "Skip for now" when the step allows it. */
export const SetupStepFooter = ({ children, onSkip, disabled }: {
    children: React.ReactNode
    onSkip?: () => void
    disabled?: boolean
}) => (
    <div className="mt-auto flex flex-col gap-2 pt-8">
        {children}
        {onSkip && (
            <Button variant="ghost" size="md" onClick={onSkip} disabled={disabled}>
                {_("Skip for now")}
            </Button>
        )}
    </div>
)
