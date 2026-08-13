import { error } from '@sveltejs/kit';
import { familyIds, isKnownProfile, loadCases, loadFamilies, profileIds } from '$lib/data';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => {
	const profiles = profileIds();
	const families = familyIds();
	return profiles.flatMap((profile) => families.map((family) => ({ profile, family })));
};

export const load: PageLoad = async ({ params, fetch }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}
	if (!familyIds().includes(params.family)) {
		error(404, `Unknown family "${params.family}"`);
	}

	const [families, cases] = await Promise.all([loadFamilies(fetch), loadCases(fetch)]);

	const profileFamilies =
		families.profiles.find((p) => p.profile_id === params.profile)?.families ?? [];
	const familyMetrics = profileFamilies.find((f) => f.family === params.family);
	if (!familyMetrics) {
		error(404, `No metrics for family "${params.family}" / profile "${params.profile}"`);
	}

	const familyCases = cases.rows
		.filter((row) => row.profile_id === params.profile && row.family === params.family)
		.sort((a, b) => a.case_id.localeCompare(b.case_id));

	return {
		profileId: params.profile,
		family: params.family,
		familyMetrics,
		familyCases
	};
};
