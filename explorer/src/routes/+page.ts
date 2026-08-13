import { profileIds } from '$lib/data';
import type { PageLoad } from './$types';

export const prerender = true;

// This lands through the normal root +layout.svelte (so the SimBanner and
// footer disclaimer render here too) and redirects to the first profile's
// overview both via a real <a> (crawlable, no-JS friendly) and a client-side
// redirect once hydrated — see +page.svelte.
export const load: PageLoad = () => {
	const [firstProfile] = profileIds();
	return { firstProfile };
};
