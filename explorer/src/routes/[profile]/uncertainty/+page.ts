import { error } from '@sveltejs/kit';
import { isKnownProfile, loadUncertainty, profileIds } from '$lib/data';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => profileIds().map((profile) => ({ profile }));

export const load: PageLoad = async ({ params, fetch }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}

	const uncertainty = await loadUncertainty(fetch);
	const metrics = uncertainty.metrics.filter((m) => m.profile_id === params.profile);

	return {
		profileId: params.profile,
		guardrail: uncertainty.guardrail,
		metrics
	};
};
