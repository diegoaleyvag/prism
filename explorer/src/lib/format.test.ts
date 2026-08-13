import { describe, expect, it } from 'vitest';
import {
	formatCI,
	formatFraction,
	formatPercent,
	formatRateCI,
	isCISuppressed,
	suppressedCILabel
} from './format';

describe('formatPercent', () => {
	it('formats a fraction as a percentage with one decimal by default', () => {
		expect(formatPercent(0.9166666666666666)).toBe('91.7%');
	});

	it('returns an em dash for null/undefined', () => {
		expect(formatPercent(null)).toBe('—');
		expect(formatPercent(undefined)).toBe('—');
	});

	it('respects the digits argument', () => {
		expect(formatPercent(0.625, 0)).toBe('63%');
	});
});

describe('formatCI', () => {
	it('formats a "[lo, hi]" style interval', () => {
		expect(formatCI(0.7916666666666666, 1.0)).toBe('[79.2%, 100.0%]');
	});

	it('falls back to the suppressed label when either bound is null', () => {
		expect(formatCI(null, 1.0)).toBe(suppressedCILabel());
		expect(formatCI(0.5, null)).toBe(suppressedCILabel());
	});
});

describe('suppressedCILabel', () => {
	it('is a stable, clear phrase with no n', () => {
		expect(suppressedCILabel()).toBe('CI suppressed');
	});

	it('includes n when provided', () => {
		expect(suppressedCILabel(6)).toBe('CI suppressed (n=6)');
	});
});

describe('isCISuppressed / formatRateCI', () => {
	const suppressedRate = { ci_low: null, ci_high: null, denominator: 6 };
	const reliableRate = { ci_low: 0.79, ci_high: 1.0, denominator: 24 };

	it('detects suppressed CIs', () => {
		expect(isCISuppressed(suppressedRate)).toBe(true);
		expect(isCISuppressed(reliableRate)).toBe(false);
	});

	it('shows the suppressed-CI label with denominator instead of a fake interval', () => {
		expect(formatRateCI(suppressedRate)).toBe('CI suppressed (n=6)');
	});

	it('shows numeric bounds when the CI is reliable', () => {
		expect(formatRateCI(reliableRate)).toBe('[79.0%, 100.0%]');
	});
});

describe('formatFraction', () => {
	it('renders "k / n"', () => {
		expect(formatFraction(22, 24)).toBe('22 / 24');
	});
});
