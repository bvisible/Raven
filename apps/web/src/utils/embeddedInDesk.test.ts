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
