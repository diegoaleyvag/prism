<script lang="ts">
	import type { Snippet } from 'svelte';

	export interface ChartFrameRow {
		label: string;
		value: string;
	}

	interface Props {
		/** Short human title for the chart, e.g. "Task success by family". */
		title: string;
		/** The n backing this chart (denominator of the underlying rate/sample). */
		denominator: number;
		/** How the numbers were produced, e.g. "percentile bootstrap, B=10000, level=0.95". */
		method: string;
		/** Unit of the plotted values, e.g. "%", "ms", "USD". */
		units: string;
		/** One or two sentences of context, repeated for every chart per the SIMULATED policy. */
		caption: string;
		/** Rows backing the visually-hidden data table fallback. */
		rows?: ChartFrameRow[];
		/** Override the computed aria-label if a more specific summary is available. */
		ariaLabel?: string;
		children: Snippet;
	}

	let { title, denominator, method, units, caption, rows = [], ariaLabel, children }: Props =
		$props();

	// Validate once, synchronously, at component initialization — including
	// during prerendering (SSR), not just after client hydration. This is a
	// deliberate one-time guard-clause read of the initial prop values (not a
	// reactive computation), so it intentionally sits outside `$derived`/
	// `$effect`; Svelte's `state_referenced_locally` warning is expected and
	// safe to ignore here.
	if (import.meta.env.DEV) {
		const initial = { title, denominator, method };
		if (!initial.title || !initial.title.trim()) {
			throw new Error('ChartFrame: "title" prop is required and must not be empty.');
		}
		if (initial.denominator === undefined || initial.denominator === null || Number.isNaN(initial.denominator)) {
			throw new Error('ChartFrame: "denominator" prop is required.');
		}
		if (!initial.method || !initial.method.trim()) {
			throw new Error('ChartFrame: "method" prop is required and must not be empty.');
		}
	}

	const computedAriaLabel = $derived(
		ariaLabel ?? `${title}. n=${denominator}. Units: ${units}. Method: ${method}.`
	);
</script>

<figure class="chart-frame">
	<figcaption class="chart-frame__title">{title}</figcaption>
	<div class="chart-frame__body" role="img" aria-label={computedAriaLabel}>
		{@render children()}
	</div>

	<table class="chart-frame__fallback sr-only">
		<caption>{title} — underlying data ({units})</caption>
		<thead>
			<tr>
				<th scope="col">Series</th>
				<th scope="col">Value</th>
			</tr>
		</thead>
		<tbody>
			{#each rows as row (row.label)}
				<tr>
					<td>{row.label}</td>
					<td>{row.value}</td>
				</tr>
			{/each}
		</tbody>
	</table>

	<p class="chart-frame__caption">
		{caption}
		<span class="chart-frame__disclaimer">SIMULATED — deterministic fixtures, not named-model performance.</span>
		<span class="chart-frame__method">Method: {method}. n={denominator}.</span>
	</p>
</figure>

<style>
	.chart-frame {
		margin: 0;
		padding: var(--space-4);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-bg-raised);
	}

	.chart-frame__title {
		font-weight: 600;
		margin-bottom: var(--space-3);
	}

	.chart-frame__body {
		width: 100%;
		overflow-x: auto;
	}

	.chart-frame__caption {
		margin: var(--space-3) 0 0;
		font-size: 0.85rem;
		color: var(--color-fg-muted);
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}

	.chart-frame__disclaimer {
		font-style: italic;
	}

	.chart-frame__method {
		font-family: var(--font-mono);
	}
</style>
