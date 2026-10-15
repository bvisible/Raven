import { describe, expect, it } from "vitest"
import { getGreetingPeriod, getNextOpenStep, getSetupProgress, getSetupSteps } from "./steps"

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

describe("getNextOpenStep", () => {
    const steps = getSetupSteps({ hasTeamStep: true, hrInstalled: true })

    it("opens the next unsettled step after the one just finished", () => {
        expect(getNextOpenStep(steps, { workspace: "completed" }, "workspace")).toBe("channel")
    })

    it("goes back to an earlier unsettled step when the later ones are done", () => {
        expect(getNextOpenStep(steps, { workspace: "completed", team: "completed", hr: "skipped" }, "hr")).toBe("channel")
    })

    it("returns null once every step is settled", () => {
        expect(getNextOpenStep(steps, { workspace: "completed", channel: "skipped", team: "completed", hr: "completed" }, "team")).toBeNull()
    })
})

describe("getSetupProgress", () => {
    it("counts skipped steps as settled but not done", () => {
        const steps = getSetupSteps({ hasTeamStep: true, hrInstalled: false })
        expect(getSetupProgress(steps, { workspace: "completed", channel: "skipped" })).toEqual({ done: 1, skipped: 1, settled: 2, total: 3 })
    })

    it("ignores statuses of steps that aren't in the list", () => {
        const steps = getSetupSteps({ hasTeamStep: false, hrInstalled: false })
        expect(getSetupProgress(steps, { team: "completed" })).toEqual({ done: 0, skipped: 0, settled: 0, total: 2 })
    })
})

describe("getGreetingPeriod", () => {
    it.each([[5, "morning"], [11, "morning"], [12, "afternoon"], [16, "afternoon"], [17, "evening"], [2, "evening"]] as const)(
        "%i:00 is %s",
        (hour, period) => expect(getGreetingPeriod(hour)).toBe(period),
    )
})
