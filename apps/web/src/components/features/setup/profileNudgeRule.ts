/** Asks for a photo until there is one; adding it ends the nudge everywhere, "Not now" on this device. */
export const shouldShowProfileNudge = ({ setupOpen, hasProfile, hasPhoto, dismissed, settingsOpen, isMobile }: {
    setupOpen: boolean
    hasProfile: boolean
    hasPhoto: boolean
    dismissed: boolean
    settingsOpen: boolean
    isMobile: boolean
}) => !setupOpen && hasProfile && !hasPhoto && !dismissed && !settingsOpen && !isMobile
