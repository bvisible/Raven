import { useEffect, useState } from "react"
import { useForm, useWatch } from "react-hook-form"
import { useFrappeGetCall } from "frappe-react-sdk"
import { useCreateWorkspace } from "@components/features/workspaces/useCreateWorkspace"
import { Button } from "@components/ui/button"
import ErrorBanner from "@components/ui/error-banner"
import { Form } from "@components/ui/form"
import { DataField, SmallTextField } from "@components/ui/form-elements"
import { useIsMobile } from "@hooks/use-mobile"
import { useWorkspaces, type WorkspaceFields } from "@hooks/useWorkspaces"
import _ from "@lib/translate"
import { ImageUploadField } from "./ImageUploadField"
import { StepFooter } from "./StepFooter"
import type { SetupStepBodyProps } from "../types"

type WorkspaceForm = { workspace_name: string; logo: string; description: string }

/** Mandatory. Created Public and open to join, so the team lands in it. Back here, it edits the same workspace. */
export const WorkspaceStep = (props: SetupStepBodyProps) => {
    const { workspaces, isLoading } = useWorkspaces()
    // Made already but the list isn't in yet: wait, or the form would offer to make another.
    if (props.setup.workspace && isLoading) return null
    const saved = props.setup.workspace ? workspaces.find((workspace) => workspace.name === props.setup.workspace) : undefined
    // Keyed by the saved name, so a rename (or the list arriving) starts the form from what's saved.
    return <WorkspaceForm key={saved?.name ?? "new"} {...props} saved={saved} />
}

const WorkspaceForm = ({ saved, onDone, onSave, onPreview }: SetupStepBodyProps & { saved?: WorkspaceFields }) => {
    const form = useForm<WorkspaceForm>({
        defaultValues: { workspace_name: saved?.workspace_name ?? "", logo: saved?.logo ?? "", description: saved?.description ?? "" },
    })
    // The company from Frappe's setup wizard (ERPNext's slide) is the site's default; a new workspace starts from it.
    const { data: company } = useFrappeGetCall<{ message: { name: string; logo: string | null } | null }>(
        "raven.api.setup.get_company",
        undefined,
        saved ? null : undefined,
        { revalidateOnFocus: false, revalidateIfStale: false },
    )
    const typedName = useWatch({ control: form.control, name: "workspace_name" })
    const typedLogo = useWatch({ control: form.control, name: "logo" })
    useEffect(() => {
        onPreview({ workspace: { name: typedName ?? "", logo: typedLogo || undefined } })
    }, [typedName, typedLogo]) // eslint-disable-line react-hooks/exhaustive-deps
    const { createWorkspace, updateWorkspace, loading, error } = useCreateWorkspace()
    const [uploadingLogo, setUploadingLogo] = useState(false)
    const isMobile = useIsMobile()

    useEffect(() => {
        const suggested = company?.message
        // Only into a form the admin hasn't filled in.
        if (!suggested || saved || form.getValues("workspace_name")) return
        form.reset({ workspace_name: suggested.name, logo: suggested.logo ?? "", description: "" })
    }, [company]) // eslint-disable-line react-hooks/exhaustive-deps

    const onSubmit = ({ workspace_name: typed, logo, description: typedDescription }: WorkspaceForm) => {
        // Trimmed, so "Acme " isn't a different name (and a rename) from "Acme".
        const workspace_name = typed.trim()
        const description = typedDescription.trim()
        // A second Enter before the first save lands would make a second one.
        // Mid-upload, the save would go out without the logo.
        if (loading || uploadingLogo) return
        if (saved && !form.formState.isDirty) return onDone()
        return (saved
            // A rename changes the workspace's name; later steps and the app follow it.
            ? updateWorkspace(saved.name, { workspace_name, logo, description }, (workspace) => onSave({ workspace })).then((workspace) => onDone(workspace !== saved.name ? { workspace } : undefined))
            : createWorkspace({ workspace_name, logo, description, type: "Public", can_only_join_via_invite: 0 })
                .then((workspace) => onDone({ workspace: workspace.name }))
        ).catch(() => { })
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
                <p className="text-p-base text-ink-gray-7">{_("This is how your workspace will appear across Raven.")}</p>
                {error && <ErrorBanner error={error} />}
                <ImageUploadField
                    name="logo"
                    label={_("Workspace logo")}
                    // Before the workspace exists, the file uploads unattached; the save then links it.
                    attachTo={{ doctype: "Raven Workspace", docname: saved?.name ?? "", fieldname: "logo" }}
                    onUploadingChange={setUploadingLogo}
                />
                <DataField
                    name="workspace_name"
                    label={_("Workspace name")}
                    isRequired
                    rules={{ validate: (value) => !!value.trim() || _("Name is required") }}
                    inputProps={{ autoFocus: !isMobile && !saved, placeholder: _("e.g. Acme") }}
                />
                <SmallTextField
                    name="description"
                    label={_("Description (optional)")}
                    inputProps={{ placeholder: _("What does your team do?"), rows: 3 }}
                />
                <StepFooter>
                    <Button type="submit" variant="solid" size="md" loading={loading} disabled={!typedName?.trim() || uploadingLogo}>
                        {!saved ? _("Create workspace") : form.formState.isDirty ? _("Save and continue") : _("Continue")}
                    </Button>
                </StepFooter>
            </form>
        </Form>
    )
}
