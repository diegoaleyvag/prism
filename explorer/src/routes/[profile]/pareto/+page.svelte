<script lang="ts">
	import ParetoScatter from '$lib/charts/ParetoScatter.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>Prism · {data.profileId} · Pareto</title>
</svelte:head>

<h1>Pareto frontier — quality vs. cost/latency</h1>
<p class="hint">
	Every profile in the release review scope, plotted by aggregate task success against mean cost
	per case and p90 latency. This chart compares all profiles at once — toggle the x-axis, and
	click any point to jump to that profile's overview. You are currently viewing profile
	<strong>{data.profileId}</strong>.
</p>

<ParetoScatter
	points={data.points}
	axes={data.axes}
	caption="Aggregate quality vs. cost/latency across all profiles in this release's review scope. Frontier points are not dominated on both axes by any other profile."
	method="deterministic Pareto-frontier computation over aggregate task_success_rate, mean cost per case, and p90 latency (simulated fixture run, no sampling)"
/>

<style>
	.hint {
		color: var(--color-fg-muted);
		font-size: 0.9rem;
		max-width: 70ch;
	}
</style>
