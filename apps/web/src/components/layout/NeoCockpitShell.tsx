//// Neoffice — added file (no upstream equivalent). The Frappe-embedded shell for /raven.
//// Replaces the v2 `components/layout/frappe/FrappeLayout.tsx`, which upstream deleted with the
//// whole `frontend/` folder at v3.0.0 (ac601a48f:frontend/src/components/layout/frappe/).
import type { ReactNode } from 'react'
import { NeoCockpit } from '@neoffice/frappe-sidebar-react'
import { useFrappeThemeBridge } from './useFrappeThemeBridge'

/**
 * NeoCockpitShell — the Neoffice chrome around the Raven SPA.
 *
 * `/raven` is a page of Neoffice, not a third-party app opened in a tab: it must carry the same
 * rail, the same app switcher and the same theme as the rest of the product. NeoCockpit
 * (bvisible/frappe-sidebar-react) is the shared chrome that provides all three; it reads
 * `window.frappe.boot`, which `raven/www/raven.py` fills with the curated mini-boot from
 * `raven.api.boot.get_navbar_boot()` rather than the full ~150 KB desk bootinfo.
 *
 * `layout="shell"` (the default) renders the gray frame + rail and puts `children` inside a
 * floating rounded panel. Raven's own `PrimarySidebar` lives INSIDE that panel — the two are not
 * duplicates: the cockpit rail navigates between Neoffice apps, Raven's rail navigates within
 * Raven. That is exactly the v2 arrangement, where the cockpit wrapped a panel containing
 * Raven's `WorkspacesSidebar` + channel list.
 *
 * `onSynk` is deliberately NOT passed: that button opens the docked Raven chat from elsewhere in
 * Neoffice, and here we already are Raven. The lib only renders it when the prop is given.
 */
export function NeoCockpitShell({ children }: { children: ReactNode }) {
	//// Neoffice - the panel must follow the theme of the desk around it, and mirror it onto
	//// <html data-theme>, which is what the injected chrome stylesheets read.
	useFrappeThemeBridge(true)

	return (
		<NeoCockpit env='spa' homeUrl='/app/home'>
			{children}
		</NeoCockpit>
	)
}

/**
 * True when the SPA is served embedded inside Frappe at /raven.
 *
 * `raven/www/raven.html` sets the flag in the inline boot script, BEFORE the bundle loads, so it
 * is readable at module scope. Bracket notation is mandatory: Frappe's Jinja `safe_render`
 * refuses any dot followed by two underscores anywhere in a template as an anti-SSTI guard and
 * answers HTTP 417 — which is what killed /raven for every visitor on 2026-09-03.
 */
export const FRAPPE_INTEGRATION =
	typeof window !== 'undefined' &&
	(window as unknown as { __FRAPPE_INTEGRATION__?: boolean })['__FRAPPE_INTEGRATION__'] === true
