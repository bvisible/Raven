import { Check } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@components/ui/avatar"
import { Button } from "@components/ui/button"
import { Checkbox } from "@components/ui/checkbox"
import { GroupedAvatars } from "@components/ui/grouped-avatars"
import { Popover, PopoverContent, PopoverTrigger } from "@components/ui/popover"
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
        {/* items-start: View sits in the corner, as far from the top edge as from the right */}
        <div className="flex items-start gap-3">
            <div className="flex min-w-0 flex-1 items-center gap-3">
                <GroupedAvatars users={users.map((user) => ({ name: user.user, full_name: user.full_name, user_image: user.user_image }))} max={3} size="sm" />
                <div className="flex min-w-0 flex-col gap-1">
                    <p className="text-base-medium text-ink-gray-8">
                        {users.length === 1 ? _("1 person already has Raven") : _("{0} people already have Raven", [String(users.length)])}
                    </p>
                    <p className="text-p-sm text-ink-gray-5">{_("From this site's users. Not in a workspace yet.")}</p>
                </div>
            </div>
            <Popover>
                <PopoverTrigger asChild>
                    <Button type="button" variant="ghost" size="sm" className="shrink-0">{_("View")}</Button>
                </PopoverTrigger>
                <PopoverContent align="end" className="w-60 p-1.5">
                    <ul className="max-h-64 overflow-y-auto">
                        {users.map((user) => (
                            <li key={user.user} className="flex items-center gap-2 px-1.5 py-2.5 text-base text-ink-gray-8 md:py-1.5 md:text-sm">
                                <Avatar className="size-5 rounded-full">
                                    <AvatarImage src={user.user_image} alt="" />
                                    <AvatarFallback>{user.full_name.charAt(0).toLocaleUpperCase()}</AvatarFallback>
                                </Avatar>
                                <span className="truncate">{user.full_name}</span>
                            </li>
                        ))}
                    </ul>
                </PopoverContent>
            </Popover>
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
