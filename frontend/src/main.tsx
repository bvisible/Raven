import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import '@radix-ui/themes/styles.css';
import './index.css'

// @ts-ignore
import FrappePushNotification from "../public/frappe-push-notification";


//// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): frappe.model.sync throws when
//// boot.docs is missing, and our curated mini-boot can legitimately omit it. Upstream calls it
//// unguarded, so React never mounted and /raven showed a blank page.
// Defensive sync — frappe.model.sync(frappe.boot.docs) throws when docs is
// missing (the curated mini-boot might omit it on a fresh install before the
// session has loaded meta). React still needs to mount in that case.
function safeSyncDocs() {
  try {
    const w = window as unknown as {
      frappe?: { model?: { sync?: (docs: unknown) => void }; boot?: { docs?: unknown } }
    }
    if (w.frappe?.model?.sync && w.frappe?.boot?.docs) {
      w.frappe.model.sync(w.frappe.boot.docs)
    }
  } catch (e) {
    console.warn('[raven] frappe.model.sync failed, continuing without docs:', e)
  }
}

const registerServiceWorker = () => {
  // @ts-ignore
  window.frappePushNotification = new FrappePushNotification("raven")

  if ("serviceWorker" in navigator) {
    // @ts-ignore
    window.frappePushNotification
      .appendConfigToServiceWorkerURL("/assets/raven/raven/sw.js")
      .then((url: string) => {
        navigator.serviceWorker
          .register(url, {
            type: "classic",
          })
          .then((registration) => {
            // @ts-ignore
            window.frappePushNotification.initialize(registration).then(() => {
              console.info("Frappe Push Notification initialized")
            })
          })
      })
      .catch((err: any) => {
        console.error("Failed to register service worker", err)
      })
  } else {
    console.error("Service worker not enabled/supported by browser")
  }
}

if (import.meta.env.DEV) {
  fetch('/api/method/raven.www.raven.get_context_for_dev', {
    method: 'POST',
  })
    .then(response => response.json())
    .then((values) => {
      const v = JSON.parse(values.message)
      //@ts-ignore
      if (!window.frappe) window.frappe = {};
      //@ts-ignore
      window.frappe.boot = v
      //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): the dev server must mirror what
      //// raven.html does in production, or the embedded chrome renders untranslated in dev only.
      //@ts-ignore - mirror the assignment done by raven.html in production:
      // the embedded i18n shim reads frappe._messages (bracket notation).
      window.frappe._messages = window.frappe.boot['__messages']
      safeSyncDocs()
      registerServiceWorker()
      ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
        <React.StrictMode>
          <App />
        </React.StrictMode>,
      )
    }
    )
} else {
  //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): guarded sync on the production path.
  safeSyncDocs()
  registerServiceWorker()
  ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  )
}
