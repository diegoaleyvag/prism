<script lang="ts">
	import '$lib/styles/global.css';
	import SimBanner from '$lib/components/SimBanner.svelte';
	import ModeBadge from '$lib/components/ModeBadge.svelte';
	import { indexArtifact } from '$lib/data';
	import { base } from '$app/paths';

	let { children } = $props();
</script>

<SimBanner />

<div class="app-shell">
	<header class="app-header">
		<a class="app-header__brand" href="{base}/">Prism <span class="app-header__tag">explorer</span></a>
		<div class="app-header__modes" aria-label="Evaluation modes available in this build">
			<ModeBadge mode="fixture" active={true} />
			<ModeBadge mode="replay" active={false} />
			<ModeBadge mode="live" active={false} />
		</div>
	</header>

	<main class="app-main">
		{@render children()}
	</main>

	<footer class="app-footer">
		<p class="app-footer__disclaimer">{indexArtifact.disclaimer}</p>
		<p class="app-footer__meta">
			manifest <code>{indexArtifact.run.manifest_id}</code> · prism {indexArtifact.run.prism_version} ·
			review scope <code>{indexArtifact.run.review_scope}</code> · record set
			<code>{indexArtifact.run.record_set_hash.slice(0, 19)}…</code>
		</p>
	</footer>
</div>

<style>
	.app-shell {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	.app-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-4);
		padding: var(--space-3) var(--space-5);
		border-bottom: 1px solid var(--color-border);
		flex-wrap: wrap;
	}

	.app-header__brand {
		font-weight: 700;
		font-size: 1.1rem;
		text-decoration: none;
		color: var(--color-fg);
	}

	.app-header__tag {
		font-weight: 400;
		color: var(--color-fg-muted);
	}

	.app-header__modes {
		display: flex;
		gap: var(--space-2);
		flex-wrap: wrap;
	}

	.app-main {
		flex: 1;
		padding: var(--space-5);
		max-width: 1100px;
		width: 100%;
		margin: 0 auto;
	}

	.app-footer {
		padding: var(--space-4) var(--space-5);
		border-top: 1px solid var(--color-border);
		font-size: 0.78rem;
		color: var(--color-fg-muted);
	}

	.app-footer__disclaimer {
		margin: 0 0 var(--space-1);
	}

	.app-footer__meta {
		margin: 0;
		font-family: var(--font-mono);
	}
</style>
