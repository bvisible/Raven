import { ArrowLeft } from "lucide-react"
import { Button } from "@components/ui/button"
import _ from "@lib/translate"

type StepFooterProps = {
    onBack?: () => void
    /** Shown when the step can be skipped */
    onSkip?: () => void
    disabled?: boolean
    /** The step's main button */
    children: React.ReactNode
}

/** Back on the left; Skip and the step's main button on the right. */
export const StepFooter = ({ onBack, onSkip, disabled, children }: StepFooterProps) => (
    <div className="flex items-center gap-2 pt-2">
        {onBack && (
            <Button type="button" variant="ghost" size="md" onClick={onBack} disabled={disabled}>
                <ArrowLeft />
                {_("Back")}
            </Button>
        )}
        <div className="ms-auto flex items-center gap-2">
            {onSkip && (
                <Button type="button" variant="ghost" size="md" onClick={onSkip} disabled={disabled}>
                    {_("Skip")}
                </Button>
            )}
            {children}
        </div>
    </div>
)
