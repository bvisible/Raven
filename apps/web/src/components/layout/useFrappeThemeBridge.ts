//// Neoffice — added file (no upstream equivalent). Ported from the v2 theme logic that lived
//// inline in `frontend/src/App.tsx` (ac601a48f), rewritten against v3's own ThemeProvider
//// instead of the Radix Themes `appearance` prop, which no longer exists.
import { useEffect, useRef } from 'react'
import { useTheme } from '@components/theme-provider'

type Resolved = 'light' | 'dark'

/**
 * Read the theme Frappe is currently showing, from the SAME-ORIGIN localStorage the desk writes.
 *
 * Frappe keeps two keys and they do NOT always agree:
 *   - `appearance`    the user's PREFERENCE: light | dark | automatic. Sometimes JSON-quoted.
 *   - `theme_active`  a resolved light|dark cache.
 *
 * `appearance` is authoritative and `theme_active` can lag behind it. Measured on osiris
 * 2026-09-22: after switching the desk back to light, `appearance` read "light" and the desk
 * rendered light, while `theme_active` still said "dark" — so an embedded Raven that trusted
 * `theme_active` sat dark inside a light desk. Read the preference first; `theme_active` is only
 * a fallback for the case where no preference was ever written.
 */
function readFrappeTheme(): Resolved | null {
	try {
		const pref = (window.localStorage.getItem('appearance') || '').replace(/^"|"$/g, '')
		if (pref === 'dark' || pref === 'light') return pref
		if (pref === 'automatic') {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
		}

		const active = window.localStorage.getItem('theme_active')
		if (active === 'dark' || active === 'light') return active
	} catch {
		// localStorage throws in a sandboxed or blocked context — the caller falls back.
	}
	return null
}

/** `?theme=dark` wins over everything, so a link can force a rendering. */
function readUrlTheme(): Resolved | null {
	const t = new URLSearchParams(window.location.search).get('theme')
	return t === 'dark' || t === 'light' ? t : null
}

/**
 * Keep the embedded Raven in step with the theme of the Neoffice desk around it.
 *
 * Two things the upstream ThemeProvider cannot do on its own:
 *
 * 1. **Follow Frappe.** Upstream persists its own choice under `raven-theme` and never looks at
 *    the host. Embedded, that gave a glaring white panel inside a dark Neoffice. We adopt
 *    Frappe's theme on mount and whenever the HOST changes it — not on every tick, so a user who
 *    picks a theme in Raven's own Appearance panel keeps it until the desk moves.
 *
 * 2. **Mirror onto `<html data-theme>`.** Upstream toggles the `light`/`dark` CLASS. The two
 *    stylesheets `raven.py` injects for the chrome — `desk.bundle.css` and `neoffice-theme.css` —
 *    key off the ATTRIBUTE instead, so without this the rail stays light under a dark Raven.
 *
 * The 1 s poll is not laziness: `storage` only fires in OTHER tabs, and the desk writing the key
 * in this same tab (cockpit theme toggle) would never be seen otherwise.
 */
export function useFrappeThemeBridge(enabled: boolean) {
	const { setTheme, themeValue } = useTheme()
	const lastHostTheme = useRef<Resolved | null>(null)

	// Adopt the host's theme, then follow it when IT changes.
	useEffect(() => {
		if (!enabled) return

		const initial = readUrlTheme() ?? readFrappeTheme()
		if (initial) setTheme(initial)
		lastHostTheme.current = readFrappeTheme()

		const sync = () => {
			const fresh = readFrappeTheme()
			if (!fresh || fresh === lastHostTheme.current) return
			lastHostTheme.current = fresh
			setTheme(fresh)
		}

		window.addEventListener('storage', sync)
		const id = window.setInterval(sync, 1000)
		return () => {
			window.removeEventListener('storage', sync)
			window.clearInterval(id)
		}
	}, [enabled, setTheme])

	// Mirror the RESOLVED theme onto the attribute the chrome stylesheets read.
	useEffect(() => {
		if (!enabled) return
		document.documentElement.setAttribute('data-theme', themeValue)
	}, [enabled, themeValue])
}
