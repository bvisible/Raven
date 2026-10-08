//// Neoffice — added file (no upstream equivalent): the list timestamps on the user's clock and in their
//// language (maintenance#1324). Upstream wrote « 4:13 PM » and « Nov 25, 2025 » for every account.
import { afterEach, describe, expect, it } from "vitest"
import dayjs from "dayjs"
import { formatCalendarDate, formatRelativeDate, getDateObject, SYSTEM_TIMEZONE } from "./date"
import { setDateLocale } from "./dateLocale"

// The tests run in node: no window, unless a test gives one with a boot.
const boot = (timeFormat?: string) => {
    const scope = globalThis as { window?: unknown }
    if (timeFormat) scope.window = { frappe: { boot: { raven_time_format: timeFormat } } }
    else delete scope.window
}
// A timestamp as the server stores it: the system zone's wall clock.
const stored = (day: dayjs.Dayjs) => day.tz(SYSTEM_TIMEZONE).format("YYYY-MM-DD HH:mm:ss")

describe("formatRelativeDate", () => {
    afterEach(() => {
        boot(undefined)
        setDateLocale("en")
    })

    it("writes a message of today on the 24-hour clock, unless the user chose 12 hours", () => {
        boot("24-hour")
        expect(formatRelativeDate(stored(dayjs()))).toMatch(/^\d{2}:\d{2}$/)
        boot(undefined)
        expect(formatRelativeDate(stored(dayjs()))).toMatch(/^\d{2}:\d{2}$/)
        boot("12-hour")
        expect(formatRelativeDate(stored(dayjs()))).toMatch(/^\d{1,2}:\d{2} (AM|PM)$/)
    })

    it("writes the day before the month for a French account", () => {
        setDateLocale("fr")
        expect(formatRelativeDate("2025-11-25 10:00:00")).toBe("25 nov. 2025")
        const earlier = dayjs().subtract(9, "day")
        if (earlier.isSame(dayjs(), "year")) {
            expect(formatRelativeDate(stored(earlier))).toBe(earlier.format("D MMM"))
        }
    })

    it("keeps upstream's month-first dates in English", () => {
        expect(formatRelativeDate("2025-11-25 10:00:00")).toBe("Nov 25, 2025")
    })
})

describe("formatCalendarDate", () => {
    afterEach(() => {
        setDateLocale("en")
    })

    it("writes the day before the month for a French account, and keeps upstream's English", () => {
        const day = getDateObject("2025-11-25 10:00:00")
        expect(formatCalendarDate(day)).toBe("Nov 25th, 2025")
        expect(formatCalendarDate(day, "MMM D, YYYY")).toBe("Nov 25, 2025")
        setDateLocale("fr")
        // a date read once the account's language is set, as the app reads every date
        expect(formatCalendarDate(getDateObject("2025-11-25 10:00:00"))).toBe("25 nov. 2025")
        // an object made before keeps its language whole: English names in the English order
        expect(formatCalendarDate(day)).toBe("Nov 25th, 2025")
    })
})
