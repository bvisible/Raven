import { describe, expect, it } from "vitest"
import { getSetupSteps } from "./steps"

describe("getSetupSteps", () => {
    it("invites first, then workspace and channel", () => {
        expect(getSetupSteps({ hrInstalled: false })).toEqual(["invite", "workspace", "channel"])
    })

    it("adds the HR step last when Frappe HR is installed", () => {
        expect(getSetupSteps({ hrInstalled: true })).toEqual(["invite", "workspace", "channel", "hr"])
    })
})
