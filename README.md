<div align="center" markdown="1">

<a href="https://frappe.io/raven">
    <img src="raven/public/raven_logo.svg" height="80" alt="Raven logo">
</a>

<h1>Raven</h1>

**A simple chat app for teams**

[![GitHub release](https://img.shields.io/github/v/release/frappe/raven)](https://github.com/frappe/raven/releases)
[![CI](https://github.com/frappe/raven/actions/workflows/ci.yml/badge.svg)](https://github.com/frappe/raven/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPLv3-blue)](LICENSE)

[Website](https://frappe.io/raven) - [Discussions](https://github.com/frappe/raven/discussions) - [Issues](https://github.com/frappe/raven/issues)

</div>

## Raven

Raven is open-source chat for teams. Channels, direct messages, threads, files and reactions, with nothing surprising in between. It runs on your own Frappe site, so your conversations stay in your database and there is no per-user pricing.

Raven is built on the [Frappe Framework](https://frappe.io/framework) and works alongside ERPNext, HR, CRM and Helpdesk.

### Key features

- **Channels and direct messages:** Open, private and public channels, plus one-to-one messages. Group channels into workspaces.
- **Threads and replies:** Reply inline, or start a thread when a discussion needs its own space.
- **Rich messages:** Formatting, mentions, links, code blocks, emoji and custom reactions.
- **Files and previews:** Drag in images and documents. Links and shared documents show a preview card.
- **Search:** Find messages, files and people across every channel you belong to.
- **Notifications:** Web push, quiet hours and per-channel preferences. Reminders and scheduled messages.
- **Mobile:** Works in the browser and as an installable web app on phones.

### Works with your Frappe apps

- **Share a document:** Paste a link to any document on the site and Raven shows it with its status and key fields.
- **Document notifications:** Post to a channel when a document is created, changed or submitted. Conditions and templates are configurable without code.
- **Workflows from the chat:** Approve, reject or send back a document without leaving the conversation.
- **Know who is on leave:** Frappe HR leave shows up next to a person's name.
- **Bots, webhooks and AI agents:** Build bots that post and reply, send incoming webhooks into channels, and set up agents backed by your own OpenAI or compatible provider.

### Under the hood

- [Frappe Framework](https://github.com/frappe/frappe): A full-stack web application framework.
- [Frappe React SDK](https://github.com/frappe/frappe-react-sdk): React hooks for auth, data fetching and realtime with a Frappe backend.

### Compatibility

| Raven branch | Frappe branch |
| :----------- | :------------ |
| develop      | version-15 (15.111 or later), version-16, develop |

## Getting started

### Frappe Cloud

Install Raven on a site from the Frappe Cloud marketplace. Frappe Cloud takes care of hosting, upgrades, backups and support.

<div>
	<a href="https://cloud.frappe.io/marketplace/apps/raven" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/try-on-fc-white.png">
			<img src="https://frappe.io/files/try-on-fc-black.png" alt="Try on Frappe Cloud" height="28" />
		</picture>
	</a>
</div>

### Self hosting

[Pilot](https://github.com/frappe/pilot) is the recommended way to run Raven on your own server. It installs Frappe, manages sites and backups, and sets up production with nginx and TLS. Pilot needs Frappe v16 or later.

Install Pilot:

```bash
curl -fsSL https://raw.githubusercontent.com/frappe/pilot/develop/install.sh | bash
```

Create a bench and run the setup wizard. The first `start` prints the URL of the admin wizard.

```bash
pilot new main
pilot -b main start
```

Then add Raven and create a site:

```bash
pilot -b main get-app https://github.com/frappe/raven
pilot -b main new-site chat.example.com
pilot -b main install-app chat.example.com raven
```

Raven opens at `https://chat.example.com/raven`. See the Pilot [production guide](https://github.com/frappe/pilot/blob/develop/docs/production.md) for nginx, TLS and process managers.

If you already have a bench, install Raven the usual way:

```bash
bench get-app https://github.com/frappe/raven
bench --site your-site install-app raven
```

## Development

Set up a bench with Pilot or [bench](https://docs.frappe.io/framework/user/en/installation), get the app and create a site as above, then turn on developer mode and skip CSRF checks for the site. The second setting is for local development only, since the Vite dev server has no CSRF token.

```bash
bench set-config -g developer_mode 1
bench --site raven.localhost set-config ignore_csrf 1
```

### Web app

The web app is a React single page app in `apps/web`. To work on it with hot reloading, add a `.env.local` file in `apps/web`:

```
VITE_SITE_NAME='raven.localhost'
VITE_SOCKET_PORT=9000
```

`VITE_SOCKET_PORT` is the socket.io port of your bench, usually the web port plus 1000. Then start the dev server from the app folder:

```bash
cd apps/raven
yarn
yarn dev
```

The app runs at `http://raven.localhost:8080` and proxies API calls to your site. Run `yarn` from the repository root only, not from `apps/web`.

## Community

- [GitHub Discussions](https://github.com/frappe/raven/discussions): Questions, ideas and help.
- [GitHub Issues](https://github.com/frappe/raven/issues): Bug reports. Include steps to reproduce, screenshots and any console or server errors.
- [Report security vulnerabilities](https://frappe.io/security)
- [Translations](https://crowdin.com/project/frappe)

## License

[AGPLv3](LICENSE)

<br>
<br>
<div align="center" style="padding-top: 1rem; padding-bottom: 1rem; display: flex; justify-content:center;">
	<a href="https://frappe.io" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/Frappe-white.png">
			<img src="https://frappe.io/files/Frappe-black.png" alt="Frappe Technologies" height="28"/>
		</picture>
	</a>
</div>
