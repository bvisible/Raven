import { Check } from "lucide-react"
import { Checkbox } from "@components/ui/checkbox"
import { GroupedAvatars } from "@components/ui/grouped-avatars"
import _ from "@lib/translate"
import type { SiteUser } from "../types"

type SiteUsersBoxProps = {
    users: SiteUser[]
    added: boolean
    /** "Acme and #general", or "Acme" when the channel was skipped */
    where: string
    checked: boolean
    onCheckedChange: (checked: boolean) => void
}

/** People imported on install: in Raven, but in no workspace until added here. */
export const SiteUsersBox = ({ users, added, where, checked, onCheckedChange }: SiteUsersBoxProps) => (
    <section aria-label={_("Already on this site")} className="flex flex-col gap-3 rounded-md border border-outline-gray-2 p-3">
        <div className="flex min-w-0 items-center gap-3">
            <GroupedAvatars users={users.map((user) => ({ name: user.user, full_name: user.full_name, user_image: user.user_image }))} max={3} size="sm" />
            <div className="flex min-w-0 flex-col gap-1">
                <p className="text-base-medium text-ink-gray-8">
                    {users.length === 1 ? _("1 person already has Raven") : _("{0} people already have Raven", [String(users.length)])}
                </p>
                <p className="text-p-sm text-ink-gray-5">{_("From this site's users. Not in a workspace yet.")}</p>
            </div>
        </div>
        {added ? (
            <p className="flex items-center gap-2 text-sm text-ink-gray-7">
                <Check className="size-4 shrink-0 text-ink-green-6" aria-hidden />
                {_("Added to {0}", [where])}
            </p>
        ) : (
            <label className="flex cursor-pointer items-center gap-2 text-p-sm-medium text-ink-gray-7">
                <Checkbox checked={checked} onCheckedChange={(value) => onCheckedChange(value === true)} />
                {_("Add them to {0}", [where])}
            </label>
        )}
    </section>
)
