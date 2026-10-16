import { Button } from "@components/ui/button"
import _ from "@lib/translate"

type StepFooterProps = {
    /** Shown when the step can be skipped */
    onSkip?: () => void
    disabled?: boolean
    /** The step's main button; stretched to fill the row */
    children: React.ReactNode
}

/** Skip beside a full-width main button. Back lives at the top of the column. */
export const StepFooter = ({ onSkip, disabled, children }: StepFooterProps) => (
    <div className="flex items-center gap-2 pt-4">
        {onSkip && (
            <Button type="button" variant="ghost" size="md" onClick={onSkip} disabled={disabled}>
                {_("Skip")}
            </Button>
        )}
        <div className="flex flex-1 [&>button]:w-full">{children}</div>
    </div>
)
