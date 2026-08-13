<script lang="ts">
	import type { ExplorerMode } from '$lib/types';

	interface Props {
		mode: ExplorerMode;
		active?: boolean;
	}

	let { mode, active = mode === 'fixture' }: Props = $props();

	const meta: Record<ExplorerMode, { icon: string; label: string }> = {
		fixture: { icon: '◆', label: 'Fixture' }, // diamond
		replay: { icon: '↻', label: 'Replay' }, // circular arrow
		live: { icon: '⚡', label: 'Live' } // lightning bolt
	};
</script>

<span
	class="mode-badge mode-badge--{mode}"
	class:mode-badge--disabled={!active}
	aria-disabled={!active}
	title={active ? `${meta[mode].label} mode` : `${meta[mode].label} mode (unavailable in this release)`}
>
	<span class="mode-badge__icon" aria-hidden="true">{meta[mode].icon}</span>
	<span class="mode-badge__label">{meta[mode].label}{active ? '' : ' (unavailable)'}</span>
</span>

<style>
	.mode-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: 2px var(--space-2);
		border-radius: 999px;
		font-size: 0.75rem;
		font-weight: 600;
		border: 1px solid transparent;
	}

	.mode-badge--fixture {
		background: color-mix(in srgb, var(--color-series-3) 20%, transparent);
		color: var(--color-series-3);
		border-color: var(--color-series-3);
	}

	.mode-badge--replay {
		background: color-mix(in srgb, var(--color-series-2) 20%, transparent);
		color: var(--color-series-2);
		border-color: var(--color-series-2);
	}

	.mode-badge--live {
		background: color-mix(in srgb, var(--color-series-4) 20%, transparent);
		color: var(--color-series-4);
		border-color: var(--color-series-4);
	}

	.mode-badge--disabled {
		opacity: 0.6;
		text-decoration: line-through;
		filter: grayscale(0.4);
	}

	.mode-badge__icon {
		line-height: 1;
	}
</style>
