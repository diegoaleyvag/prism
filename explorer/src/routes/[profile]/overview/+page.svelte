<script lang="ts">
	import { base } from '$app/paths';
	import RateStat from '$lib/components/RateStat.svelte';
	import RateBarCI, { type RateItem } from '$lib/charts/RateBarCI.svelte';
	import LatencyDist from '$lib/charts/LatencyDist.svelte';
	import { formatMethod, formatMs, formatPercent, formatUsd } from '$lib/format';

	let { data } = $props();

	const agg = $derived(data.aggregate);

	const method = $derived(
		formatMethod(data.guardrail.method, {
			resamples: data.guardrail.resamples,
			level: data.guardrail.level
		})
	);

	const rateItems: RateItem[] = $derived(
		[
			{ label: 'Task success', rate: agg.task_success },
			{ label: 'Schema validity', rate: agg.schema_validity },
			{ label: 'Correct escalation', rate: agg.correct_escalation },
			{ label: 'Over-refusal', rate: agg.over_refusal }
		].filter((item): item is RateItem => item.rate !== null)
	);
</script>

<svelte:head>
	<title>Prism · {data.profileId} · Overview</title>
</svelte:head>

<section class="page-header">
	<h1>Overview — {data.profileId}</h1>
	<p class="page-header__meta">
		review scope <code>{data.reviewScope}</code> · profile digest
		<code>{data.profileDigest.slice(0, 19)}…</code> · excluded records
		<strong>{data.excludedCount}</strong> · price table <code>{data.priceTableId}</code>
	</p>
	<p class="page-header__guardrail">
		Small-n guardrail: intervals are suppressed below n={data.guardrail.n_hard} (hard) and flagged
		as unstable below n={data.guardrail.n_stable}. Method: {method}.
	</p>
</section>

<section class="stat-grid" aria-label="Headline metrics">
	<RateStat label="Task success" rate={agg.task_success} href="{base}/{data.profileId}/failures" />
	<RateStat label="Schema validity" rate={agg.schema_validity} href="{base}/{data.profileId}/uncertainty" />
	<RateStat label="Correct escalation" rate={agg.correct_escalation} href="{base}/{data.profileId}/uncertainty" />
	<RateStat label="Over-refusal" rate={agg.over_refusal} href="{base}/{data.profileId}/uncertainty" />
</section>

<section class="chart-grid">
	<RateBarCI
		title="Aggregate outcome rates — {data.profileId}"
		caption="All {agg.n} records in the release review scope. Click a metric above for the full uncertainty breakdown."
		{method}
		denominator={agg.n}
		items={rateItems}
	/>

	<LatencyDist
		title="Latency distribution — {data.profileId}"
		caption="Latency percentiles over {agg.latency.n} recorded cases (simulated fixture clock)."
		latency={agg.latency}
	/>
</section>

<section class="detail-grid">
	<div class="detail-card">
		<h2>Tokens</h2>
		<table class="kv-table">
			<tbody>
				<tr><th scope="row">Input (mean / sum)</th><td>{agg.tokens.input_mean.toFixed(1)} / {agg.tokens.input_sum}</td></tr>
				<tr><th scope="row">Output (mean / sum)</th><td>{agg.tokens.output_mean.toFixed(1)} / {agg.tokens.output_sum}</td></tr>
				<tr><th scope="row">Total tokens</th><td>{agg.tokens.total_sum}</td></tr>
				<tr><th scope="row">n</th><td>{agg.tokens.n}</td></tr>
			</tbody>
		</table>
	</div>

	<div class="detail-card">
		<h2>Estimated cost <span class="badge-sim">SIMULATED</span></h2>
		<table class="kv-table">
			<tbody>
				<tr><th scope="row">Mean per case</th><td>{formatUsd(agg.cost.mean_usd)}</td></tr>
				<tr><th scope="row">Total</th><td>{formatUsd(agg.cost.total_usd)}</td></tr>
				<tr><th scope="row">Price table</th><td><code>{agg.cost.price_table_id}</code></td></tr>
				<tr><th scope="row">n</th><td>{agg.cost.n}</td></tr>
			</tbody>
		</table>
		<p class="detail-card__note">
			Simulated educational pricing only — not real provider pricing, not billed cost.
		</p>
	</div>
</section>

<section class="families-section">
	<h2>By family</h2>
	<p class="families-section__hint">
		Each family bundles 6 cases. Click through for the per-case breakdown and CI detail.
	</p>
	<table class="families-table">
		<thead>
			<tr>
				<th scope="col">Family</th>
				<th scope="col">n</th>
				<th scope="col">Task success</th>
				<th scope="col">Schema validity</th>
				<th scope="col">Mean latency (p90)</th>
				<th scope="col"></th>
			</tr>
		</thead>
		<tbody>
			{#each data.families as fam (fam.family)}
				<tr>
					<td>{fam.family}</td>
					<td>{fam.n}</td>
					<td>{formatPercent(fam.task_success.rate)} ({fam.task_success.display})</td>
					<td>{formatPercent(fam.schema_validity.rate)} ({fam.schema_validity.display})</td>
					<td>{formatMs(fam.latency.p90_ms)}</td>
					<td>
						<a href="{base}/{data.profileId}/families/{fam.family}">View cases →</a>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<style>
	.page-header h1 {
		margin: 0 0 var(--space-2);
	}

	.page-header__meta,
	.page-header__guardrail {
		margin: 0 0 var(--space-1);
		font-size: 0.85rem;
		color: var(--color-fg-muted);
	}

	.stat-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: var(--space-3);
		margin: var(--space-5) 0;
	}

	.chart-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
		gap: var(--space-4);
		margin-bottom: var(--space-5);
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: var(--space-4);
		margin-bottom: var(--space-5);
	}

	.detail-card {
		padding: var(--space-4);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
	}

	.detail-card h2 {
		margin-top: 0;
		font-size: 1rem;
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}

	.badge-sim {
		font-size: 0.65rem;
		font-weight: 700;
		padding: 1px 6px;
		border-radius: 4px;
		background: var(--color-banner-bg);
		color: var(--color-banner-fg);
	}

	.kv-table {
		width: 100%;
		font-size: 0.85rem;
	}

	.kv-table th {
		text-align: left;
		color: var(--color-fg-muted);
		font-weight: 400;
		padding: 2px 0;
	}

	.kv-table td {
		text-align: right;
		padding: 2px 0;
	}

	.detail-card__note {
		margin: var(--space-2) 0 0;
		font-size: 0.75rem;
		font-style: italic;
		color: var(--color-fg-muted);
	}

	.families-section__hint {
		font-size: 0.85rem;
		color: var(--color-fg-muted);
	}

	.families-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.88rem;
	}

	.families-table th,
	.families-table td {
		padding: var(--space-2) var(--space-3);
		border-bottom: 1px solid var(--color-border);
		text-align: left;
	}
</style>
