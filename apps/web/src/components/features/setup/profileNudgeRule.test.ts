import { describe, expect, it } from "vitest"
import { shouldShowProfileNudge } from "./profileNudgeRule"

const base = { setupOpen: false, hasProfile: true, hasPhoto: false, dismissed: false, settingsOpen: false, isMobile: false }

describe("shouldShowProfileNudge", () => {
    it("shows for someone without a photo", () => expect(shouldShowProfileNudge(base)).toBe(true))
    it("waits for setup to close", () => expect(shouldShowProfileNudge({ ...base, setupOpen: true })).toBe(false))
    it("never shows to someone with a photo", () => expect(shouldShowProfileNudge({ ...base, hasPhoto: true })).toBe(false))
    it("stays away after Not now", () => expect(shouldShowProfileNudge({ ...base, dismissed: true })).toBe(false))
    it("hides while settings are open", () => expect(shouldShowProfileNudge({ ...base, settingsOpen: true })).toBe(false))
    it("waits for the profile to load", () => expect(shouldShowProfileNudge({ ...base, hasProfile: false })).toBe(false))
    it("is desktop only, like the rail", () => expect(shouldShowProfileNudge({ ...base, isMobile: true })).toBe(false))
})
