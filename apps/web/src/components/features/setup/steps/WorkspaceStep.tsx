import { useEffect } from "react"
import { useForm, useWatch } from "react-hook-form"
import { useFrappeGetCall } from "frappe-react-sdk"
import WorkspaceLogoField from "@components/features/settings/panels/Workspaces/WorkspaceLogoField"
import { useCreateWorkspace } from "@components/features/workspaces/useCreateWorkspace"
import { Button } from "@components/ui/button"
import ErrorBanner from "@components/ui/error-banner"
import { Form } from "@components/ui/form"
import { DataField } from "@components/ui/form-elements"
import { useIsMobile } from "@hooks/use-mobile"
import { useWorkspaces, type WorkspaceFields } from "@hooks/useWorkspaces"
import _ from "@lib/translate"
import { StepFooter } from "./StepFooter"
import type { SetupStepBodyProps } from "../types"

/** `name` is the saved workspace's (the logo upload attaches to it); empty until it's created. */
type WorkspaceForm = { name: string; workspace_name: string; logo: string }

/** Mandatory. Created Public and open to join, so the team lands in it. Back here, it edits the same workspace. */
export const WorkspaceStep = (props: SetupStepBodyProps) => {
    const { workspaces, isLoading } = useWorkspaces()
    // Made already but the list isn't in yet: wait, or the form would offer to make another.
    if (props.setup.workspace && isLoading) return null
    const saved = props.setup.workspace ? workspaces.find((workspace) => workspace.name === props.setup.workspace) : undefined
    // Keyed by the saved name, so a rename (or the list arriving) starts the form from what's saved.
    return <WorkspaceForm key={saved?.name ?? "new"} {...props} saved={saved} />
}

const WorkspaceForm = ({ saved, onDone, onSave }: SetupStepBodyProps & { saved?: WorkspaceFields }) => {
    const form = useForm<WorkspaceForm>({
        defaultValues: { name: saved?.name ?? "", workspace_name: saved?.workspace_name ?? "", logo: saved?.logo ?? "" },
    })
    // ERPNext's setup wizard makes a Company and sets it as the site's default; a new workspace starts from it.
    const { data: company } = useFrappeGetCall<{ message: { name: string; logo: string | null } | null }>(
        "raven.api.setup.get_company",
        undefined,
        saved ? null : undefined,
        { revalidateOnFocus: false, revalidateIfStale: false },
    )
    const typedName = useWatch({ control: form.control, name: "workspace_name" })
    const { createWorkspace, updateWorkspace, loading, error } = useCreateWorkspace()
    const isMobile = useIsMobile()

    useEffect(() => {
        const suggested = company?.message
        // Only into a form the admin hasn't filled in.
        if (!suggested || saved || form.getValues("workspace_name")) return
        form.reset({ name: "", workspace_name: suggested.name, logo: suggested.logo ?? "" })
    }, [company]) // eslint-disable-line react-hooks/exhaustive-deps

    const onSubmit = ({ workspace_name: typed, logo }: WorkspaceForm) => {
        // Trimmed, so "Acme " isn't a different name (and a rename) from "Acme".
        const workspace_name = typed.trim()
        // A second Enter before the first save lands would make a second one.
        if (loading) return
        if (saved && !form.formState.isDirty) return onDone()
        return (saved
            // A rename changes the workspace's name; later steps and the app follow it.
            ? updateWorkspace(saved.name, { workspace_name, logo }, (workspace) => onSave({ workspace })).then((workspace) => onDone(workspace !== saved.name ? { workspace } : undefined))
            : createWorkspace({ workspace_name, logo, type: "Public", can_only_join_via_invite: 0 })
                .then((workspace) => onDone({ workspace: workspace.name }))
        ).catch(() => { })
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
                <p className="text-p-base text-ink-gray-7">{_("Name it after your team or company. Everyone you add joins it.")}</p>
                {error && <ErrorBanner error={error} />}
                {/* self-start: the logo button would otherwise stretch across the column */}
                <div className="self-start">
                    <WorkspaceLogoField menuAlign="start" />
                </div>
                <DataField
                    name="workspace_name"
                    label={_("Workspace name")}
                    isRequired
                    rules={{ validate: (value) => !!value.trim() || _("Name is required") }}
                    inputProps={{ autoFocus: !isMobile && !saved, placeholder: _("e.g. Acme") }}
                />
                <StepFooter>
                    <Button type="submit" variant="solid" size="md" loading={loading} disabled={!typedName?.trim()}>
                        {!saved ? _("Create workspace") : form.formState.isDirty ? _("Save and continue") : _("Continue")}
                    </Button>
                </StepFooter>
            </form>
        </Form>
    )
}
