//// Neoffice — added file (no upstream equivalent): the tab title of /raven (maintenance#1316).
import { describe, expect, it } from "vitest"
import { tabTitle } from "./DocumentTitle"

describe("tabTitle", () => {
    it("names the open page, then the app", () => {
        expect(tabTitle(0, "général", "Neoffice | Synk")).toBe("général | Neoffice | Synk")
    })

    it("is the app's name alone when no page is open, with no leading separator", () => {
        expect(tabTitle(0, null, "Neoffice | Synk")).toBe("Neoffice | Synk")
    })

    it("counts the unread conversations first, and caps the count", () => {
        expect(tabTitle(3, null, "Synk")).toBe("(3) Synk")
        expect(tabTitle(150, "général", "Synk")).toBe("(99+) général | Synk")
    })
})
