<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import ChartFrame, { type ChartFrameRow } from '$lib/components/ChartFrame.svelte';
	import { formatMs } from '$lib/format';
	import type { LatencyStats } from '$lib/types';

	interface Props {
		title: string;
		caption: string;
		latency: LatencyStats;
	}

	let { title, caption, latency }: Props = $props();

	const percentiles: { key: 'p50_ms' | 'p90_ms' | 'p95_ms' | 'p99_ms'; label: string }[] = [
		{ key: 'p50_ms', label: 'p50' },
		{ key: 'p90_ms', label: 'p90' },
		{ key: 'p95_ms', label: 'p95' },
		{ key: 'p99_ms', label: 'p99' }
	];

	const width = 480;
	const barHeight = 34;
	const gap = 14;
	const leftLabelWidth = 60;
	const plotWidth = width - leftLabelWidth - 90;
	const height = $derived(percentiles.length * (barHeight + gap));

	const x = $derived(scaleLinear().domain([0, latency.max_ms]).range([0, plotWidth]).nice());

	const rows: ChartFrameRow[] = $derived([
		...percentiles.map((p) => ({ label: p.label, value: formatMs(latency[p.key]) })),
		{ label: 'mean', value: formatMs(latency.mean_ms) },
		{ label: 'min', value: formatMs(latency.min_ms) },
		{ label: 'max', value: formatMs(latency.max_ms) }
	]);
</script>

<ChartFrame
	{title}
	{caption}
	method="percentile of {latency.n} recorded case latencies (fixture clock, simulated)"
	denominator={latency.n}
	units="ms"
	{rows}
>
	<svg viewBox="0 0 {width} {height}" width={width} height={height} role="presentation">
		{#each percentiles as p, i (p.key)}
			{@const y = i * (barHeight + gap)}
			{@const barW = x(latency[p.key])}
			<text x="0" y={y + barHeight / 2} dy="0.32em" class="ld-label">{p.label}</text>
			<g transform="translate({leftLabelWidth}, 0)">
				<rect x="0" y={y} width={plotWidth} height={barHeight} class="ld-track" rx="4" />
				<rect x="0" y={y} width={barW} height={barHeight} class="ld-bar" rx="4" />
				<text x={plotWidth + 10} y={y + barHeight / 2} dy="0.32em" class="ld-value">
					{formatMs(latency[p.key])}
				</text>
			</g>
		{/each}
	</svg>
	<p class="ld-summary">
		mean {formatMs(latency.mean_ms)} · min {formatMs(latency.min_ms)} · max {formatMs(latency.max_ms)} · n={latency.n}
	</p>
</ChartFrame>

<style>
	.ld-label {
		font-size: 0.85rem;
		fill: var(--color-fg);
		font-weight: 600;
	}

	.ld-value {
		font-size: 0.78rem;
		fill: var(--color-fg-muted);
	}

	.ld-track {
		fill: var(--color-border);
	}

	.ld-bar {
		fill: var(--color-series-3);
	}

	.ld-summary {
		margin-top: var(--space-2);
		font-size: 0.78rem;
		color: var(--color-fg-muted);
	}
</style>
