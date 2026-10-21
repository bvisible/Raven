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
