// "Send a Raven" button on every form timeline the user can read.

frappe.provide("frappe.raven");

/**
 * The first icon name the page's sprite actually has. Raven's own icons
 * come from hooks.py, lucide names from Frappe v16, and the last candidates
 * cover Frappe v15, whose sprite uses different names.
 */
frappe.raven.icon_name = (...candidates) =>
  candidates.find((name) => name && document.getElementById(`icon-${name}`));

/** The icon markup for the first available name, or nothing at all. */
frappe.raven.icon = (name, fallback, size = "sm") => {
  const known = frappe.raven.icon_name(name, fallback);
  return known ? frappe.utils.icon(known, size) : "";
};

$(document).on("app_ready", function () {
  $.each(frappe.boot.user.can_read, function (i, doctype) {
    frappe.ui.form.on(doctype, {
      refresh(frm) {
        const timeline = frm.footer?.frm?.timeline;
        if (frm.is_new() || !timeline) return;
        if (timeline.timeline_actions_wrapper.find(".send-raven-button").length) return;
        add_send_button(timeline, frm);
      },
    });
  });
});

// //// Neoffice - the brand's hand-drawn chat bubble, the icon the cockpit shows for this app (served by
// //// neoffice_theme: Streamline's licence keeps the drawing out of this public repository).
const BRAND_ICON = "/assets/neoffice_theme/icons/streamline/chat-bubble-text.svg";

/**
 * //// Neoffice - the button carries the brand's drawing, not the Raven mark: the timeline helper only draws
 * //// sprite icons, so the button takes a line icon (or none) and the drawing replaces it, at 16px like the
 * //// upstream mark. The desk's dark theme inverts every Streamline image (neoffice-theme.css).
 */
const add_send_button = (timeline, frm) => {
  // //// Neoffice - the app is « Messagerie d'entreprise » for our users (hooks.py app_title); upstream: "Send a Raven".
  const label = __("Send to the business messaging");
  const open = () => open_send_dialog(frm);
  const classes = "btn-secondary send-raven-button";
  // //// Neoffice - a line icon first (the helper draws sprite icons only), then the brand's drawing in its place.
  const button = timeline.add_action_button(label, open, frappe.raven.icon_name("send", "share"), classes);
  const icon = `<img class="icon icon-sm send-raven-icon" src="${BRAND_ICON}" alt="">`;
  const svg = button.find("svg.icon");
  if (svg.length) svg.replaceWith(icon);
  else button.prepend(icon);
};

const open_send_dialog = (frm) => {
  frappe
    .xcall("raven.api.raven_channel.get_channels", { hide_archived: true })
    .then((channels) => {
      if (!channels?.length) {
        // //// Neoffice - the app is « Messagerie d'entreprise » for our users (hooks.py app_title); upstream: "Send a Raven".
        frappe.msgprint({ title: __("Send to the business messaging"), indicator: "blue", message: __("No channels found") });
        return;
      }
      show_send_dialog(frm, channels);
    });
};

/** One list for channels and DMs. The description tells them apart. */
const channel_options = (channels) =>
  channels.map((channel) => ({
    value: channel.name,
    label: channel.is_direct_message ? channel.full_name || channel.peer_user_id : channel.channel_name,
    description: channel.is_direct_message ? __("Direct Message") : channel.workspace,
  }));

const show_send_dialog = (frm, channels) => {
  const dialog = new frappe.ui.Dialog({
    // //// Neoffice - the app is « Messagerie d'entreprise » for our users (hooks.py app_title); upstream: "Send a Raven".
    title: __("Send to the business messaging"),
    fields: [
      {
        fieldname: "channel",
        label: __("Channel or Person"),
        fieldtype: "Autocomplete",
        options: channel_options(channels),
        reqd: 1,
      },
      { fieldname: "message", label: __("Message"), fieldtype: "Long Text" },
      { fieldtype: "Section Break" },
      { fieldname: "select_attachments", label: __("Select Attachments"), fieldtype: "HTML" },
    ],
    primary_action_label: __("Send"),
    primary_action(values) {
      send_message(frm, values.channel, values.message, selected_attachment(dialog));
      dialog.hide();
    },
    secondary_action_label: __("Discard"),
    secondary_action: () => dialog.hide(),
    minimizable: true,
  });
  setup_attachments(frm, dialog);
  dialog.show();
};

const setup_attachments = (frm, dialog) => {
  const wrapper = $(dialog.fields_dict.select_attachments.wrapper).empty();
  $(`
    <label class="control-label">${__("Select Attachments")}</label>
    <div class="attach-list"></div>
    <p class="add-more-attachments">
      <button class="btn btn-xs btn-default">
        ${frappe.raven.icon("plus", "small-add", "xs")}&nbsp;${__("Add Attachment")}
      </button>
    </p>
  `).appendTo(wrapper);

  const uploader_args = {
    doctype: frm.doctype,
    docname: frm.docname,
    folder: "Home/Attachments",
    on_success: (attachment) => {
      frm.attachments.attachment_uploaded(attachment);
      render_attachment_rows(frm, wrapper);
    },
  };
  wrapper.find(".add-more-attachments button").on("click", () => new frappe.ui.FileUploader(uploader_args));
  render_attachment_rows(frm, wrapper);
};

const render_attachment_rows = (frm, wrapper) => {
  const rows = wrapper.find(".attach-list").empty();
  frm.get_files().forEach((file) => {
    if (!file.file_name) return;
    rows.append(`
      <p class="flex">
        <label class="attachment-radio">
          <input type="radio" name="raven-attachment" data-file-url="${frappe.utils.escape_html(file.file_url)}">
          <span class="ellipsis">${frappe.utils.escape_html(file.file_name)}</span>
        </label>
        &nbsp;
        <a href="${frappe.urllib.get_full_url(file.file_url)}" target="_blank">
          ${frappe.raven.icon("link", "link-url", "xs")}
        </a>
      </p>
    `);
  });
};

// The form already has each attachment's URL, so no File lookup is needed (and it needs File permission).
const selected_attachment = (dialog) =>
  $(dialog.wrapper).find("[data-file-url]:checked").attr("data-file-url") || "";

const IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif"];

const message_type_for = (file_url) => {
  if (!file_url) return "Text";
  return IMAGE_EXTENSIONS.includes(file_url.split(".").pop().toLowerCase()) ? "Image" : "File";
};

const send_message = (frm, channel, message, file_url) => {
  frappe.db
    .insert({
      doctype: "Raven Message",
      channel_id: channel,
      text: message,
      json: {
        type: "doc",
        content: [{ type: "paragraph", content: [{ type: "text", text: message }] }],
      },
      message_type: message_type_for(file_url),
      file: file_url,
      link_doctype: frm.doctype,
      link_document: frm.docname,
    })
    .then(() => {
      frm.reload_doc();
      frappe.show_alert({ message: __("Message sent"), indicator: "green" });
      frappe.utils.play_sound("email");
    })
    .catch(() => frappe.throw(__("Error sending message")));
};
