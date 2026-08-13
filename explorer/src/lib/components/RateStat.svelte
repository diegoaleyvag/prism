<script lang="ts">
	import { formatPercent, formatRateCI, isCISuppressed } from '$lib/format';
	import type { Rate } from '$lib/types';

	interface Props {
		label: string;
		rate: Rate | null;
		href?: string;
	}

	let { label, rate, href }: Props = $props();
</script>

{#snippet body()}
	<span class="rate-stat__label">{label}</span>
	{#if rate === null}
		<span class="rate-stat__value rate-stat__value--na">n/a for this scope</span>
	{:else}
		<span class="rate-stat__value">{formatPercent(rate.rate)}</span>
		<span class="rate-stat__fraction">{rate.display}</span>
		<span class="rate-stat__ci" class:rate-stat__ci--suppressed={isCISuppressed(rate)}>
			{formatRateCI(rate)}
		</span>
		{#if rate.ci_flags.length}
			<span class="rate-stat__flags">flags: {rate.ci_flags.join(', ')}</span>
		{/if}
	{/if}
{/snippet}

{#if href}
	<a class="rate-stat rate-stat--link" {href}>{@render body()}</a>
{:else}
	<div class="rate-stat">{@render body()}</div>
{/if}

<style>
	.rate-stat {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-bg-raised);
		color: inherit;
		text-decoration: none;
	}

	.rate-stat--link:hover {
		border-color: var(--color-link);
	}

	.rate-stat--link:hover .rate-stat__value {
		text-decoration: underline;
	}

	.rate-stat__label {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		color: var(--color-fg-muted);
	}

	.rate-stat__value {
		font-size: 1.5rem;
		font-weight: 700;
	}

	.rate-stat__value--na {
		font-size: 0.9rem;
		font-weight: 400;
		color: var(--color-fg-muted);
	}

	.rate-stat__fraction {
		font-size: 0.8rem;
		color: var(--color-fg-muted);
	}

	.rate-stat__ci {
		font-size: 0.78rem;
		font-family: var(--font-mono);
	}

	.rate-stat__ci--suppressed {
		color: var(--color-bad);
		font-style: italic;
	}

	.rate-stat__flags {
		font-size: 0.7rem;
		color: var(--color-fg-muted);
	}
</style>
