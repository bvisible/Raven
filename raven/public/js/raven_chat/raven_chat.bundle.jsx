import * as React from "react";
import { App } from "./App";
import { createRoot } from "react-dom/client";


class RavenChat {
	//// Neoffice - docked mode (4b543c6b9 + e58d43ae8, 2026-06-11 "feat(cockpit): docked chat widget"): the desk passes docked=true when the
	//// NeoCockpit rail is present, so the widget renders anchored rather than floating.
	constructor({ wrapper, docked = false }) {
		this.$wrapper = $(wrapper);
		//// Neoffice - docked mode (4b543c6b9 + e58d43ae8, 2026-06-11 "feat(cockpit): docked chat widget").
		this.docked = docked;

		this.init();
	}

	init() {
		this.setup_app();
	}

	setup_app() {
		// create and mount the react app
		const root = createRoot(this.$wrapper.get(0));
		//// Neoffice - docked mode (4b543c6b9 + e58d43ae8, 2026-06-11 "feat(cockpit): docked chat widget"): flag handed to the React tree.
		root.render(<App docked={this.docked} />);
		this.$raven_chat = root;
	}
}

frappe.provide("frappe.ui");
frappe.ui.RavenChat = RavenChat;
export default RavenChat;