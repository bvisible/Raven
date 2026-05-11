/**
 * FrappeLayout — Layout used when the SPA is embedded inside Frappe (/raven/*).
 *
 * Frappe-pattern layout: flex-row at the root, sidebar and main as siblings.
 * Navbar lives INSIDE main (not full-width), so it starts right of the sidebar
 * and the app-switcher in the sidebar aligns naturally with the logo in the
 * navbar (same Y=0 modulo padding).
 *
 * The `window.__FRAPPE_INTEGRATION__` flag is set by index.html. If absent
 * (vite standalone dev case), App.tsx falls back to the legacy chrome.
 */
import type { ReactNode } from 'react'
import { FrappeSidebar } from './FrappeSidebar'
import { FrappeNavbar } from './FrappeNavbar'

interface FrappeLayoutProps {
	children: ReactNode
}

export function FrappeLayout({ children }: FrappeLayoutProps) {
	return (
		<div
			className="frappe-desk-root"
			style={{
				display: 'flex',
				flexDirection: 'row',
				alignItems: 'flex-start',
				minHeight: '100vh',
				width: '100%',
			}}
		>
			<FrappeSidebar />
			<main
				className="main-section"
				style={{
					flex: 1,
					height: '100vh',
					overflowY: 'auto',
					position: 'relative',
					minWidth: 0,
				}}
			>
				<FrappeNavbar />
				<div className="page-content">{children}</div>
			</main>
		</div>
	)
}
