import { error } from '@sveltejs/kit';
import { isKnownProfile, loadFailures, profileIds } from '$lib/data';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => profileIds().map((profile) => ({ profile }));

export const load: PageLoad = async ({ params, fetch }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}

	const failures = await loadFailures(fetch);
	const rows = failures.rows
		.filter((row) => row.profile_id === params.profile)
		.sort((a, b) => a.case_id.localeCompare(b.case_id));

	return {
		profileId: params.profile,
		rows
	};
};
