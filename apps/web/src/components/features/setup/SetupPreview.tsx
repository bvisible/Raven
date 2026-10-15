import { Building2, CalendarOff, Globe, Hash, ImageIcon, Mail, UserPlus, Users, type LucideIcon } from "lucide-react"
import _ from "@lib/translate"
import type { SetupStepName } from "./steps"

/** Decorative side panel: what the active step sets up. */
export const SetupPreview = ({ step }: { step: SetupStepName }) => (
    <aside aria-hidden className="hidden flex-col items-center justify-center gap-3 bg-surface-gray-2 p-10 lg:flex">
        {getHighlights(step).map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-2 rounded-lg bg-surface-base px-3 py-2 text-base text-ink-gray-7 shadow-sm">
                <Icon className="size-4 text-ink-gray-5" />
                {label}
            </div>
        ))}
    </aside>
)

const getHighlights = (step: SetupStepName): { icon: LucideIcon; label: string }[] => {
    switch (step) {
        case "invite":
            return [
                { icon: UserPlus, label: _("Invite teammates by email") },
                { icon: Mail, label: _("They get an email to sign in") },
                { icon: Users, label: _("New members join your first workspace") },
            ]
        case "workspace":
            return [
                { icon: Building2, label: _("One place for your whole team") },
                { icon: ImageIcon, label: _("Add a logo so it's easy to spot") },
            ]
        case "channel":
            return [
                { icon: Hash, label: _("Keep conversations organised by topic") },
                { icon: Globe, label: _("Open channels include everyone") },
            ]
        case "hr":
            return [
                { icon: CalendarOff, label: _("See who's on leave today") },
                { icon: Users, label: _("A channel for each department") },
            ]
    }
}
