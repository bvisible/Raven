import { lazy, Suspense, useEffect, useState } from "react"
import { useSetAtom } from "jotai"
import { isSetupPending, SETUP_DONE_STORAGE_KEY } from "@utils/setup"
import { setupOpenAtom } from "./setupAtoms"

const SetupPage = lazy(() => import("./SetupPage"))

/** Opens the first-admin setup page while boot flags it. Frappe's own setup wizard runs first. */
export const SetupGate = () => {
    const [open, setOpen] = useState(isSetupPending)
    const setSetupOpen = useSetAtom(setupOpenAtom)
    useEffect(() => setSetupOpen(open), [open, setSetupOpen])

    // Finished in another tab: close here too, or this tab would offer to make it all again.
    useEffect(() => {
        if (!open) return
        const onStorage = (event: StorageEvent) => {
            if (event.key === SETUP_DONE_STORAGE_KEY && event.newValue === "1") setOpen(false)
        }
        window.addEventListener("storage", onStorage)
        return () => window.removeEventListener("storage", onStorage)
    }, [open])

    if (!open) return null
    if (!window.frappe?.boot?.setup_complete) return <FrappeSetupRedirect />
    return (
        <Suspense fallback={null}>
            <SetupPage onFinished={() => setOpen(false)} />
        </Suspense>
    )
}

/** Desk sends the user on to Frappe's setup wizard while that's incomplete. */
const FrappeSetupRedirect = () => {
    useEffect(() => window.location.replace("/app"), [])
    return null
}
