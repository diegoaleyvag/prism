import { error } from '@sveltejs/kit';
import { caseIds, isKnownProfile, loadCases, profileIds } from '$lib/data';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => {
	const profiles = profileIds();
	const cases = caseIds();
	return profiles.flatMap((profile) => cases.map((c) => ({ profile, case: c })));
};

export const load: PageLoad = async ({ params, fetch }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}
	if (!caseIds().includes(params.case)) {
		error(404, `Unknown case "${params.case}"`);
	}

	const cases = await loadCases(fetch);
	const row = cases.rows.find((r) => r.profile_id === params.profile && r.case_id === params.case);
	if (!row) {
		error(404, `No case "${params.case}" for profile "${params.profile}"`);
	}

	return {
		profileId: params.profile,
		caseId: params.case,
		row
	};
};
