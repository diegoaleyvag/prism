<script lang="ts">
	import { base } from '$app/paths';
	import { extent } from 'd3-array';
	import { scaleLinear } from 'd3-scale';
	import ChartFrame, { type ChartFrameRow } from '$lib/components/ChartFrame.svelte';
	import { formatMs, formatPercent, formatUsd } from '$lib/format';
	import type { ParetoAxes, ParetoPoint } from '$lib/types';

	interface Props {
		points: ParetoPoint[];
		axes: ParetoAxes;
		caption: string;
		method: string;
	}

	let { points, axes, caption, method }: Props = $props();

	type XMetric = 'cost_usd' | 'latency_p90_ms';
	let xMetric: XMetric = $state('cost_usd');

	const width = 560;
	const height = 360;
	const margin = { top: 20, right: 30, bottom: 50, left: 60 };
	const plotW = width - margin.left - margin.right;
	const plotH = height - margin.top - margin.bottom;

	const xValues = $derived(points.map((p) => p[xMetric]));
	const yValues = $derived(points.map((p) => p.quality));

	const xDomain = $derived.by(() => {
		const [lo, hi] = extent(xValues) as [number, number];
		if (lo === hi) return [0, (hi || 1) * 1.2];
		const pad = (hi - lo) * 0.15;
		return [Math.max(0, lo - pad), hi + pad];
	});

	const yDomain = $derived.by(() => {
		const [lo, hi] = extent(yValues) as [number, number];
		const padLo = Math.max(0, lo - 0.1);
		const padHi = Math.min(1, hi + 0.1);
		return [padLo, padHi];
	});

	const x = $derived(scaleLinear().domain(xDomain).range([0, plotW]).nice());
	const y = $derived(scaleLinear().domain(yDomain).range([plotH, 0]).nice());

	const xLabel = $derived(xMetric === 'cost_usd' ? `Cost (${axes.cost_usd})` : `Latency (${axes.latency_p90_ms})`);
	const yLabel = $derived(`Quality (${axes.quality})`);

	function formatX(value: number): string {
		return xMetric === 'cost_usd' ? formatUsd(value) : formatMs(value);
	}

	const rows: ChartFrameRow[] = $derived(
		points.map((p) => ({
			label: p.profile_id,
			value: `quality=${formatPercent(p.quality)}, cost=${formatUsd(p.cost_usd)}, latency_p90=${formatMs(p.latency_p90_ms)}, frontier=${p.on_frontier ? 'yes' : 'no'}`
		}))
	);

	const xTicks = $derived(x.ticks(5));
	const yTicks = $derived(y.ticks(5));
</script>

<ChartFrame
	title="Quality vs {xMetric === 'cost_usd' ? 'cost' : 'latency'}"
	{caption}
	{method}
	denominator={points.length}
	units="quality fraction vs {xMetric === 'cost_usd' ? 'USD' : 'ms'}"
	{rows}
>
	<div class="pareto-toggle" role="group" aria-label="Choose x-axis metric">
		<button type="button" class:active={xMetric === 'cost_usd'} onclick={() => (xMetric = 'cost_usd')}>
			Quality vs Cost
		</button>
		<button
			type="button"
			class:active={xMetric === 'latency_p90_ms'}
			onclick={() => (xMetric = 'latency_p90_ms')}
		>
			Quality vs Latency (p90)
		</button>
	</div>

	<svg viewBox="0 0 {width} {height}" width={width} height={height} role="presentation">
		<g transform="translate({margin.left}, {margin.top})">
			<!-- axes -->
			<line x1="0" x2={plotW} y1={plotH} y2={plotH} class="axis-line" />
			<line x1="0" x2="0" y1="0" y2={plotH} class="axis-line" />

			{#each xTicks as t (t)}
				<line x1={x(t)} x2={x(t)} y1={plotH} y2={plotH + 6} class="tick-line" />
				<text x={x(t)} y={plotH + 22} class="tick-label" text-anchor="middle">{formatX(t)}</text>
			{/each}

			{#each yTicks as t (t)}
				<line x1="-6" x2="0" y1={y(t)} y2={y(t)} class="tick-line" />
				<text x="-10" y={y(t)} class="tick-label" text-anchor="end" dy="0.32em">{formatPercent(t, 0)}</text>
			{/each}

			<text x={plotW / 2} y={plotH + 42} class="axis-label" text-anchor="middle">{xLabel}</text>
			<text
				x={-plotH / 2}
				y={-42}
				class="axis-label"
				text-anchor="middle"
				transform="rotate(-90)"
			>
				{yLabel}
			</text>

			{#each points as p (p.profile_id)}
				<a href="{base}/{p.profile_id}/overview" aria-label="{p.profile_id}: quality {formatPercent(p.quality)}, {xLabel} {formatX(p[xMetric])}{p.on_frontier ? ', on Pareto frontier' : ''}">
					{#if p.on_frontier}
						<rect
							x={x(p[xMetric]) - 8}
							y={y(p.quality) - 8}
							width="16"
							height="16"
							class="point point--frontier"
							transform="rotate(45 {x(p[xMetric])} {y(p.quality)})"
						/>
					{:else}
						<circle cx={x(p[xMetric])} cy={y(p.quality)} r="7" class="point" />
					{/if}
					<text x={x(p[xMetric]) + 12} y={y(p.quality)} dy="0.32em" class="point-label">
						{p.profile_id}{p.on_frontier ? ' (frontier)' : ''}
					</text>
				</a>
			{/each}
		</g>
	</svg>
	<p class="pareto-legend">
		<span class="legend-item"><span class="legend-swatch legend-swatch--frontier"></span> Diamond = on Pareto frontier</span>
		<span class="legend-item"><span class="legend-swatch legend-swatch--point"></span> Circle = dominated</span>
	</p>
</ChartFrame>

<style>
	.pareto-toggle {
		display: flex;
		gap: var(--space-2);
		margin-bottom: var(--space-3);
	}

	.pareto-toggle button {
		padding: var(--space-2) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-bg);
		color: var(--color-fg);
		cursor: pointer;
		font-size: 0.85rem;
	}

	.pareto-toggle button.active {
		background: var(--color-series-1);
		color: white;
		border-color: var(--color-series-1);
		font-weight: 600;
	}

	.axis-line {
		stroke: var(--color-fg-muted);
		stroke-width: 1;
	}

	.tick-line {
		stroke: var(--color-fg-muted);
		stroke-width: 1;
	}

	.tick-label {
		font-size: 0.7rem;
		fill: var(--color-fg-muted);
	}

	.axis-label {
		font-size: 0.8rem;
		fill: var(--color-fg);
	}

	.point {
		fill: var(--color-series-2);
		stroke: var(--color-bg);
		stroke-width: 1.5;
	}

	.point--frontier {
		fill: var(--color-series-1);
		stroke: var(--color-bg);
		stroke-width: 1.5;
	}

	.point-label {
		font-size: 0.72rem;
		fill: var(--color-fg);
	}

	.pareto-legend {
		display: flex;
		gap: var(--space-4);
		font-size: 0.78rem;
		color: var(--color-fg-muted);
		margin-top: var(--space-2);
	}

	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
	}

	.legend-swatch {
		display: inline-block;
		width: 10px;
		height: 10px;
	}

	.legend-swatch--frontier {
		background: var(--color-series-1);
		transform: rotate(45deg);
	}

	.legend-swatch--point {
		background: var(--color-series-2);
		border-radius: 50%;
	}
</style>
