import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	// Svelte's package exports pick the client runtime via the "browser"
	// resolution condition; without it, Vitest (which runs in Node) resolves
	// svelte's server-only runtime and `mount()` throws
	// "lifecycle_function_unavailable" for every component test.
	resolve: process.env.VITEST ? { conditions: ['browser'] } : undefined,
	test: {
		environment: 'jsdom',
		include: ['src/**/*.{test,spec}.{js,ts}'],
		setupFiles: ['./src/vitest-setup.ts']
	}
});
