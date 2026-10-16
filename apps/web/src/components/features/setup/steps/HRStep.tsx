import { useEffect } from "react"
import { useForm, useWatch } from "react-hook-form"
import { useFrappeUpdateDoc } from "frappe-react-sdk"
import { X } from "lucide-react"
import { Button } from "@components/ui/button"
import ErrorBanner from "@components/ui/error-banner"
import { Form } from "@components/ui/form"
import { SwitchFormField } from "@components/ui/form-elements"
import { useRavenSettings } from "@hooks/fetchers/useRavenSettings"
import _ from "@lib/translate"
import type { RavenSettings } from "@raven/types/Raven/RavenSettings"
import { StepFooter } from "./StepFooter"
import type { SetupStepBodyProps } from "../types"

/** Frappe HR's leave indicator, saved as the settings panel saves it (merged over the current doc). */
export const HRStep = ({ completed, isLast, finishing, onDone, onSkip, onPreview }: SetupStepBodyProps) => {
    const { ravenSettings, mutate } = useRavenSettings()
    const { updateDoc, loading, error } = useFrappeUpdateDoc<RavenSettings>()
    const form = useForm<RavenSettings>()

    useEffect(() => {
        if (ravenSettings) form.reset(ravenSettings)
    }, [ravenSettings]) // eslint-disable-line react-hooks/exhaustive-deps

    const showLeave = useWatch({ control: form.control, name: "show_if_a_user_is_on_leave" })
    useEffect(() => {
        onPreview({ leave: !!showLeave })
    }, [showLeave]) // eslint-disable-line react-hooks/exhaustive-deps

    const onSubmit = (data: RavenSettings) => {
        if (loading || finishing) return
        if (!ravenSettings) return
        if (!form.formState.isDirty) return onDone()
        updateDoc("Raven Settings", ravenSettings.name, { ...ravenSettings, ...data })
            .then((saved) => {
                mutate(saved, { revalidate: false })
                onDone()
            })
            .catch(() => { })
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
                {/* Frappe HR × Raven. HR's logo is served by hrms, which this step needs installed. */}
                {/* About a line height of room either side: the title-to-body gap is sized for a subtitle. */}
                <div className="mt-3 mb-1 flex items-center gap-3">
                    <img src="/assets/hrms/images/frappe-hr-logo.svg" alt={_("Frappe HR")} className="size-10 animate-setup-join-left" />
                    <X className="size-4 text-ink-gray-5 animate-setup-join-mark" aria-hidden />
                    <img src="/assets/raven/raven_logo.svg" alt={_("Raven")} className="size-10 animate-setup-join-right" />
                </div>
                <p className="text-p-base text-ink-gray-7">{_("Connect Frappe HR to Raven.")}</p>
                {error && <ErrorBanner error={error} />}
                <SwitchFormField
                    name="show_if_a_user_is_on_leave"
                    label={_("Show if a user is on leave")}
                    formDescription={_("Based on today's attendance in Frappe HR.")}
                />
                <StepFooter onSkip={completed ? undefined : onSkip} disabled={loading || finishing}>
                    <Button type="submit" variant="solid" size="md" loading={loading || finishing} disabled={!ravenSettings}>
                        {isLast ? _("Continue to Raven") : _("Save and continue")}
                    </Button>
                </StepFooter>
            </form>
        </Form>
    )
}
