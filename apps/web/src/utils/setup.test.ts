import { afterEach, describe, expect, it, vi } from "vitest"
import { keepSetupPendingInDev } from "./setup"

const storage = (value: string | null) => ({ getItem: () => value })

afterEach(() => {
    vi.unstubAllGlobals()
    vi.unstubAllEnvs()
})

describe("keepSetupPendingInDev", () => {
    it("holds setup pending in a dev build with the key set", () => {
        vi.stubEnv("DEV", true)
        vi.stubGlobal("localStorage", storage("1"))
        expect(keepSetupPendingInDev()).toBe(true)
    })

    it("does nothing without the key", () => {
        vi.stubEnv("DEV", true)
        vi.stubGlobal("localStorage", storage(null))
        expect(keepSetupPendingInDev()).toBe(false)
    })

    it("never holds it in a production build", () => {
        vi.stubEnv("DEV", false)
        vi.stubGlobal("localStorage", storage("1"))
        expect(keepSetupPendingInDev()).toBe(false)
    })
})
