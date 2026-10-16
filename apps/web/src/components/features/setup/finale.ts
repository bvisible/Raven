/**
 * After the last step: the form leaves, "Now," shows and goes, "Send a Raven" shows and fades
 * while the preview grows into the app, and the page fades onto it.
 */
export type FinalePhase = "out" | "now" | "now-out" | "send" | "expand" | "leave" | "closed"

const OUT_MS = 250
// Each line's blur-in plus a beat to read it.
const LINE_MS = 700
// The step-out blur.
const LINE_OUT_MS = 200
// The `transition-setup-expand` utility in index.css.
const EXPAND_MS = 600
const LEAVE_MS = 250

/** When each phase starts, in ms from the finish. No preview (narrow screens) means nothing to expand. */
export const finaleSchedule = ({ reducedMotion, previewShown }: { reducedMotion: boolean; previewShown: boolean }): { at: number; phase: FinalePhase }[] => {
    if (reducedMotion) return [{ at: 0, phase: "now" }, { at: LINE_MS, phase: "send" }, { at: 2 * LINE_MS, phase: "closed" }]
    const send = OUT_MS + LINE_MS + LINE_OUT_MS
    const leave = send + LINE_MS + (previewShown ? EXPAND_MS : 0)
    return [
        { at: 0, phase: "out" },
        { at: OUT_MS, phase: "now" },
        { at: OUT_MS + LINE_MS, phase: "now-out" },
        { at: send, phase: "send" },
        ...(previewShown ? [{ at: send + LINE_MS, phase: "expand" as const }] : []),
        { at: leave, phase: "leave" },
        { at: leave + LEAVE_MS, phase: "closed" },
    ]
}
