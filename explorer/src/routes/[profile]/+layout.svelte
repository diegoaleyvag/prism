<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { profileIds } from '$lib/data';

	let { data, children } = $props();

	const tabs = [
		{ href: (p: string) => `${base}/${p}/overview`, label: 'Overview' },
		{ href: (p: string) => `${base}/${p}/families`, label: 'Families' },
		{ href: (p: string) => `${base}/${p}/failures`, label: 'Failures' },
		{ href: (p: string) => `${base}/${p}/uncertainty`, label: 'Uncertainty' },
		{ href: (p: string) => `${base}/${p}/pareto`, label: 'Pareto' }
	];

	const otherProfiles = $derived(profileIds().filter((p) => p !== data.profileId));

	function isActive(href: string): boolean {
		return page.url.pathname.replace(/\/+$/, '') === href.replace(/\/+$/, '');
	}
</script>

<div class="profile-shell">
	<nav class="profile-nav" aria-label="Profile sections">
		<span class="profile-nav__current">
			Profile: <strong>{data.profileId}</strong>
		</span>
		<ul class="profile-nav__tabs">
			{#each tabs as tab (tab.label)}
				{@const href = tab.href(data.profileId)}
				<li>
					<a {href} aria-current={isActive(href) ? 'page' : undefined}>{tab.label}</a>
				</li>
			{/each}
		</ul>
		{#if otherProfiles.length}
			<div class="profile-nav__switch">
				Compare:
				{#each otherProfiles as other (other)}
					<a href="{base}/{other}/overview">{other}</a>
				{/each}
			</div>
		{/if}
	</nav>

	{@render children()}
</div>

<style>
	.profile-shell {
		display: flex;
		flex-direction: column;
		gap: var(--space-5);
	}

	.profile-nav {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--space-4);
		padding-bottom: var(--space-3);
		border-bottom: 1px solid var(--color-border);
	}

	.profile-nav__current {
		font-size: 0.85rem;
		color: var(--color-fg-muted);
	}

	.profile-nav__tabs {
		display: flex;
		gap: var(--space-3);
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.profile-nav__tabs a {
		text-decoration: none;
		padding: var(--space-1) var(--space-2);
		border-radius: var(--radius);
		color: var(--color-fg);
	}

	.profile-nav__tabs a[aria-current='page'] {
		background: var(--color-series-1);
		color: white;
		font-weight: 600;
	}

	.profile-nav__switch {
		font-size: 0.82rem;
		color: var(--color-fg-muted);
		display: flex;
		gap: var(--space-2);
		margin-left: auto;
	}
</style>
