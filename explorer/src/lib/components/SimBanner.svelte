<script lang="ts">
	// Sticky, non-dismissible disclaimer. Renders in the root layout so every
	// prerendered page carries it — there is no close/dismiss control by design.
</script>

<div class="sim-banner" role="note">
	<span class="sim-banner__icon" aria-hidden="true">&#9888;</span>
	<p class="sim-banner__text">
		<strong>SIMULATED</strong> — deterministic fixtures, not named-model performance. All costs,
		latencies, and outcomes in this workbench come from a reproducible fixture run, not any named
		model or provider, and are not billed cost.
	</p>
</div>

<style>
	.sim-banner {
		position: sticky;
		top: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-2) var(--space-4);
		background: var(--color-banner-bg);
		color: var(--color-banner-fg);
		border-bottom: 3px solid var(--color-banner-border);
	}

	.sim-banner__icon {
		font-size: 1.2rem;
		line-height: 1;
		flex-shrink: 0;
	}

	.sim-banner__text {
		margin: 0;
		font-size: 0.85rem;
		line-height: 1.4;
	}

	.sim-banner__text strong {
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}
</style>
