import { describe, expect, it } from 'vitest';
import { caseIds, familyIds, indexArtifact, profileIds } from './data';

describe('static routing index', () => {
	it('contains the two fixture profiles and all route dimensions', () => {
		expect(profileIds()).toHaveLength(2);
		expect(familyIds()).toHaveLength(4);
		expect(caseIds()).toHaveLength(24);
		expect(indexArtifact.simulated).toBe(true);
	});

	it('declares exactly the eight redacted export artifacts', () => {
		expect(['index.json', ...Object.keys(indexArtifact.artifacts)].sort()).toEqual([
			'cases.json',
			'failures.json',
			'families.json',
			'index.json',
			'overview.json',
			'pareto.json',
			'pricing.json',
			'uncertainty.json'
		]);
	});
});
