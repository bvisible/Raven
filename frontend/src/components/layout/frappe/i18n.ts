//// Neoffice - added file (no upstream equivalent). Typed wrapper around the window['__']
//// shim declared in index.html (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven").
/**
 * Helper for the `window.__` shim defined in the index.html template.
 *
 * The shim does: lookup in `frappe._messages`, fallback on the source string.
 * Supports positional placeholders `{0}` and the `Source|Context` pattern.
 *
 * Exported as a TypeScript-typed function for React components.
 */
declare global {
	interface Window {
		__?: (text: string, args?: (string | number)[], context?: string) => string
	}
}

export function t(text: string, args?: (string | number)[], context?: string): string {
	if (typeof window === 'undefined' || !window.__) return text
	return window.__(text, args, context)
}
