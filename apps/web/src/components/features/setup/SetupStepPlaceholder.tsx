import { Button } from "@components/ui/button"
import _ from "@lib/translate"
import { SetupStepFooter, SetupStepHeader } from "./SetupStepLayout"
import { getSetupStepTitle, type SetupStepName, type SetupStepProps } from "./steps"

/** Stand-in until the step's real form lands. The workspace step can't be skipped. */
export const SetupStepPlaceholder = ({ step, isLast, finishing, onDone, onSkip }: SetupStepProps & { step: SetupStepName }) => (
    <div className="flex flex-1 flex-col">
        <SetupStepHeader title={getSetupStepTitle(step)} description={_("This step is being built.")} />
        <SetupStepFooter onSkip={step === "workspace" ? undefined : onSkip} disabled={finishing}>
            <Button size="md" onClick={() => onDone()} loading={finishing}>
                {isLast ? _("Complete setup") : _("Continue")}
            </Button>
        </SetupStepFooter>
    </div>
)
