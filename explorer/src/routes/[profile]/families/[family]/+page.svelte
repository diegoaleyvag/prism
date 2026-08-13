<script lang="ts">
	import { base } from '$app/paths';
	import RateBarCI, { type RateItem } from '$lib/charts/RateBarCI.svelte';
	import { formatMethod, formatMs, formatUsd } from '$lib/format';

	let { data } = $props();

	const m = $derived(data.familyMetrics);

	const method = $derived(formatMethod(m.task_success.method));

	const rateItems: RateItem[] = $derived(
		[
			{ label: 'Task success', rate: m.task_success },
			{ label: 'Schema validity', rate: m.schema_validity },
			{ label: 'Correct escalation', rate: m.correct_escalation },
			{ label: 'Over-refusal', rate: m.over_refusal }
		].filter((item): item is RateItem => item.rate !== null)
	);
</script>

<svelte:head>
	<title>Prism · {data.profileId} · {data.family}</title>
</svelte:head>

<p class="breadcrumb">
	<a href="{base}/{data.profileId}/families">← All families</a>
</p>

<h1>{data.family} — {data.profileId}</h1>
<p class="hint">
	{m.n} cases in this family. n_hard/n_stable guardrail thresholds apply per-metric, so some
	intervals below are suppressed even though every case is shown.
</p>

<RateBarCI
	title="Family outcome rates — {data.family}"
	caption="{m.n} cases in the {data.family} family, profile {data.profileId}."
	{method}
	denominator={m.n}
	items={rateItems}
/>

<section class="cases-section">
	<h2>Cases</h2>
	<table class="cases-table">
		<thead>
			<tr>
				<th scope="col">Case</th>
				<th scope="col">Behavior class</th>
				<th scope="col">Schema valid</th>
				<th scope="col">Task success</th>
				<th scope="col">Latency</th>
				<th scope="col">Cost</th>
				<th scope="col"></th>
			</tr>
		</thead>
		<tbody>
			{#each data.familyCases as row (row.case_id)}
				<tr>
					<td><code>{row.case_id}</code></td>
					<td>{row.behavior_class.replaceAll('_', ' ')}</td>
					<td>
						<span class="status" class:status--pass={row.schema_valid} class:status--fail={!row.schema_valid}>
							{row.schema_valid ? 'Valid' : 'Invalid'}
						</span>
					</td>
					<td>
						<span class="status" class:status--pass={row.task_success} class:status--fail={!row.task_success}>
							{row.task_success ? 'Pass' : 'Fail'}
						</span>
					</td>
					<td>{formatMs(row.latency_ms)}</td>
					<td>{formatUsd(row.cost_usd)}</td>
					<td><a href="{base}/{data.profileId}/cases/{row.case_id}">Detail →</a></td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<style>
	.breadcrumb {
		font-size: 0.85rem;
	}

	.hint {
		color: var(--color-fg-muted);
		font-size: 0.9rem;
	}

	.cases-section {
		margin-top: var(--space-5);
	}

	.cases-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.88rem;
	}

	.cases-table th,
	.cases-table td {
		padding: var(--space-2) var(--space-3);
		border-bottom: 1px solid var(--color-border);
		text-align: left;
	}

	.status {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-weight: 600;
		font-size: 0.8rem;
	}

	.status::before {
		content: '';
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.status--pass {
		color: var(--color-good);
	}

	.status--pass::before {
		background: var(--color-good);
	}

	.status--fail {
		color: var(--color-bad);
	}

	.status--fail::before {
		background: var(--color-bad);
	}
</style>
