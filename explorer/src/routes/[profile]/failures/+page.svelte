<script lang="ts">
	import { base } from '$app/paths';
	import { formatMs, formatUsd } from '$lib/format';

	let { data } = $props();

	let familyFilter: string = $state('all');

	const families = $derived(
		Array.from(new Set(data.rows.map((r) => r.family))).sort((a, b) => a.localeCompare(b))
	);

	const filteredRows = $derived(
		familyFilter === 'all' ? data.rows : data.rows.filter((r) => r.family === familyFilter)
	);
</script>

<svelte:head>
	<title>Prism · {data.profileId} · Failures</title>
</svelte:head>

<h1>Failures — {data.profileId}</h1>
<p class="hint">
	{data.rows.length} of the release-scope cases failed at least one metric for this profile.
	Every row links to the redacted case detail.
</p>

<div class="filter-bar">
	<label for="family-filter">Filter by family</label>
	<select id="family-filter" bind:value={familyFilter}>
		<option value="all">All families ({data.rows.length})</option>
		{#each families as fam (fam)}
			<option value={fam}>{fam} ({data.rows.filter((r) => r.family === fam).length})</option>
		{/each}
	</select>
</div>

{#if filteredRows.length === 0}
	<p class="empty">No failing cases for this filter.</p>
{:else}
	<div class="table-scroll">
	<table class="failures-table">
		<thead>
			<tr>
				<th scope="col">Case</th>
				<th scope="col">Family</th>
				<th scope="col">Failed metric</th>
				<th scope="col">Reason</th>
				<th scope="col">Latency</th>
				<th scope="col">Cost</th>
				<th scope="col"></th>
			</tr>
		</thead>
		<tbody>
			{#each filteredRows as row (row.case_id)}
				<tr>
					<td><code>{row.case_id}</code></td>
					<td>{row.family}</td>
					<td><span class="failed-metric">{row.failed_metric ?? 'unknown'}</span></td>
					<td class="reason-cell">{row.reason}</td>
					<td>{formatMs(row.latency_ms)}</td>
					<td>{formatUsd(row.cost_usd)}</td>
					<td><a href="{base}/{data.profileId}/cases/{row.case_id}">Detail →</a></td>
				</tr>
			{/each}
		</tbody>
	</table>
	</div>
{/if}

<style>
	.hint {
		color: var(--color-fg-muted);
		font-size: 0.9rem;
	}

	.filter-bar {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin: var(--space-4) 0;
		font-size: 0.9rem;
	}

	.filter-bar select {
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-bg);
		color: var(--color-fg);
	}

	.empty {
		color: var(--color-fg-muted);
		font-style: italic;
	}

	.failures-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}

	.failures-table th,
	.failures-table td {
		padding: var(--space-2) var(--space-3);
		border-bottom: 1px solid var(--color-border);
		text-align: left;
		vertical-align: top;
	}

	.reason-cell {
		max-width: 320px;
	}

	.failed-metric {
		display: inline-block;
		padding: 1px 6px;
		border-radius: 4px;
		background: color-mix(in srgb, var(--color-bad) 18%, transparent);
		color: var(--color-bad);
		font-size: 0.78rem;
		font-weight: 600;
	}
</style>
