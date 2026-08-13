<script lang="ts">
	import { scaleLinear } from 'd3-scale';
	import ChartFrame, { type ChartFrameRow } from '$lib/components/ChartFrame.svelte';
	import { formatPercent, formatRateCI, isCISuppressed, suppressedCILabel } from '$lib/format';
	import type { Rate } from '$lib/types';

	export interface RateItem {
		label: string;
		rate: Rate;
	}

	interface Props {
		title: string;
		caption: string;
		method: string;
		denominator: number;
		items: RateItem[];
	}

	let { title, caption, method, denominator, items }: Props = $props();

	const width = 560;
	const rowHeight = 44;
	const leftLabelWidth = 170;
	const plotWidth = width - leftLabelWidth - 90;
	const height = $derived(items.length * rowHeight + 24);

	const x = $derived(scaleLinear().domain([0, 1]).range([0, plotWidth]).clamp(true));

	const rows: ChartFrameRow[] = $derived(
		items.map((item) => ({
			label: item.label,
			value: `${item.rate.display} = ${formatPercent(item.rate.rate)}, CI ${formatRateCI(item.rate)}, flags: ${
				item.rate.ci_flags.length ? item.rate.ci_flags.join('; ') : 'none'
			}`
		}))
	);
</script>

<ChartFrame {title} {caption} {method} {denominator} units="%" {rows}>
	<svg viewBox="0 0 {width} {height}" width={width} height={height} role="presentation">
		{#each items as item, i (item.label)}
			{@const cy = i * rowHeight + rowHeight / 2 + 12}
			{@const barW = item.rate.rate === null ? 0 : x(item.rate.rate)}
			<text x="0" y={cy} dy="0.32em" class="rbc-label">{item.label}</text>
			<g transform="translate({leftLabelWidth}, 0)">
				<rect x="0" y={cy - 10} width={plotWidth} height="20" class="rbc-track" rx="4" />
				{#if item.rate.rate !== null}
					<rect x="0" y={cy - 10} width={barW} height="20" class="rbc-bar" rx="4" />
				{/if}
				{#if !isCISuppressed(item.rate) && item.rate.ci_low !== null && item.rate.ci_high !== null}
					{@const xLo = x(item.rate.ci_low)}
					{@const xHi = x(item.rate.ci_high)}
					<line x1={xLo} x2={xHi} y1={cy} y2={cy} class="rbc-whisker" />
					<line x1={xLo} x2={xLo} y1={cy - 6} y2={cy + 6} class="rbc-whisker-cap" />
					<line x1={xHi} x2={xHi} y1={cy - 6} y2={cy + 6} class="rbc-whisker-cap" />
				{/if}
				<text x={plotWidth + 10} y={cy} dy="0.32em" class="rbc-value">
					{item.rate.rate === null ? 'n/a' : formatPercent(item.rate.rate)}
					({item.rate.display})
				</text>
				{#if isCISuppressed(item.rate)}
					<text x={plotWidth + 10} y={cy + 16} class="rbc-suppressed">
						{suppressedCILabel(item.rate.denominator)}
					</text>
				{/if}
			</g>
		{/each}
	</svg>
</ChartFrame>

<style>
	.rbc-label {
		font-size: 0.85rem;
		fill: var(--color-fg);
	}

	.rbc-value {
		font-size: 0.78rem;
		fill: var(--color-fg-muted);
	}

	.rbc-suppressed {
		font-size: 0.7rem;
		font-style: italic;
		fill: var(--color-bad);
	}

	.rbc-track {
		fill: var(--color-border);
	}

	.rbc-bar {
		fill: var(--color-series-1);
	}

	.rbc-whisker,
	.rbc-whisker-cap {
		stroke: var(--color-fg);
		stroke-width: 2;
	}
</style>
