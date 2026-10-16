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

/** Dev builds only: with this key at "1", finishing setup leaves it pending, so the flow can be walked through again. */
export const KEEP_SETUP_PENDING_DEV_KEY = "raven_dev_keep_setup_pending"

export const keepSetupPendingInDev = (): boolean => {
    if (!import.meta.env.DEV) return false
    try {
        return localStorage.getItem(KEEP_SETUP_PENDING_DEV_KEY) === "1"
    } catch {
        return false
    }
}
