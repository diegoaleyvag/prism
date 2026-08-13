import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import ChartFrame from './ChartFrame.svelte';

// A minimal snippet-shaped children prop. ChartFrame's own guard clauses run
// before the template ever calls {@render children()}, so this only needs to
// exist to satisfy the component's prop shape for the "should not throw" case.
function noopChildren() {
	return { update() {}, destroy() {} };
}

describe('ChartFrame', () => {
	it('throws when title is missing', () => {
		expect(() =>
			render(ChartFrame, {
				props: { title: '', denominator: 10, method: 'percentile_bootstrap', units: '%', caption: 'c' } as any
			})
		).toThrow(/title/i);
	});

	it('throws when denominator is missing', () => {
		expect(() =>
			render(ChartFrame, {
				props: { title: 't', method: 'percentile_bootstrap', units: '%', caption: 'c' } as any
			})
		).toThrow(/denominator/i);
	});

	it('throws when method is missing', () => {
		expect(() =>
			render(ChartFrame, {
				props: { title: 't', denominator: 10, method: '', units: '%', caption: 'c' } as any
			})
		).toThrow(/method/i);
	});

	it('does not throw when all required props are present', () => {
		expect(() =>
			render(ChartFrame, {
				props: {
					title: 't',
					denominator: 10,
					method: 'percentile_bootstrap',
					units: '%',
					caption: 'c',
					children: noopChildren
				} as any
			})
		).not.toThrow();
	});
});
