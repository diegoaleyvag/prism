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

	it('renders the fallback table with its caption and row content in the accessibility tree', () => {
		const { container, getByText } = render(ChartFrame, {
			props: {
				title: 'Task success by family',
				denominator: 24,
				method: 'percentile_bootstrap',
				units: '%',
				caption: 'c',
				rows: [
					{ label: 'reasoning', value: '83% (20/24)' },
					{ label: 'retrieval', value: '91% (22/24)' }
				],
				children: noopChildren
			} as any
		});

		const table = container.querySelector('table.chart-frame__fallback');
		expect(table).not.toBeNull();

		// The caption must be a real <caption> element (part of the table's
		// accessible structure), not a decorative label.
		const caption = table!.querySelector('caption');
		expect(caption?.textContent).toContain('Task success by family');
		expect(caption?.textContent).toContain('underlying data (%)');

		// Row data must be present as real table cells, queryable by text —
		// i.e. actually in the DOM/accessibility tree, not stripped out.
		expect(getByText('reasoning')).toBeInTheDocument();
		expect(getByText('83% (20/24)')).toBeInTheDocument();
		expect(getByText('retrieval')).toBeInTheDocument();
		expect(getByText('91% (22/24)')).toBeInTheDocument();
	});

	it('never sets aria-hidden, display:none, or visibility:hidden on the fallback table or its wrapper', () => {
		const { container } = render(ChartFrame, {
			props: {
				title: 't',
				denominator: 10,
				method: 'percentile_bootstrap',
				units: '%',
				caption: 'c',
				rows: [{ label: 'x', value: '1' }],
				children: noopChildren
			} as any
		});

		const table = container.querySelector('table.chart-frame__fallback');
		expect(table).not.toBeNull();

		// Walk from the table up to the figure, asserting none of the
		// ancestors (nor the table itself) remove it from the accessibility
		// tree via aria-hidden, or hide it visually via inline styles that
		// jsdom *does* record (attribute presence, not computed layout).
		let node: Element | null = table;
		while (node) {
			expect(node.getAttribute('aria-hidden')).not.toBe('true');
			expect(node.getAttribute('style') ?? '').not.toMatch(/display:\s*none/i);
			expect(node.getAttribute('style') ?? '').not.toMatch(/visibility:\s*hidden/i);
			node = node.parentElement;
		}
	});

	it('places the fallback table inside a dedicated sr-only clipping wrapper, not directly sr-only itself', () => {
		// The bug this guards against: putting `sr-only` (position: absolute)
		// directly on the <table> makes the *table* the absolutely-positioned
		// box. Wrapping it in a dedicated element keeps the table a normal,
		// unpositioned participant in the accessibility tree while only the
		// wrapper is clipped/hidden visually.
		const { container } = render(ChartFrame, {
			props: {
				title: 't',
				denominator: 10,
				method: 'percentile_bootstrap',
				units: '%',
				caption: 'c',
				rows: [{ label: 'x', value: '1' }],
				children: noopChildren
			} as any
		});

		const table = container.querySelector('table.chart-frame__fallback');
		expect(table).not.toBeNull();
		expect(table!.classList.contains('sr-only')).toBe(false);

		const wrapper = table!.parentElement;
		expect(wrapper).not.toBeNull();
		expect(wrapper!.classList.contains('sr-only')).toBe(true);
	});

	it('renders no rows without throwing and keeps the table/caption structure intact', () => {
		const { container } = render(ChartFrame, {
			props: {
				title: 't',
				denominator: 0,
				method: 'percentile_bootstrap',
				units: '%',
				caption: 'c',
				children: noopChildren
			} as any
		});

		const table = container.querySelector('table.chart-frame__fallback');
		expect(table).not.toBeNull();
		expect(table!.querySelector('caption')).not.toBeNull();
		expect(table!.querySelectorAll('tbody tr')).toHaveLength(0);
	});
});
