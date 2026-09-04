import { defineConfig, devices } from '@playwright/test';

/**
 * Browser regression suite for the explorer's static, prerendered build.
 *
 * This intentionally runs against `vite preview` serving the real
 * `adapter-static` output (see `test:e2e` in package.json, which builds
 * first), not the dev server — the bug this guards against (a visually-hidden
 * fallback table inflating `document.documentElement.scrollHeight` on mobile
 * viewports) only reproduces against the actual static HTML/CSS the app
 * ships, not a live-reloading dev bundle.
 */
export default defineConfig({
	testDir: './e2e',
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 1 : 0,
	reporter: [['list']],
	use: {
		baseURL: 'http://localhost:4173',
		trace: 'retain-on-failure'
	},
	projects: [
		{
			name: 'mobile-chromium',
			use: { ...devices['Pixel 7'] }
		}
	],
	webServer: {
		// Note: no extra `--` before the vite flags — pnpm already forwards
		// everything after its own `--` to the underlying `vite preview`
		// command, so a second `--` would be passed through literally and
		// vite would ignore the flags that follow it.
		command: 'pnpm run preview --port 4173 --strictPort',
		url: 'http://localhost:4173',
		reuseExistingServer: !process.env.CI,
		timeout: 60_000
	}
});
