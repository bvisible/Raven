//// Neoffice — added file (no upstream equivalent): Synk framed by a page of the Neoffice desk.

/**
 * True when this app is framed by a page of the Neoffice desk on the same site that asked for it, with `?embed=desk`
 * on the frame's first address: the desk's NeoMail page (bvisible/frappe_webmail, /app/neomail) shows Synk as one of
 * its views, inside the desk's own menu, so the Neoffice chrome is not drawn a second time inside the frame.
 *
 * Both are needed: the address alone (a link someone followed into a tab) or a frame alone (a page that did not ask)
 * leave the app as it is, and a parent of another site cannot even be read. Read once, as the app starts: the router's
 * first redirect (/raven → /raven/<workspace>) drops the query.
 */
export const EMBEDDED_IN_DESK: boolean = (() => {
    if (typeof window === "undefined" || window.parent === window) return false
    if (new URLSearchParams(window.location.search).get("embed") !== "desk") return false
    try {
        return window.parent.location.origin === window.location.origin
    } catch {
        return false
    }
})()

/**
 * The window a sign-in page replaces. Framed by the desk, the desk's page around the frame: signing in inside the
 * frame would bring the whole desk back within the page, its menu included, and leave the page around it signed out.
 */
export const signInWindow = (): Window => (EMBEDDED_IN_DESK && window.top ? window.top : window)

/**
 * True when, framed by the desk (EMBEDDED_IN_DESK), the desk's own menu shows Synk's lists: `chrome=menu` on the frame's
 * first address, which the desk's NeoMail page adds where its menu can draw a page's navigation. Raven then draws
 * neither its rail nor its list of channels or direct messages beside an open conversation: the menu opens them (the
 * desk's NeoMail page, neomailHost.synkSections). An index page asked for with `?all` (see showsAllOf) shows its list
 * instead, the whole width, as on a phone. Read once, with EMBEDDED_IN_DESK.
 */
export const LISTS_IN_DESK_MENU: boolean =
    EMBEDDED_IN_DESK && new URLSearchParams(window.location.search).get("chrome") === "menu"

/**
 * Whether an index page (a workspace's, the direct messages') shows its whole list rather than opening a conversation:
 * with the desk's menu showing the lists (LISTS_IN_DESK_MENU), when the menu asked for it (`?all` in `search`, the
 * address's query): « all the channels », « all the direct messages », where Raven's own lists start a conversation.
 */
export const showsAllOf = (search: string): boolean => LISTS_IN_DESK_MENU && new URLSearchParams(search).has("all")

/**
 * Tells the desk's page around the frame where Raven is (`path`, the address's path, `/raven/<workspace>/<channel>`),
 * so that its menu lights that conversation: framed by the desk only, and only to a page of the same origin.
 */
export function tellDeskWhere(path: string): void {
    if (!EMBEDDED_IN_DESK) return
    window.parent.postMessage({ type: "raven:route", path }, window.location.origin)
}

/** The settings' tabs the desk's page may open (Raven's SettingsDialog ids); another opens the profile. */
const DESK_SETTINGS_TABS = ["profile", "appearance", "preferences", "sidebar", "workspaces", "channels"] as const

/** What the desk's page may ask Raven to open (deskCommandOf): its settings, at a tab, or its scheduled messages. */
export type DeskCommand =
    | { name: "settings.open"; tab: (typeof DESK_SETTINGS_TABS)[number] }
    | { name: "scheduled.open" }

/**
 * The command a message from the desk's page asks of Raven, framed by the desk with Synk's lists in its menu
 * (LISTS_IN_DESK_MENU): `{type: "raven:command", name: "settings.open", tab?}` (the menu's « Synk settings »: Raven's
 * rail, which opens them, is not drawn) or `{type: "raven:command", name: "scheduled.open"}`. Taken only from the page
 * around the frame (`source`) and from this site (`origin`); anything else is null.
 */
export function deskCommandOf(event: { source: unknown; origin: string; data: unknown }): DeskCommand | null {
    if (!LISTS_IN_DESK_MENU || event.source !== window.parent || event.origin !== window.location.origin) return null
    const data = event.data as { type?: unknown; name?: unknown; tab?: unknown } | null
    if (!data || typeof data !== "object" || data.type !== "raven:command") return null
    if (data.name === "settings.open") {
        const tab = DESK_SETTINGS_TABS.find((known) => known === data.tab) ?? "profile"
        return { name: "settings.open", tab }
    }
    if (data.name === "scheduled.open") return { name: "scheduled.open" }
    return null
}
