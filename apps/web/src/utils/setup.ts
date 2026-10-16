/** Set when the admin finishes or skips setup, so a failed save can't bring the flow back. */
export const SETUP_DONE_STORAGE_KEY = "raven_setup_completed"

/** Boot flags it only for admins on a site that isn't set up. */
export const isSetupPending = (): boolean => {
    if (!window.frappe?.boot?.raven_setup_pending) return false
    try {
        return localStorage.getItem(SETUP_DONE_STORAGE_KEY) !== "1"
    } catch {
        return true
    }
}

export const markSetupDoneLocally = () => {
    try {
        localStorage.setItem(SETUP_DONE_STORAGE_KEY, "1")
    } catch {
        // Storage blocked: the server flag alone ends the flow on the next load.
    }
}

/** The installed app's offline launch reads boot from this cache; keep its onboarded flag in step with the save. */
export const markOnboardedInBootCache = () => {
    try {
        const cached = localStorage.getItem("raven-boot-cache")
        if (!cached) return
        localStorage.setItem("raven-boot-cache", JSON.stringify({ ...JSON.parse(cached), raven_onboarded: 1 }))
    } catch {
        // Corrupt or blocked storage: the next online launch caches a fresh boot.
    }
}
