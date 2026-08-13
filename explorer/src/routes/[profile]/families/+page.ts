import { error } from '@sveltejs/kit';
import { isKnownProfile, loadFamilies, profileIds } from '$lib/data';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => profileIds().map((profile) => ({ profile }));

export const load: PageLoad = async ({ params, fetch }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}

	const families = await loadFamilies(fetch);
	const profileFamilies =
		families.profiles.find((p) => p.profile_id === params.profile)?.families ?? [];

	return {
		profileId: params.profile,
		families: profileFamilies
	};
};
