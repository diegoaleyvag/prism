import { error } from '@sveltejs/kit';
import { isKnownProfile, loadFamilies, loadOverview, profileIds } from '$lib/data';
import type { EntryGenerator, PageLoad } from './$types';

export const prerender = true;

export const entries: EntryGenerator = () => profileIds().map((profile) => ({ profile }));

export const load: PageLoad = async ({ params, fetch }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}

	const [overview, families] = await Promise.all([loadOverview(fetch), loadFamilies(fetch)]);

	const profileOverview = overview.profiles.find((p) => p.profile_id === params.profile);
	if (!profileOverview) {
		error(404, `No overview entry for profile "${params.profile}"`);
	}

	const profileFamilies =
		families.profiles.find((p) => p.profile_id === params.profile)?.families ?? [];

	return {
		profileId: params.profile,
		guardrail: overview.guardrail,
		reviewScope: overview.review_scope,
		excludedCount: overview.excluded_count,
		priceTableId: overview.price_table_id,
		recordSetHash: overview.record_set_hash,
		aggregate: profileOverview.aggregate,
		profileDigest: profileOverview.profile_digest,
		families: profileFamilies
	};
};
