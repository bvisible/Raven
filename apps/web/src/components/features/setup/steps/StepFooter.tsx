import { useContext, useEffect, useState } from "react"
import { Button } from "@components/ui/button"
import _ from "@lib/translate"
import { cn } from "@lib/utils"
import { SkipMemoryContext, skipEnters } from "./skipEntrance"

type StepFooterProps = {
    /** Shown when the step can be skipped */
    onSkip?: () => void
    disabled?: boolean
    /** The step's main button; stretched to fill the row */
    children: React.ReactNode
}

/** Skip beside a full-width main button, held at the bottom of the step. The page keeps it still while the step changes. */
export const StepFooter = ({ onSkip, disabled, children }: StepFooterProps) => {
    const memory = useContext(SkipMemoryContext)
    const [enters] = useState(() => skipEnters({ previousHadSkip: memory?.current ?? true, hasSkip: !!onSkip }))
    useEffect(() => {
        if (memory) memory.current = !!onSkip
    }, [memory, onSkip])

    return (
        <div data-slot="step-footer" className="mt-auto flex items-center pt-4">
            {onSkip && (
                // The gap lives inside the clipped column, so the main button slides over as Skip opens.
                <div className={cn("grid shrink-0 grid-cols-[1fr]", enters && "animate-setup-skip-in")}>
                    <div className="min-w-0 overflow-hidden">
                        <div className="flex pe-2">
                            <Button type="button" variant="ghost" size="md" onClick={onSkip} disabled={disabled}>
                                {_("Skip")}
                            </Button>
                        </div>
                    </div>
                </div>
            )}
            <div className="flex flex-1 [&>button]:w-full">{children}</div>
        </div>
    )
}
