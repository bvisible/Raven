from . import __version__ as app_version

app_name = "raven"
# //// Neoffice - the app is shown as "Business messaging" (« Messagerie d'entreprise »), the name the cockpit's menu
# //// gives it (Jérémy, 21.10 and 27.10). It was published as Synk from 1d6dea095 (2026-01-03) to 2026-10-27.
app_title = "Business messaging"
app_publisher = "Frappe"
app_description = "Messaging Application"
app_email = "support@frappe.io"
app_license = "AGPLv3"
source_link = "https://github.com/frappe/Raven"
# //// Neoffice - the brand's hand-drawn chat bubble, the icon the cockpit shows for this app, instead of the Raven
# //// mark. neoffice_theme serves it (Streamline's licence keeps the drawing out of this public repository).
app_logo = "/assets/neoffice_theme/icons/streamline/chat-bubble-text.svg"
app_logo_url = "/assets/neoffice_theme/icons/streamline/chat-bubble-text.svg"

# Frappe Shell Native pattern — neoffice_theme provides the Lucide sprite,
# the neoffice-theme.css used by FrappeSidebar/FrappeNavbar, and the
# `App Customization` doctype for app-switcher grouping.
# //// Neoffice — org/repo form on purpose (upstream has no such dependency).
# //// frappe/installer.py runs parse_app_name() on every required_apps entry
# //// BEFORE the "already installed" check; a bare name is looked up under the
# //// frappe/ and erpnext/ GitHub orgs -> 404 for a private app ->
# //// InvalidRemoteException aborts every install-app. "org/repo" is split
# //// locally into the package name, no network involved.
required_apps = ["bvisible/neoffice_theme"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# //// Neoffice - the desk chat widget (raven/public/js/raven_chat, anchored to the cockpit's messaging icon) is ours:
# //// upstream removed it with its stylesheet (#2311, 2026-10-16), the widget needs the stylesheet back.
app_include_css = "raven.bundle.css"
app_include_js = "raven.bundle.js"
# //// Neoffice - no app_include_icons: upstream loads raven/public/icons/raven.svg (the Raven mark) into the desk
# //// sprite as "/assets/raven/icons/raven.svg", and frappe v15's app.html fetches `/assets/{{ path }}`, so the desk
# //// asked for /assets//assets/… and got a 404 on every page (maintenance#1884). The Raven mark is not ours either:
# //// the timeline button draws the brand's chat bubble (timeline_button.js). Restore the include, as
# //// "raven/icons/raven.svg", only if a desk icon of Raven's own is wanted again.

add_to_apps_screen = [
	{
		"name": "raven",
		# //// Neoffice - apps-screen tile: the brand's chat bubble and the cockpit's name for the app (see app_title).
		"logo": "/assets/neoffice_theme/icons/streamline/chat-bubble-text.svg",
		"title": "Business messaging",
		# //// Neoffice - same wording as the tile.
		"setup_wizard_text": "Welcome to your business messaging. Let's set up your team's space.",
		"route": "/raven",
		"has_permission": "raven.permissions.check_app_permission",
	}
]


sounds = [
	{
		"name": "raven_notification",
		"src": "/assets/raven/sounds/raven_notification.mp3",
		"volume": 0.2,
	},
]

extend_bootinfo = "raven.boot.boot_session"
# include js, css files in header of web template
# web_include_css = "/assets/raven/css/raven.css"
# web_include_js = "/assets/raven/js/raven.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "raven/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# "methods": "raven.utils.jinja_methods",
# "filters": "raven.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "raven.install.before_install"
# On Frappe Cloud, set push up on install and at setup, so it works from the first message.
after_install = ["raven.install.after_install", "raven.frappe_cloud_push.queue_initial_push_setup"]
setup_wizard_success = "raven.frappe_cloud_push.queue_initial_push_setup"
# after_sync = ""

# Uninstallation
# ------------

# before_uninstall = "raven.uninstall.before_uninstall"
after_uninstall = "raven.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "raven.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"*": {
		"after_insert": "raven.raven_integrations.doctype.raven_document_notification.raven_document_notification.run_document_notification",
		"on_update": "raven.raven_integrations.doctype.raven_document_notification.raven_document_notification.run_document_notification",
		"on_trash": "raven.raven_integrations.doctype.raven_document_notification.raven_document_notification.run_document_notification",
		"on_cancel": "raven.raven_integrations.doctype.raven_document_notification.raven_document_notification.run_document_notification",
		"on_submit": "raven.raven_integrations.doctype.raven_document_notification.raven_document_notification.run_document_notification",
	},
	"User": {
		"after_insert": "raven.raven.doctype.raven_user.raven_user.add_user_to_raven",
		"on_update": "raven.raven.doctype.raven_user.raven_user.add_user_to_raven",
		"on_trash": "raven.raven.doctype.raven_user.raven_user.remove_user_from_raven",
	},
	"Department": {
		"after_insert": "raven.raven_integrations.controllers.department.after_insert",
		"on_update": "raven.raven_integrations.controllers.department.on_update",
		"on_trash": "raven.raven_integrations.controllers.department.on_trash",
	},
	"Employee": {
		"after_insert": "raven.raven_integrations.controllers.employee.after_insert",
		"on_update": "raven.raven_integrations.controllers.employee.on_update",
		"on_trash": "raven.raven_integrations.controllers.employee.on_trash",
	},
	# //// Neoffice — a person who gets the messaging joins the workspaces anyone may join, so that their channels
	# //// show (Jérémy, 13.10.2026, maintenance#1553); see raven/open_workspaces.py.
	"Raven User": {
		"after_insert": "raven.open_workspaces.join_open_workspaces_on_insert",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"raven.scheduler.all"
	# ],
	# "daily": [
	# 	"raven.scheduler.daily"
	# ],
	# "hourly": [
	# 	"raven.scheduler.hourly"
	# ],
	# "weekly": [
	# 	"raven.scheduler.weekly"
	# ],
	# "monthly": [
	# 	"raven.scheduler.monthly"
	# ],
	"daily_maintenance": [
		"raven.scheduler.daily.sync_invalid_tokens",
		"raven.raven_cloud_notifications.sync_users_tokens_to_raven_cloud",
	],
	"cron": {
		# run every 5 minutes. Reminder and scheduled message times are aligned to this
		# grid in their validate methods, so both fire on time.
		"*/5 * * * *": [
			"raven.scheduler.close_expired_polls.close_expired_polls",
			"raven.scheduler.send_reminders.send_due_reminders",
			"raven.scheduler.send_scheduled_messages.send_due_messages",
		],
	},
}

# Auto-registered in Log Settings; each doctype's clear_old_logs does the deletion.
default_log_clearing_doctypes = {
	"Raven Reminder": 30,
	"Raven Scheduled Message": 30,
}

# Testing
# -------

# before_tests = "raven.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# "frappe.desk.doctype.event.event.get_events": "raven.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# "Task": "raven.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = ["Raven Message", "Raven Reminder", "Raven Scheduled Message"]


# User Data Protection
# --------------------

# user_data_fields = [
# {
# "doctype": "{doctype_1}",
# "filter_by": "{filter_by}",
# "redact_fields": ["{field_1}", "{field_2}"],
# "partial": 1,
# },
# {
# "doctype": "{doctype_2}",
# "filter_by": "{filter_by}",
# "partial": 1,
# },
# {
# "doctype": "{doctype_3}",
# "strict": False,
# },
# {
# "doctype": "{doctype_4}"
# }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# "raven.auth.validate"
# ]

additional_timeline_content = {"*": ["raven.api.raven_message.get_timeline_message_content"]}

website_route_rules = [
	{"from_route": "/raven/<path:app_path>", "to_route": "raven"},
]

# Serves the v3 service worker at /raven/sw.js (in-scope for page control —
# offline app shell + share target). See raven/page_renderers.py for why.
page_renderer = ["raven.page_renderers.RavenV3ServiceWorker"]

permission_query_conditions = {
	# //// Neoffice — the user directory had no entry here at all, so a LIST of
	# //// it came back whole to anyone holding the role. See raven.permissions.
	"Raven User": "raven.permissions.raven_user_query",
	"Raven Channel": "raven.permissions.raven_channel_query",
	"Raven Message": "raven.permissions.raven_message_query",
	"Raven Poll": "raven.permissions.raven_poll_query",
	"Raven Poll Vote": "raven.permissions.raven_poll_vote_query",
	"Raven Workspace": "raven.permissions.raven_workspace_query",
	"Raven Workspace Member": "raven.permissions.raven_workspace_member_query",
	"Raven Channel Member": "raven.permissions.raven_channel_member_query",
}

has_permission = {
	"Raven Channel": "raven.permissions.channel_has_permission",
	"Raven Channel Member": "raven.permissions.channel_member_has_permission",
	"Raven Message": "raven.permissions.message_has_permission",
	"Raven Poll Vote": "raven.permissions.raven_poll_vote_has_permission",
	"Raven Poll": "raven.permissions.raven_poll_has_permission",
	"Raven User": "raven.permissions.raven_user_has_permission",
	"Raven Workspace Member": "raven.permissions.workspace_member_has_permission",
	"Raven Workspace": "raven.permissions.workspace_has_permission",
}

on_session_creation = "raven.api.user_availability.set_user_active"

# The bundled native app runs from its own origins; allow them on API calls without site config.
before_request = ["raven.api.native.set_cors"]
# Frappe 15 ignores the origin set_cors chooses, so Raven writes the CORS headers there itself.
after_request = ["raven.api.native.add_cors_headers"]
on_logout = "raven.api.user_availability.set_user_inactive"

export_python_type_annotations = True
require_type_annotated_api_methods = True

raven_document_link_override = "raven.api.document_link.get_new_app_document_links"

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
ignore_translatable_strings_from = ["frappe"]

sqlite_search = ["raven.api.search.RavenSearch"]
