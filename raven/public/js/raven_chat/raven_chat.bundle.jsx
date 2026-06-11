import * as React from "react";
import { App } from "./App";
import { createRoot } from "react-dom/client";


class RavenChat {
	constructor({ wrapper, docked = false }) {
		this.$wrapper = $(wrapper);
		this.docked = docked;

		this.init();
	}

	init() {
		this.setup_app();
	}

	setup_app() {
		// create and mount the react app
		const root = createRoot(this.$wrapper.get(0));
		root.render(<App docked={this.docked} />);
		this.$raven_chat = root;
	}
}

frappe.provide("frappe.ui");
frappe.ui.RavenChat = RavenChat;
export default RavenChat;