import { useEffect, useState } from "react"
import { useForm, useWatch } from "react-hook-form"
import { useFrappeUpdateDoc, type FrappeError } from "frappe-react-sdk"
import useCurrentRavenUser from "@raven/lib/hooks/useCurrentRavenUser"
import type { RavenUser } from "@raven/types/Raven/RavenUser"
import { Button } from "@components/ui/button"
import ErrorBanner from "@components/ui/error-banner"
import { Form } from "@components/ui/form"
import { DataField } from "@components/ui/form-elements"
import { useIsMobile } from "@hooks/use-mobile"
import _ from "@lib/translate"
import { ImageUploadField } from "./ImageUploadField"
import { buildProfileUpdate } from "./profileUpdate"
import { StepFooter } from "./StepFooter"
import type { SetupStepBodyProps } from "../types"

type ProfileForm = { full_name: string; user_image: string }

/** Name and photo, so the team knows who this is. Continue also marks the user onboarded. */
export const ProfileStep = (props: SetupStepBodyProps) => {
    const { myProfile, mutate } = useCurrentRavenUser()
    // The form starts from the saved profile; wait for it.
    if (!myProfile) return null
    return <ProfileFormBody key={myProfile.name} {...props} profile={myProfile} onSaved={() => mutate()} />
}

const ProfileFormBody = ({ isLast, finishing, onDone, onPreview, profile, onSaved }: SetupStepBodyProps & { profile: RavenUser; onSaved: () => void }) => {
    const form = useForm<ProfileForm>({ defaultValues: { full_name: profile.full_name ?? "", user_image: profile.user_image ?? "" } })
    const typedName = useWatch({ control: form.control, name: "full_name" })
    const typedImage = useWatch({ control: form.control, name: "user_image" })
    const { updateDoc, loading, error } = useFrappeUpdateDoc()
    const [uploadingPhoto, setUploadingPhoto] = useState(false)
    const isMobile = useIsMobile()

    useEffect(() => {
        onPreview({ profile: { name: typedName ?? "", image: typedImage || undefined } })
    }, [typedName, typedImage]) // eslint-disable-line react-hooks/exhaustive-deps

    const onSubmit = (values: ProfileForm) => {
        // Mid-upload, the save would go out without the photo.
        if (loading || finishing || uploadingPhoto) return
        updateDoc("Raven User", profile.name, buildProfileUpdate(profile, values))
            .then(() => {
                if (window.frappe?.boot) window.frappe.boot.raven_onboarded = 1
                onSaved()
                onDone()
            })
            .catch(() => { })
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
                <p className="text-p-base text-ink-gray-7">{_("So your team knows it's you.")}</p>
                {error && <ErrorBanner error={error as FrappeError} />}
                <ImageUploadField
                    name="user_image"
                    label={_("Profile picture")}
                    shape="round"
                    attachTo={{ doctype: "Raven User", docname: profile.name, fieldname: "user_image" }}
                    onUploadingChange={setUploadingPhoto}
                />
                <DataField
                    name="full_name"
                    label={_("Full name")}
                    isRequired
                    rules={{
                        validate: (value) => !!value.trim() || _("Name is required"),
                        maxLength: { value: 140, message: _("Name cannot be more than 140 characters.") },
                    }}
                    inputProps={{ autoFocus: !isMobile }}
                />
                <StepFooter disabled={loading || finishing}>
                    <Button type="submit" variant="solid" size="md" loading={loading || finishing} disabled={!typedName?.trim() || uploadingPhoto}>
                        {isLast ? _("Continue to Raven") : _("Continue")}
                    </Button>
                </StepFooter>
            </form>
        </Form>
    )
}
