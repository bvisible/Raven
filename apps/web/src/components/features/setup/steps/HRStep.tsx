import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { useFrappeUpdateDoc } from "frappe-react-sdk"
import { FrappeHRFields } from "@components/features/settings/panels/FrappeHR"
import { Button } from "@components/ui/button"
import ErrorBanner from "@components/ui/error-banner"
import { Form } from "@components/ui/form"
import { useRavenSettings } from "@hooks/fetchers/useRavenSettings"
import _ from "@lib/translate"
import type { RavenSettings } from "@raven/types/Raven/RavenSettings"
import { StepFooter } from "./StepFooter"
import type { SetupStepBodyProps } from "../types"

/** The Frappe HR settings panel's fields, saved the same way (merged over the current doc). */
export const HRStep = ({ completed, isLast, finishing, onDone, onSkip }: SetupStepBodyProps) => {
    const { ravenSettings, mutate } = useRavenSettings()
    const { updateDoc, loading, error } = useFrappeUpdateDoc<RavenSettings>()
    const form = useForm<RavenSettings>()

    useEffect(() => {
        if (ravenSettings) form.reset(ravenSettings)
    }, [ravenSettings]) // eslint-disable-line react-hooks/exhaustive-deps

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
                <p className="text-p-base text-ink-gray-7">{_("Show who's on leave and keep a channel for each department in sync.")}</p>
                {error && <ErrorBanner error={error} />}
                <FrappeHRFields />
                <StepFooter onSkip={completed ? undefined : onSkip} disabled={loading || finishing}>
                    <Button type="submit" variant="solid" size="md" loading={loading || finishing} disabled={!ravenSettings}>
                        {isLast ? _("Continue to Raven") : _("Save and continue")}
                    </Button>
                </StepFooter>
            </form>
        </Form>
    )
}
