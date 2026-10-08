//// Neoffice — added file (no upstream equivalent): Raven's dates in the account's language (maintenance#1324).
//// Upstream never sets a dayjs locale, so the day separators read « 25th November 2025 » and the month names stayed
//// English for a French account. The boot carries the account's language (frappe.boot.lang).
import dayjs from "dayjs"
import "dayjs/locale/de"
import "dayjs/locale/fr"
import "dayjs/locale/it"

// The languages Neoffice ships besides English. Anything else keeps dayjs' English.
const SUPPORTED = ["de", "fr", "it"]

/** Sets dayjs' locale from a language code (`fr`, `de-CH`…) and returns the one it took. */
export function setDateLocale(lang: string | null | undefined): string {
    const base = (lang || "en").toLowerCase().split(/[-_]/)[0]
    const locale = SUPPORTED.includes(base) ? base : "en"
    dayjs.locale(locale)
    return locale
}
