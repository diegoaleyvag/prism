import { error } from '@sveltejs/kit';
import { isKnownProfile } from '$lib/data';
import type { LayoutLoad } from './$types';

export const prerender = true;

// `entries` is only a valid export from +page.(server.)ts / +server.ts, not
// +layout.ts, so every leaf +page.ts under [profile]/ declares its own
// entries (see overview/, families/, failures/, uncertainty/, pareto/).

export const load: LayoutLoad = ({ params }) => {
	if (!isKnownProfile(params.profile)) {
		error(404, `Unknown profile "${params.profile}"`);
	}
	return { profileId: params.profile };
};
