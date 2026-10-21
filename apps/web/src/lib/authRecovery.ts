import Cookies from "js-cookie"
//// Neoffice - framed by the desk's NeoMail page, the sign-in replaces the desk's page, not the frame.
import { signInWindow } from "@utils/embeddedInDesk"

/**
 * Runtime recovery from a DEAD SESSION. The boot-time login check in App.tsx
 * only runs once, so a session that expires while the app is open (or an
 * expired session behind the service-worker-cached app shell) would otherwise
 * strand every page on skeletons with no way out.
 *
 * The detector is the user_id cookie, and the server itself keeps it honest:
 * when Frappe fails to resume an expired session it becomes Guest for that
 * request and REWRITES user_id to "Guest" on that very response (LoginManager's
 * resume-failure branch → set_user_info → set_cookie; cookies are flushed even
 * on error responses). So after any failed request, the cookie already carries
 * the server's verdict — no extra "are you alive" request needed. A failure
 * that never reached Frappe (network down, proxy error) leaves the cookie
 * untouched and we correctly do nothing but keep retrying.
 */

/** Same login redirect App.tsx does at boot — returns here after login. */
export const redirectToLogin = () => {
    //// Neoffice - framed by the desk's NeoMail page: the desk's page signs in, and comes back to itself.
    const away = signInWindow()
    away.location.href = `/login?redirect-to=${away.location.pathname}`
}

/** Global SWR onError: side-effect only — SWR's own retry behavior is untouched. */
export const redirectToLoginIfSessionDied = () => {
    if (Cookies.get("user_id") === "Guest") redirectToLogin()
}
