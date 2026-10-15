import { useAtom, useAtomValue } from "jotai"
import { useLocalStorage } from "usehooks-ts"
import useCurrentRavenUser from "@raven/lib/hooks/useCurrentRavenUser"
import { settingsDialogOpenTab } from "@components/features/settings/settingsDialogAtom"
import { Button } from "@components/ui/button"
import { useIsMobile } from "@hooks/use-mobile"
import _ from "@lib/translate"
import { shouldShowProfileNudge } from "./profileNudgeRule"
import { setupOpenAtom } from "./setupAtoms"

/**
 * "Set up your profile" beside the rail avatar, after setup and on anyone's first open.
 * A plain card, not a popover: a dismissable layer would swallow every Escape in the app
 * (the editor's included) for as long as it's up.
 */
export const ProfileNudge = ({ children }: { children: React.ReactNode }) => {
    const setupOpen = useAtomValue(setupOpenAtom)
    const [settingsTab, setSettingsTab] = useAtom(settingsDialogOpenTab)
    const { myProfile } = useCurrentRavenUser()
    const [dismissed, setDismissed] = useLocalStorage("raven_profile_nudge_dismissed", false)
    const isMobile = useIsMobile()

    const open = shouldShowProfileNudge({
        setupOpen,
        hasProfile: !!myProfile,
        hasPhoto: !!myProfile?.user_image,
        dismissed,
        settingsOpen: settingsTab !== "",
        isMobile,
    })

    return (
        <div className="relative">
            {children}
            {open && (
                <div
                    role="dialog"
                    aria-labelledby="profile-nudge-title"
                    className="absolute bottom-0 start-full z-50 ms-3 flex w-72 flex-col gap-3 rounded-lg border bg-surface-elevation-2 p-4 shadow-xl"
                >
                    <div className="flex flex-col gap-1">
                        <p id="profile-nudge-title" className="text-base-semibold text-ink-gray-9">{_("Set up your profile")}</p>
                        <p className="text-p-sm text-ink-gray-6">{_("So your team knows it's you.")}</p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="solid" onClick={() => setSettingsTab("profile")}>
                            {_("Edit profile")}
                        </Button>
                        <Button variant="ghost" onClick={() => setDismissed(true)}>
                            {_("Not now")}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}
