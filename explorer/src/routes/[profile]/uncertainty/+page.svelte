<script lang="ts">
	import RateBarCI, { type RateItem } from '$lib/charts/RateBarCI.svelte';
	import { formatMethod, formatPercent, formatRateCI, isCISuppressed } from '$lib/format';
	import type { Rate } from '$lib/types';

	let { data } = $props();

	const metricOrder: Record<string, string> = {
		task_success_rate: 'Task success',
		schema_validity_rate: 'Schema validity',
		correct_escalation_rate: 'Correct escalation',
		over_refusal_rate: 'Over-refusal'
	};
	const orderedIds = Object.keys(metricOrder);

	interface Bucket {
		key: string;
		title: string;
		family: string | null;
		metrics: Rate[];
	}

	const buckets: Bucket[] = $derived.by(() => {
		const byKey = new Map<string, Bucket>();
		for (const metric of data.metrics) {
			const key = metric.scope === 'aggregate' ? 'aggregate' : `family:${metric.family}`;
			if (!byKey.has(key)) {
				byKey.set(key, {
					key,
					title: metric.scope === 'aggregate' ? 'Aggregate' : (metric.family as string),
					family: metric.family,
					metrics: []
				});
			}
			byKey.get(key)!.metrics.push(metric);
		}
		const list = Array.from(byKey.values());
		for (const bucket of list) {
			bucket.metrics.sort((a, b) => orderedIds.indexOf(a.metric_id) - orderedIds.indexOf(b.metric_id));
		}
		list.sort((a, b) => {
			if (a.key === 'aggregate') return -1;
			if (b.key === 'aggregate') return 1;
			return a.title.localeCompare(b.title);
		});
		return list;
	});

	function items(bucket: Bucket): RateItem[] {
		return bucket.metrics.map((m) => ({ label: metricOrder[m.metric_id] ?? m.metric_id, rate: m }));
	}

	function bucketMethod(bucket: Bucket): string {
		const seed = bucket.metrics.find((m) => m.seed !== null)?.seed ?? null;
		return formatMethod(data.guardrail.method, {
			resamples: data.guardrail.resamples,
			level: data.guardrail.level,
			seed
		});
	}

	function bucketDenominator(bucket: Bucket): number {
		return Math.max(...bucket.metrics.map((m) => m.denominator));
	}
</script>

<svelte:head>
	<title>Prism · {data.profileId} · Uncertainty</title>
</svelte:head>

<h1>Uncertainty — {data.profileId}</h1>
<p class="hint">
	Bootstrap confidence intervals via {data.guardrail.method.replaceAll('_', ' ')} (B={data.guardrail.resamples},
	level={data.guardrail.level}). Intervals are suppressed below n={data.guardrail.n_hard} and flagged as
	unstable below n={data.guardrail.n_stable}. A suppressed CI means "not enough data for a reliable
	interval," not zero uncertainty — always read the denominator and flags alongside the point estimate.
</p>

{#each buckets as bucket (bucket.key)}
	<section class="bucket">
		<h2>{bucket.title}</h2>

		<RateBarCI
			title="{bucket.title} — bootstrap CIs"
			caption="{bucket.title === 'Aggregate' ? 'All' : bucket.title} cases, profile {data.profileId}. CI suppressed rows below show the guardrail reason instead of a fabricated interval."
			method={bucketMethod(bucket)}
			denominator={bucketDenominator(bucket)}
			items={items(bucket)}
		/>

		<table class="metrics-table">
			<caption class="visually-hidden">{bucket.title} metric detail</caption>
			<thead>
				<tr>
					<th scope="col">Metric</th>
					<th scope="col">n</th>
					<th scope="col">Rate</th>
					<th scope="col">CI</th>
					<th scope="col">Flags</th>
					<th scope="col">Method</th>
					<th scope="col">Seed</th>
				</tr>
			</thead>
			<tbody>
				{#each bucket.metrics as metric (metric.metric_id)}
					<tr>
						<td>{metricOrder[metric.metric_id] ?? metric.metric_id}</td>
						<td>{metric.denominator}</td>
						<td>{formatPercent(metric.rate)} ({metric.display})</td>
						<td class:suppressed={isCISuppressed(metric)}>{formatRateCI(metric)}</td>
						<td>{metric.ci_flags.length ? metric.ci_flags.join(', ') : '—'}</td>
						<td><code>{metric.method}</code></td>
						<td>{metric.seed ?? '—'}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
{/each}

<style>
	.hint {
		color: var(--color-fg-muted);
		font-size: 0.9rem;
		max-width: 70ch;
	}

	.bucket {
		margin: var(--space-6) 0;
		padding-top: var(--space-4);
		border-top: 1px solid var(--color-border);
	}

	.bucket h2 {
		text-transform: capitalize;
	}

	.metrics-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.82rem;
		margin-top: var(--space-3);
	}

	.metrics-table th,
	.metrics-table td {
		padding: var(--space-2) var(--space-3);
		border-bottom: 1px solid var(--color-border);
		text-align: left;
	}

	.suppressed {
		color: var(--color-bad);
		font-style: italic;
	}
</style>
