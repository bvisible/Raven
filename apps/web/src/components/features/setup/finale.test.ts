import { describe, expect, it } from "vitest"
import { finaleSchedule } from "./finale"

describe("finaleSchedule", () => {
    it("fades the form out, shows \"Now,\" then \"Send a Raven\", expands the preview, then fades onto the app", () => {
        expect(finaleSchedule({ reducedMotion: false, previewShown: true })).toEqual([
            { at: 0, phase: "out" },
            { at: 250, phase: "now" },
            { at: 950, phase: "now-out" },
            { at: 1150, phase: "send" },
            { at: 1850, phase: "expand" },
            { at: 2450, phase: "leave" },
            { at: 2700, phase: "closed" },
        ])
    })

    it("skips the expansion where there's no preview", () => {
        expect(finaleSchedule({ reducedMotion: false, previewShown: false })).toEqual([
            { at: 0, phase: "out" },
            { at: 250, phase: "now" },
            { at: 950, phase: "now-out" },
            { at: 1150, phase: "send" },
            { at: 1850, phase: "leave" },
            { at: 2100, phase: "closed" },
        ])
    })

    it("swaps the two lines without motion, then the app", () => {
        expect(finaleSchedule({ reducedMotion: true, previewShown: true })).toEqual([
            { at: 0, phase: "now" },
            { at: 700, phase: "send" },
            { at: 1400, phase: "closed" },
        ])
    })
})
