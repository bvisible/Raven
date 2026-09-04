//// Neoffice - added file (no upstream equivalent). Frappe-embedded shell for /raven
//// (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven", then 549919c71, 2026-06-10 "feat(cockpit): consume shared NeoCockpit").
//// Replaces the copy-pasted FrappeSidebar.tsx + FrappeNavbar.tsx that the first version shipped.
/**
 * FrappeLayout — Frappe-embedded shell (/raven/*).
 *
 * Now delegates to the shared NeoCockpit chrome (bvisible/frappe-sidebar-react):
 * one sidebar that absorbs the header, gray frame + floating panel around the
 * content. Replaces the old copy-pasted FrappeSidebar.tsx + FrappeNavbar.tsx
 * (deleted). NeoCockpit reads window.frappe.boot (the curated mini-boot) and
 * navigates via window.location.href (env="spa"). Raven's .page-content CSS
 * keeps the chat full-height inside the floating panel.
 */
import type { ReactNode } from 'react'
import { NeoCockpit } from '@neoffice/frappe-sidebar-react'

interface FrappeLayoutProps {
	children: ReactNode
}

export function FrappeLayout({ children }: FrappeLayoutProps) {
	return (
		<NeoCockpit env="spa">
			<div className="page-content">{children}</div>
		</NeoCockpit>
	)
}
