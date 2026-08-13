import { base } from '$app/paths';
import indexArtifactJson from '../../static/data/index.json';
import type {
	CasesArtifact,
	FailuresArtifact,
	FamiliesArtifact,
	IndexArtifact,
	OverviewArtifact,
	ParetoArtifact,
	PricingArtifact,
	UncertaintyArtifact
} from './types';

/**
 * index.json is small and needed for navigation/entries generation everywhere
 * (including inside `entries()` functions, which run outside of `load` and have
 * no `fetch`), so it is statically imported rather than fetched.
 */
export const indexArtifact = indexArtifactJson as unknown as IndexArtifact;

export function profileIds(): string[] {
	return indexArtifact.profiles.map((p) => p.profile_id);
}

export function familyIds(): string[] {
	return indexArtifact.families;
}

export function caseIds(): string[] {
	return indexArtifact.case_ids;
}

export function isKnownProfile(profileId: string): boolean {
	return profileIds().includes(profileId);
}

/**
 * The larger per-run artifacts are loaded with the ambient `fetch` inside a
 * `load` function. During prerendering SvelteKit intercepts these fetches and
 * inlines the responses, so the final static build has no runtime dependency
 * on a server.
 */
async function loadJson<T>(fetchFn: typeof fetch, file: string): Promise<T> {
	const res = await fetchFn(`${base}/data/${file}`);
	if (!res.ok) {
		throw new Error(`Failed to load ${file}: ${res.status} ${res.statusText}`);
	}
	return (await res.json()) as T;
}

export const loadOverview = (fetchFn: typeof fetch) =>
	loadJson<OverviewArtifact>(fetchFn, 'overview.json');

export const loadFamilies = (fetchFn: typeof fetch) =>
	loadJson<FamiliesArtifact>(fetchFn, 'families.json');

export const loadUncertainty = (fetchFn: typeof fetch) =>
	loadJson<UncertaintyArtifact>(fetchFn, 'uncertainty.json');

export const loadCases = (fetchFn: typeof fetch) => loadJson<CasesArtifact>(fetchFn, 'cases.json');

export const loadFailures = (fetchFn: typeof fetch) =>
	loadJson<FailuresArtifact>(fetchFn, 'failures.json');

export const loadPareto = (fetchFn: typeof fetch) =>
	loadJson<ParetoArtifact>(fetchFn, 'pareto.json');

export const loadPricing = (fetchFn: typeof fetch) =>
	loadJson<PricingArtifact>(fetchFn, 'pricing.json');
