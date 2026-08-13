<script lang="ts">
	import { base } from '$app/paths';
	import { formatMs, formatPercent } from '$lib/format';

	let { data } = $props();
</script>

<svelte:head>
	<title>Prism · {data.profileId} · Families</title>
</svelte:head>

<h1>Families — {data.profileId}</h1>
<p class="hint">Each family is a fixed set of 6 cases. Select one to see the per-case breakdown.</p>

<div class="family-grid">
	{#each data.families as fam (fam.family)}
		<a class="family-card" href="{base}/{data.profileId}/families/{fam.family}">
			<h2>{fam.family}</h2>
			<dl>
				<div><dt>n</dt><dd>{fam.n}</dd></div>
				<div><dt>Task success</dt><dd>{formatPercent(fam.task_success.rate)} ({fam.task_success.display})</dd></div>
				<div><dt>Schema validity</dt><dd>{formatPercent(fam.schema_validity.rate)} ({fam.schema_validity.display})</dd></div>
				<div><dt>p90 latency</dt><dd>{formatMs(fam.latency.p90_ms)}</dd></div>
			</dl>
			<span class="family-card__cta">View cases →</span>
		</a>
	{/each}
</div>

<style>
	.hint {
		color: var(--color-fg-muted);
		font-size: 0.9rem;
	}

	.family-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
		gap: var(--space-4);
		margin-top: var(--space-4);
	}

	.family-card {
		display: block;
		padding: var(--space-4);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		text-decoration: none;
		color: inherit;
		background: var(--color-bg-raised);
	}

	.family-card:hover {
		border-color: var(--color-link);
	}

	.family-card h2 {
		margin: 0 0 var(--space-2);
		font-size: 1.05rem;
		text-transform: capitalize;
	}

	.family-card dl {
		display: grid;
		gap: 4px;
		margin: 0 0 var(--space-3);
		font-size: 0.85rem;
	}

	.family-card dl div {
		display: flex;
		justify-content: space-between;
		gap: var(--space-2);
	}

	.family-card dt {
		color: var(--color-fg-muted);
	}

	.family-card__cta {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--color-link);
	}
</style>
