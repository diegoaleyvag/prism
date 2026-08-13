import { error } from '@sveltejs/kit';
import { isKnownProfile, loadPareto, profileIds } from '$lib/data';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => profileIds().map((profile) => ({ profile }));

export const load: PageLoad = async ({ params, fetch }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}

	const pareto = await loadPareto(fetch);

	return {
		profileId: params.profile,
		axes: pareto.axes,
		points: pareto.points
	};
};
