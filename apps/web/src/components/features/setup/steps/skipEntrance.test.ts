import { describe, expect, it } from "vitest"
import { skipEnters } from "./skipEntrance"

describe("skipEnters", () => {
    it("animates Skip when it appears after a step without one", () => {
        expect(skipEnters({ previousHadSkip: false, hasSkip: true })).toBe(true)
    })

    it("leaves Skip still when the step before had one too", () => {
        expect(skipEnters({ previousHadSkip: true, hasSkip: true })).toBe(false)
    })

    it("has nothing to animate without Skip", () => {
        expect(skipEnters({ previousHadSkip: false, hasSkip: false })).toBe(false)
        expect(skipEnters({ previousHadSkip: true, hasSkip: false })).toBe(false)
    })
})
