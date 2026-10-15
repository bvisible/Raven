import { describe, expect, it } from "vitest"
import { getSetupSteps } from "./steps"

describe("getSetupSteps", () => {
    it("creates the workspace and channel before inviting into them", () => {
        expect(getSetupSteps({ canInvite: true, hrInstalled: false })).toEqual(["workspace", "channel", "invite"])
    })

    it("adds the HR step last when Frappe HR is installed", () => {
        expect(getSetupSteps({ canInvite: true, hrInstalled: true })).toEqual(["workspace", "channel", "invite", "hr"])
    })

    it("drops the invite step for admins who can't create users", () => {
        expect(getSetupSteps({ canInvite: false, hrInstalled: true })).toEqual(["workspace", "channel", "hr"])
    })
})
