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
