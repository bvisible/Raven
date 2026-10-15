import { atom } from "jotai"

/** The setup page is on screen; the profile nudge waits for it to close. */
export const setupOpenAtom = atom(false)
