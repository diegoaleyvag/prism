<script lang="ts">
	import '$lib/styles/global.css';
	import SimBanner from '$lib/components/SimBanner.svelte';
	import ModeBadge from '$lib/components/ModeBadge.svelte';
	import { indexArtifact } from '$lib/data';
	import { base } from '$app/paths';

	let { children } = $props();
</script>

<SimBanner />

<a class="skip-link" href="#main-content">Skip to results</a>

<div class="app-shell fd-shell">
	<header class="app-header">
		<a class="app-header__brand fd-shell__identity" href="{base}/">Prism <span class="app-header__tag">evaluation register</span></a>
		<div class="app-header__modes" aria-label="Evaluation modes available in this build">
			<ModeBadge mode="fixture" active={true} />
			<ModeBadge mode="replay" active={false} />
			<ModeBadge mode="live" active={false} />
		</div>
	</header>

	<main id="main-content" class="app-main">
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
		padding: var(--space-4) var(--space-5);
		border-bottom: var(--fd-rule-width) solid var(--color-fg);
		flex-wrap: wrap;
	}

	.app-header__brand {
		font-size: clamp(2rem, 4vw, 3rem);
		line-height: 0.8;
		letter-spacing: 0.02em;
		text-transform: uppercase;
		text-decoration: none;
		color: var(--color-fg);
	}

	.app-header__tag {
		font-family: var(--font-mono);
		font-size: 0.3em;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-fg-muted);
	}

	.app-header__modes {
		display: flex;
		gap: var(--space-2);
		flex-wrap: wrap;
	}

	.app-main {
		flex: 1;
		padding: var(--space-6) var(--space-5) var(--space-8);
		max-width: 1240px;
		width: 100%;
		margin: 0 auto;
	}

	.app-footer {
		padding: var(--space-4) var(--space-5);
		border-top: var(--fd-rule-width) solid var(--color-fg);
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

	.skip-link {
		position: fixed;
		z-index: 101;
		left: var(--space-3);
		top: var(--space-3);
		padding: var(--space-2) var(--space-3);
		background: var(--fd-field-raised);
		color: var(--color-fg);
		border: 2px solid var(--color-fg);
		transform: translateY(-180%);
	}

	.skip-link:focus {
		transform: translateY(0);
	}
</style>
