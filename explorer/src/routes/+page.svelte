<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';

	let { data } = $props();

	const target = `${base}/${data.firstProfile}/overview`;

	onMount(() => {
		goto(target);
	});
</script>

<svelte:head>
	<title>Prism explorer</title>
	<meta http-equiv="refresh" content="0;url={target}" />
</svelte:head>

<p>
	Redirecting to the <strong>{data.firstProfile}</strong> overview… If you are not redirected
	automatically, <a href={target}>continue to the overview</a>.
</p>
