import { scan } from "react-scan";
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ThemeProvider } from "./components/theme-provider"

scan({
  enabled: true,
});


import { initPushNotifications, isStandalone } from "@lib/push";

//// Neoffice - the NeoCockpit menu translates through Frappe's global __(), which the desk defines
//// and this app does not: its labels stayed English in Synk v3 (« Collapse menu », 30.09.2026).
//// A thin __ over frappe._messages, read at each call, with Frappe's {0} placeholders.
type FrappeTranslate = (text: string, args?: (string | number)[]) => string
const frappeWindow = window as unknown as { __?: FrappeTranslate; frappe?: { _messages?: Record<string, string> } }
if (typeof frappeWindow.__ !== "function") {
  frappeWindow.__ = (text, args) => {
    let translated = frappeWindow.frappe?._messages?.[text] || text
    if (args) translated = translated.replace(/\{(\d+)\}/g, (_match, index) => String(args[Number(index)] ?? ""))
    return translated
  }
}

if (import.meta.env.DEV) {
  fetch('/api/method/raven.www.raven.get_context_for_dev', {
    method: 'POST',
  })
    .then(response => response.json())
    .then((values) => {
      const v = JSON.parse(values.message)
      if (!window.frappe) window.frappe = {};
      window.frappe.boot = v
      window.frappe._messages = window.frappe.boot["__messages"];
      // After boot lands — push config (firebase_client_config) comes from it
      initPushNotifications()
      createRoot(document.getElementById('root')!).render(
        <StrictMode>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </StrictMode>,
      )
    }
    )
} else {
  // Boot is inlined by the Jinja entry template. An OFFLINE (app-shell) load
  // serves the BUILT index.html from the service worker's cache instead — its
  // Jinja is unrendered, so the whole inline boot script fails to parse and
  // window.frappe never gets set. Recover the last ONLINE load's boot from
  // localStorage so the shell still knows who you are, your settings, etc.
  if (!window.frappe?.boot) {
    try {
      const cached = localStorage.getItem("raven-boot-cache")
      if (cached) {
        if (!window.frappe) window.frappe = {}
        window.frappe.boot = JSON.parse(cached)
        window.frappe._messages = window.frappe.boot["__messages"]
      }
    } catch {
      // No usable cached boot — the shell still renders; boot readers degrade.
    }
  } else if (isStandalone()) {
    // Fresh server boot — cache it for offline launches, off the critical path.
    // Installed app only: browser-tab sessions shouldn't leave boot at rest on
    // a possibly-shared machine (and don't get the offline shell anyway).
    window.setTimeout(() => {
      try {
        localStorage.setItem("raven-boot-cache", JSON.stringify(window.frappe.boot))
      } catch {
        // Quota/private mode — offline loads just won't have boot.
      }
    }, 3000)
  }
  initPushNotifications()
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </StrictMode>,
  )
}
