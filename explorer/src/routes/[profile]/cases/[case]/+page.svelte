<script lang="ts">
	import { base } from '$app/paths';
	import { formatMs, formatUsd } from '$lib/format';

	let { data } = $props();

	const row = $derived(data.row);
</script>

<svelte:head>
	<title>Prism · {data.profileId} · Case {data.caseId}</title>
</svelte:head>

<p class="breadcrumb">
	<a href="{base}/{data.profileId}/families/{row.family}">← {row.family}</a>
	·
	<a href="{base}/{data.profileId}/failures">All failures</a>
</p>

<h1>Case {row.case_id} — {data.profileId}</h1>

<section class="status-row">
	<span class="status" class:status--pass={row.schema_valid} class:status--fail={!row.schema_valid}>
		Schema {row.schema_valid ? 'valid' : 'invalid'}
	</span>
	<span class="status" class:status--pass={row.task_success} class:status--fail={!row.task_success}>
		Task {row.task_success ? 'success' : 'failure'}
	</span>
	{#if row.abstention_correct !== null}
		<span class="status" class:status--pass={row.abstention_correct} class:status--fail={!row.abstention_correct}>
			Abstention {row.abstention_correct ? 'correct' : 'incorrect'}
		</span>
	{/if}
	<span class="behavior-tag">behavior: {row.behavior_class.replaceAll('_', ' ')}</span>
</section>

{#if row.failed_metric}
	<section class="failure-note">
		<h2>Why this case failed</h2>
		<p><strong>Failed metric:</strong> {row.failed_metric}</p>
		<p><strong>Reason:</strong> {row.reason}</p>
	</section>
{:else}
	<section class="failure-note failure-note--pass">
		<p><strong>Reason:</strong> {row.reason}</p>
	</section>
{/if}

<section class="excerpts">
	<h2>Redacted excerpts <span class="badge-sim">SIMULATED</span></h2>
	<div class="excerpt-grid">
		<div class="excerpt-card">
			<h3>Input</h3>
			<p>{row.input_excerpt}</p>
		</div>
		<div class="excerpt-card">
			<h3>Expected</h3>
			<pre>{row.expected_summary}</pre>
		</div>
		<div class="excerpt-card">
			<h3>Output</h3>
			<pre>{row.output_summary}</pre>
		</div>
	</div>
</section>

<section class="metrics">
	<h2>Metrics</h2>
	<table class="kv-table">
		<tbody>
			<tr><th scope="row">Family</th><td>{row.family}</td></tr>
			<tr><th scope="row">Latency</th><td>{formatMs(row.latency_ms)}</td></tr>
			<tr><th scope="row">Tokens (in / out / total)</th><td>{row.input_tokens} / {row.output_tokens} / {row.total_tokens}</td></tr>
			<tr><th scope="row">Cost</th><td>{formatUsd(row.cost_usd)}</td></tr>
			<tr><th scope="row">Review label</th><td>{row.review_label}</td></tr>
			<tr><th scope="row">Record id</th><td class="mono">{row.record_id}</td></tr>
		</tbody>
	</table>
</section>

<style>
	.breadcrumb {
		font-size: 0.85rem;
	}

	.status-row {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-3);
		align-items: center;
		margin: var(--space-3) 0 var(--space-5);
	}

	.status {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-weight: 600;
		font-size: 0.85rem;
		padding: 4px 10px;
		border-radius: 999px;
		border: 1px solid var(--color-border);
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

	.behavior-tag {
		font-size: 0.8rem;
		color: var(--color-fg-muted);
	}

	.failure-note {
		padding: var(--space-3) var(--space-4);
		border-left: 4px solid var(--color-bad);
		background: color-mix(in srgb, var(--color-bad) 8%, transparent);
		margin-bottom: var(--space-5);
	}

	.failure-note--pass {
		border-left-color: var(--color-good);
		background: color-mix(in srgb, var(--color-good) 8%, transparent);
	}

	.failure-note p {
		margin: var(--space-1) 0;
		font-size: 0.9rem;
	}

	.excerpts h2,
	.metrics h2 {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: 1.05rem;
	}

	.badge-sim {
		font-size: 0.65rem;
		font-weight: 700;
		padding: 1px 6px;
		border-radius: 4px;
		background: var(--color-banner-bg);
		color: var(--color-banner-fg);
	}

	.excerpt-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: var(--space-3);
		margin-bottom: var(--space-5);
	}

	.excerpt-card {
		padding: var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-bg-raised);
	}

	.excerpt-card h3 {
		margin: 0 0 var(--space-2);
		font-size: 0.8rem;
		text-transform: uppercase;
		color: var(--color-fg-muted);
	}

	.excerpt-card pre {
		white-space: pre-wrap;
		word-break: break-word;
		margin: 0;
		font-size: 0.82rem;
	}

	.excerpt-card p {
		margin: 0;
		font-size: 0.9rem;
	}

	.kv-table {
		width: 100%;
		font-size: 0.88rem;
	}

	.kv-table th {
		text-align: left;
		color: var(--color-fg-muted);
		font-weight: 400;
		padding: 4px 0;
		width: 220px;
	}

	.kv-table td {
		padding: 4px 0;
	}

	.mono {
		font-family: var(--font-mono);
		font-size: 0.78rem;
		word-break: break-all;
	}
</style>
