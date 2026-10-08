//// Neoffice — added file (no upstream equivalent): Raven's dates in the account's language (maintenance#1324).
import { afterEach, describe, expect, it } from "vitest"
import dayjs from "dayjs"
import advancedFormat from "dayjs/plugin/advancedFormat"
import { setDateLocale } from "./dateLocale"

dayjs.extend(advancedFormat)

describe("setDateLocale", () => {
    afterEach(() => {
        dayjs.locale("en")
    })

    it("writes the day separators in French for a French account", () => {
        expect(setDateLocale("fr")).toBe("fr")
        expect(dayjs("2025-11-25").format("Do MMMM YYYY")).toBe("25 novembre 2025")
        expect(dayjs("2025-11-01").format("Do MMMM YYYY")).toBe("1er novembre 2025")
    })

    it("reads a regional language by its base, and keeps English for any other", () => {
        expect(setDateLocale("de-CH")).toBe("de")
        expect(dayjs("2026-10-08").format("D MMMM")).toBe("8 Oktober")
        expect(setDateLocale("pt")).toBe("en")
        expect(setDateLocale(undefined)).toBe("en")
        expect(dayjs("2025-11-25").format("Do MMMM YYYY")).toBe("25th November 2025")
    })
})
