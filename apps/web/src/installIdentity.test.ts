//// Neoffice — added file (no upstream equivalent): an installed Synk shows Synk's name and the brand's icons (maintenance#1316).
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

const web = fileURLToPath(new URL("..", import.meta.url))
// The renders of the brand's chat bubble live in neoffice_theme (Streamline's licence keeps them out of this repository).
const SYNK_ICONS = "/assets/neoffice_theme/icons/synk/"

type ManifestIcon = { src: string, sizes: string, purpose?: string }

describe("Synk's install identity", () => {
    it("the manifest names Synk and only the theme's renders of its drawing", () => {
        const manifest = JSON.parse(readFileSync(`${web}public/manifest.webmanifest`, "utf8"))
        expect(manifest.name).toBe("Synk")
        expect(manifest.short_name).toBe("Synk")
        const icons: ManifestIcon[] = manifest.icons
        expect(icons.filter((icon) => !icon.src.startsWith(SYNK_ICONS))).toEqual([])
        expect(icons.filter((icon) => icon.purpose === "maskable").map((icon) => icon.sizes)).toEqual(["192x192", "512x512"])
    })

    it("every iOS launch image is the theme's", () => {
        const html = readFileSync(`${web}index.html`, "utf8")
        const launch = [...html.matchAll(/rel="apple-touch-startup-image"[^>]*?href="([^"]+)"/g)].map((match) => match[1])
        expect(launch.length).toBeGreaterThan(40)
        expect(launch.filter((href) => !href.startsWith(`${SYNK_ICONS}splash/`))).toEqual([])
    })
})
