import { useContext, useEffect, useState } from "react"
import { useForm, useWatch } from "react-hook-form"
import { FrappeContext, type FrappeConfig, type FrappeError } from "frappe-react-sdk"
import { Button } from "@components/ui/button"
import ErrorBanner from "@components/ui/error-banner"
import { Form } from "@components/ui/form"
import { useWorkspaces } from "@hooks/useWorkspaces"
import { getErrorMessage } from "@lib/frappe"
import _ from "@lib/translate"
import { EMPTY_INVITE, InviteTable, type InviteForm } from "./InviteTable"
import { normalizeEmail } from "./inviteValidation"
import { SiteUsersBox } from "./SiteUsersBox"
import { StepFooter } from "./StepFooter"
import { teamPreviewPeople } from "./teamPreview"
import type { SetupStepBodyProps, SiteUser } from "../types"

type TeamStepProps = SetupStepBodyProps & { siteUsers: SiteUser[]; canInvite: boolean }

/** Adds people already in Raven and invites others by email, into the workspace and channel made earlier. */
export const TeamStep = ({ setup, completed, isLast, finishing, onDone, onSkip, onSave, onPreview, siteUsers, canInvite }: TeamStepProps) => {
    const form = useForm<InviteForm>({ defaultValues: { rows: [EMPTY_INVITE] } })
    const rows = useWatch({ control: form.control, name: "rows" })
    const { invited, addedSiteUsers: addedUsers } = setup
    const [addSiteUsers, setAddSiteUsers] = useState(true)
    const [sending, setSending] = useState(false)
    const [addError, setAddError] = useState<FrappeError | null>(null)
    const { call } = useContext(FrappeContext) as FrappeConfig
    const { workspaces } = useWorkspaces()

    const workspaceName = workspaces.find((workspace) => workspace.name === setup.workspace)?.workspace_name ?? ""
    const where = setup.channel ? _("{0} and #{1}", [workspaceName, setup.channel.name]) : workspaceName
    const added = addedUsers.length > 0
    const shownSiteUsers = added ? addedUsers : siteUsers
    const pendingSiteUsers = siteUsers.length > 0 && addSiteUsers && !added
    const hasFilledRow = rows.some((row) => row.email.trim())
    const somethingToSend = hasFilledRow || pendingSiteUsers

    useEffect(() => {
        onPreview({ people: teamPreviewPeople(rows, invited, shownSiteUsers) })
    }, [rows, shownSiteUsers, invited]) // eslint-disable-line react-hooks/exhaustive-deps

    const label = hasFilledRow && pendingSiteUsers ? _("Add and invite")
        : pendingSiteUsers ? siteUsers.length === 1 ? _("Add 1 person") : _("Add {0} people", [String(siteUsers.length)])
            : hasFilledRow ? _("Send invites")
                : isLast ? _("Continue to Raven") : _("Continue")

    const description = !shownSiteUsers.length
        ? _("They'll get an email to sign in, and are added to {0}.", [where])
        : canInvite
            ? _("Add people already on this site to {0}, and invite others by email.", [where])
            : _("Add people already on this site to {0}.", [where])

    const onSubmit = async ({ rows }: InviteForm) => {
        // A second Enter mid-send would send the same invites again.
        if (sending || finishing) return
        if (!somethingToSend) return onDone()
        setSending(true)
        setAddError(null)
        let nowAdded = addedUsers
        if (pendingSiteUsers) {
            try {
                await call.post("raven.api.setup.add_users_without_workspace", { workspace: setup.workspace, channel: setup.channel?.id })
                nowAdded = siteUsers
                onSave({ addedSiteUsers: siteUsers })
            } catch (error) {
                setAddError(error as FrappeError)
                setSending(false)
                return
            }
        }

        // One at a time: Frappe derives a new user's username from the first name and checks
        // it's free before inserting, so concurrent invites with the same first name collide.
        const filled = rows.flatMap((row, index) => (row.email.trim() ? [{ row, index }] : []))
        const sent: number[] = []
        const failed: { index: number; message: string }[] = []
        for (const { row, index } of filled) {
            try {
                await call.post("raven.api.raven_users.invite_user", {
                    email: row.email.trim(),
                    first_name: row.first_name.trim(),
                    workspaces: [setup.workspace],
                    channels: setup.channel ? [setup.channel.id] : [],
                })
                sent.push(index)
            } catch (error) {
                failed.push({ index, message: getErrorMessage(error as FrappeError) || _("Couldn't send this invite") })
            }
        }
        setSending(false)

        const nowInvited = [...invited, ...sent.map((index) => ({ email: normalizeEmail(rows[index].email), first_name: rows[index].first_name.trim() }))]
        if (failed.length === 0) {
            onDone({ invited: nowInvited, addedSiteUsers: nowAdded })
            return
        }

        // Keep the failed rows, with their errors, and tick the ones that went through.
        onSave({ invited: nowInvited })
        form.reset({ rows: rows.filter((_row, index) => !sent.includes(index)) })
        for (const { index, message } of failed) {
            const shift = sent.filter((sentIndex) => sentIndex < index).length
            form.setError(`rows.${index - shift}.email`, { message })
        }
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
                <p className="text-p-base text-ink-gray-7">{description}</p>
                {addError && <ErrorBanner error={addError} />}
                {shownSiteUsers.length > 0 && (
                    <SiteUsersBox users={shownSiteUsers} added={added} where={where} checked={addSiteUsers} onCheckedChange={setAddSiteUsers} />
                )}
                {canInvite && (
                    <InviteTable invited={invited} label={shownSiteUsers.length ? _("Invite others by email") : _("Invite by email")} />
                )}
                <StepFooter onSkip={completed ? undefined : onSkip} disabled={sending || finishing}>
                    <Button type="submit" variant="solid" size="md" loading={sending || finishing} disabled={!somethingToSend && !completed}>
                        {label}
                    </Button>
                </StepFooter>
            </form>
        </Form>
    )
}
