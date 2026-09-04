//// Neoffice - import order only (an IDE "organize imports" pass ran on this file).
//// No import added or removed, no behaviour change.
import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig, loadEnv } from "vite";
//// Neoffice - import order only (an IDE "organize imports" pass), no behaviour change.
import { VitePWA } from "vite-plugin-pwa";
import svgr from "vite-plugin-svgr";
//// Neoffice - import order only (an IDE "organize imports" pass), no behaviour change.
import proxyOptions from "./proxyOptions";

/// <reference types="vite-plugin-svgr/client" />
// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
	const env = loadEnv(mode, process.cwd(), "")
	return {
		plugins: [react(), svgr(), VitePWA({
			registerType: "autoUpdate",
			strategies: "injectManifest",
			injectRegister: null,
			outDir: "../raven/public/raven",
			manifest: {
				//// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk" / 49ee6e172, 2025-04-05): PWA manifest name.
				name: "Synk",
				start_url: `/${env.VITE_BASE_NAME}`,
				scope: `/${env.VITE_BASE_NAME}/`,
				//// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk" / 49ee6e172, 2025-04-05): PWA manifest short name.
				short_name: "Synk",
				description: "Simple, work messaging tool.",
				display: "standalone",
				"icons": [
					{
						"src": "/assets/raven/manifest/android-chrome-192x192.png",
						"sizes": "192x192",
						"type": "image/png"
					},
					{
						"src": "/assets/raven/manifest/android-chrome-512x512.png",
						"sizes": "512x512",
						"type": "image/png"
					},
					{
						"src": "/assets/raven/manifest/apple-touch-icon.png",
						"sizes": "180x180",
						"type": "image/png"
					},
					{
						"src": "/assets/raven/manifest/favicon-16x16.png",
						"sizes": "16x16",
						"type": "image/png"
					},
					{
						"src": "/assets/raven/manifest/favicon-32x32.png",
						"sizes": "32x32",
						"type": "image/png"
					},
					{
						"src": "/assets/raven/manifest/favicon.ico",
						"sizes": "64x64 32x32 24x24 16x16",
						"type": "image/x-icon"
					}
				],
			}
		})],
		server: {
			port: 8080,
			proxy: proxyOptions
		},
		resolve: {
			alias: {
				"@": path.resolve(__dirname, "./src")
			}
		},
		build: {
			outDir: "../raven/public/raven",
			emptyOutDir: true,
			//// Neoffice - commit-the-build (3ff52c65d, 2025-12-22 "fix(build): Add external config for
			//// standalone builds"): source maps off and only 2 parallel file ops, because the build runs on
			//// GitHub Actions for instances that cannot afford it - a 4 GB instance OOM-kills on `yarn build`.
			target: 'es2015',
			sourcemap: false,
			rollupOptions: {
				//// Neoffice - commit-the-build (3ff52c65d, 2025-12-22): the SPA is also built OUTSIDE a bench
				//// (GitHub Actions checkout has no ../../../frappe/ and no common_site_config.json), so those
				//// two imports are marked external instead of failing the build.
				maxParallelFileOps: 2,
			// Ignore Frappe bench-specific imports that don't exist in standalone builds
			external: [
				/common_site_config\.json/,
				/\.\.\/\.\.\/\.\.\/frappe\//,
			],
				onwarn(warning, warn) {
					if (warning.code === "MODULE_LEVEL_DIRECTIVE") {
						return
					}
					warn(warning)
				}
			}
		}
	};
});
