import { describe, expect, it } from "vitest"
import { getSetupSteps } from "./steps"

describe("getSetupSteps", () => {
    it("creates the workspace and channel before adding the team", () => {
        expect(getSetupSteps({ hasTeamStep: true, hrInstalled: false })).toEqual(["workspace", "channel", "team"])
    })

    it("adds the HR step last when Frappe HR is installed", () => {
        expect(getSetupSteps({ hasTeamStep: true, hrInstalled: true })).toEqual(["workspace", "channel", "team", "hr"])
    })

    it("drops the team step when there's no one to add or invite", () => {
        expect(getSetupSteps({ hasTeamStep: false, hrInstalled: false })).toEqual(["workspace", "channel"])
    })
})
