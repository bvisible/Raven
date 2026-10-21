//// Neoffice — added file (no upstream equivalent): when Synk counts as framed by the desk's NeoMail page.
import { afterEach, describe, expect, it, vi } from "vitest"

const SITE = "https://erp.example.org"

/** A window at `address` of SITE, framed by `parent` (null: a tab of its own). */
function windowAt(address: string, parent: unknown = null) {
    const url = new URL(address, SITE)
    const own: Record<string, unknown> = { location: { origin: url.origin, search: url.search, pathname: url.pathname } }
    own.parent = parent ?? own
    own.top = parent ?? own
    return own
}

const deskPage = (origin = SITE) => ({ location: { origin, pathname: "/app/neomail" } })

/** The module as it reads the window when the app starts. */
async function startedIn(win: unknown) {
    vi.stubGlobal("window", win)
    vi.resetModules()
    return import("./embeddedInDesk")
}

afterEach(() => {
    vi.unstubAllGlobals()
})

describe("EMBEDDED_IN_DESK", () => {
    it("is true for a frame of a desk page of the same site that asked for it", async () => {
        const { EMBEDDED_IN_DESK } = await startedIn(windowAt("/raven?embed=desk", deskPage()))
        expect(EMBEDDED_IN_DESK).toBe(true)
    })

    it("is false in a tab of its own, even with the address", async () => {
        const { EMBEDDED_IN_DESK } = await startedIn(windowAt("/raven?embed=desk"))
        expect(EMBEDDED_IN_DESK).toBe(false)
    })

    it("is false for a frame that did not ask", async () => {
        const { EMBEDDED_IN_DESK } = await startedIn(windowAt("/raven", deskPage()))
        expect(EMBEDDED_IN_DESK).toBe(false)
    })

    it("is false for a frame of another site", async () => {
        const elsewhere = {
            get location(): never {
                throw new Error("Blocked a frame with origin from accessing a cross-origin frame.")
            },
        }
        const { EMBEDDED_IN_DESK } = await startedIn(windowAt("/raven?embed=desk", elsewhere))
        expect(EMBEDDED_IN_DESK).toBe(false)
    })

    it("is false for a frame of another origin that can be read", async () => {
        const { EMBEDDED_IN_DESK } = await startedIn(windowAt("/raven?embed=desk", deskPage("https://other.example.org")))
        expect(EMBEDDED_IN_DESK).toBe(false)
    })
})

describe("signInWindow", () => {
    it("is the desk's page around the frame", async () => {
        const desk = deskPage()
        const { signInWindow } = await startedIn(windowAt("/raven?embed=desk", desk))
        expect(signInWindow()).toBe(desk)
    })

    it("is the app's own window otherwise", async () => {
        const own = windowAt("/raven?embed=desk")
        const { signInWindow } = await startedIn(own)
        expect(signInWindow()).toBe(own)
    })
})

describe("LISTS_IN_DESK_MENU", () => {
    it("is true framed by the desk with chrome=menu on the first address", async () => {
        const { LISTS_IN_DESK_MENU } = await startedIn(windowAt("/raven?embed=desk&chrome=menu", deskPage()))
        expect(LISTS_IN_DESK_MENU).toBe(true)
    })

    it("is false without it, and never outside the desk's frame", async () => {
        expect((await startedIn(windowAt("/raven?embed=desk", deskPage()))).LISTS_IN_DESK_MENU).toBe(false)
        expect((await startedIn(windowAt("/raven?chrome=menu", deskPage()))).LISTS_IN_DESK_MENU).toBe(false)
        expect((await startedIn(windowAt("/raven?embed=desk&chrome=menu"))).LISTS_IN_DESK_MENU).toBe(false)
    })
})

describe("showsAllOf", () => {
    it("shows a whole list where the desk's menu asked for all of it", async () => {
        const { showsAllOf } = await startedIn(windowAt("/raven?embed=desk&chrome=menu", deskPage()))
        expect(showsAllOf("?all")).toBe(true)
        expect(showsAllOf("?all=1&x=2")).toBe(true)
        expect(showsAllOf("")).toBe(false)
    })

    it("never does where the desk's menu does not show the lists", async () => {
        const { showsAllOf } = await startedIn(windowAt("/raven?embed=desk", deskPage()))
        expect(showsAllOf("?all")).toBe(false)
    })
})

describe("tellDeskWhere", () => {
    it("tells the desk's page the path, to its origin only", async () => {
        const desk = { ...deskPage(), postMessage: vi.fn() }
        const { tellDeskWhere } = await startedIn(windowAt("/raven?embed=desk", desk))
        tellDeskWhere("/raven/Synk/synk-general")
        expect(desk.postMessage).toHaveBeenCalledWith({ type: "raven:route", path: "/raven/Synk/synk-general" }, SITE)
    })

    it("tells nobody outside the desk's frame", async () => {
        const opener = { ...deskPage(), postMessage: vi.fn() }
        const { tellDeskWhere } = await startedIn(windowAt("/raven", opener))
        tellDeskWhere("/raven/Synk/synk-general")
        expect(opener.postMessage).not.toHaveBeenCalled()
    })
})

describe("deskCommandOf", () => {
    const command = (data: unknown, source: unknown, origin = SITE) => ({ data, source, origin })

    it("takes the settings and the scheduled messages from the desk's page", async () => {
        const desk = deskPage()
        const { deskCommandOf } = await startedIn(windowAt("/raven?embed=desk&chrome=menu", desk))
        expect(deskCommandOf(command({ type: "raven:command", name: "settings.open" }, desk))).toEqual({
            name: "settings.open",
            tab: "profile",
        })
        expect(deskCommandOf(command({ type: "raven:command", name: "settings.open", tab: "channels" }, desk))).toEqual({
            name: "settings.open",
            tab: "channels",
        })
        // A tab it does not know opens the profile
        expect(deskCommandOf(command({ type: "raven:command", name: "settings.open", tab: "<x>" }, desk))).toEqual({
            name: "settings.open",
            tab: "profile",
        })
        expect(deskCommandOf(command({ type: "raven:command", name: "scheduled.open" }, desk))).toEqual({
            name: "scheduled.open",
        })
    })

    it("takes nothing else, from nobody else", async () => {
        const desk = deskPage()
        const { deskCommandOf } = await startedIn(windowAt("/raven?embed=desk&chrome=menu", desk))
        expect(deskCommandOf(command({ type: "raven:command", name: "logout" }, desk))).toBeNull()
        expect(deskCommandOf(command({ type: "other", name: "settings.open" }, desk))).toBeNull()
        expect(deskCommandOf(command("settings.open", desk))).toBeNull()
        expect(deskCommandOf(command({ type: "raven:command", name: "settings.open" }, {}))).toBeNull()
        expect(deskCommandOf(command({ type: "raven:command", name: "settings.open" }, desk, "https://other.example.org"))).toBeNull()
        // Framed by the desk without the lists in its menu: Raven's rail is there, nothing to take
        const plain = deskPage()
        const without = await startedIn(windowAt("/raven?embed=desk", plain))
        expect(without.deskCommandOf(command({ type: "raven:command", name: "settings.open" }, plain))).toBeNull()
    })
})
