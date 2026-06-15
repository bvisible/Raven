$(document).on('app_ready', function () {
    if (frappe.boot.show_raven_chat_on_desk && frappe.user.has_role("Raven User")) {

        try {
            // If on mobile or on frappe v16, do not show the chat
            if (frappe.is_mobile() || frappe.boot.versions["frappe"].startsWith('16')) {
                return;
            }

            // //// NEOFFICE — NeoCockpit chrome: no floating launcher bar.
            // The same widget mounts DOCKED (hidden until toggled) and the
            // cockpit rail's synk icon opens it as a popup next to the menu.
            // Decide from the SERVER boot flag (the exact criterion desk.js
            // make_chrome uses), NOT document.body.classList: the cockpit class
            // is added by make_cockpit() which can land AFTER the app_ready that
            // fires this handler, so the DOM check is racy and intermittently
            // mounts the legacy floating bar even under the cockpit (observed on
            // demo 2026-06-15). The boot flag is available as soon as bootinfo
            // is loaded, well before any DOM timing.
            if (!frappe.boot.neoffice_cockpit_disable && frappe.boot.home_page !== "setup-wizard") {
                let docked_element = $(document.createElement('div'));
                docked_element.addClass('raven-chat raven-chat-docked');
                $('body').append(docked_element);

                frappe.require("raven_chat.bundle.jsx").then(() => {
                    frappe.raven_chat = new frappe.ui.RavenChat({
                        wrapper: docked_element,
                        docked: true,
                    });
                });
                return;
            }

            let main_section = $(document).find('.main-section');

            // Add bottom padding to the main section
            main_section.css('padding-bottom', '60px');

            let chat_element = $(document.createElement('div'));
            chat_element.addClass('raven-chat');

            main_section.append(chat_element);

            frappe.require("raven_chat.bundle.jsx").then(() => {
                frappe.raven_chat = new frappe.ui.RavenChat({
                    wrapper: chat_element,
                });
            });
        } catch (error) {
            console.error(error);
        }
    }

});
import './templates/send_message.html';
import './timeline_button';
