import type { Rate } from './types';

/** Format a 0..1 rate as a percentage string, e.g. 0.9166666 -> "91.7%". */
export function formatPercent(value: number | null | undefined, digits = 1): string {
	if (value === null || value === undefined || Number.isNaN(value)) return '—';
	return `${(value * 100).toFixed(digits)}%`;
}

/** Format a CI as "[lo, hi]" using percent values, given two 0..1 bounds. */
export function formatCI(low: number | null, high: number | null, digits = 1): string {
	if (low === null || high === null) return suppressedCILabel();
	return `[${formatPercent(low, digits)}, ${formatPercent(high, digits)}]`;
}

/** The standard label shown in place of a CI whisker when the guardrail suppressed it. */
export function suppressedCILabel(n?: number): string {
	return n === undefined ? 'CI suppressed' : `CI suppressed (n=${n})`;
}

/** True when a Rate's confidence interval was suppressed by the small-n guardrail. */
export function isCISuppressed(rate: Pick<Rate, 'ci_low' | 'ci_high'>): boolean {
	return rate.ci_low === null || rate.ci_high === null;
}

/** Human label for a Rate's CI cell: numeric bounds, or the suppressed-CI state. */
export function formatRateCI(rate: Pick<Rate, 'ci_low' | 'ci_high' | 'denominator'>): string {
	if (isCISuppressed(rate)) return suppressedCILabel(rate.denominator);
	return formatCI(rate.ci_low, rate.ci_high);
}

/** "k / n" style display, falling back to the artifact's own `display` string if present. */
export function formatFraction(numerator: number, denominator: number): string {
	return `${numerator} / ${denominator}`;
}

export function formatMs(value: number | null | undefined): string {
	if (value === null || value === undefined || Number.isNaN(value)) return '—';
	return `${Math.round(value)} ms`;
}

export function formatUsd(value: number | null | undefined, digits = 6): string {
	if (value === null || value === undefined || Number.isNaN(value)) return '—';
	return `$${value.toFixed(digits)}`;
}

export function formatMicroUsd(value: number | null | undefined): string {
	if (value === null || value === undefined || Number.isNaN(value)) return '—';
	return `${Math.round(value)} µUSD`;
}

/** A short human method string for a Rate/Guardrail, e.g. "percentile bootstrap, B=10000, level=0.95, seed=1234". */
export function formatMethod(
	method: string,
	options: { resamples?: number; level?: number; seed?: number | null } = {}
): string {
	const parts = [method.replaceAll('_', ' ')];
	if (options.resamples !== undefined) parts.push(`B=${options.resamples}`);
	if (options.level !== undefined) parts.push(`level=${options.level}`);
	if (options.seed !== undefined && options.seed !== null) parts.push(`seed=${options.seed}`);
	return parts.join(', ');
}

export function titleCase(value: string): string {
	return value
		.split('_')
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(' ');
}
