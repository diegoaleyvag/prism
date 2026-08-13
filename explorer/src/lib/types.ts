// Types modeled precisely on the redacted artifact JSON in static/data/*.json.
// Every artifact carries these common envelope fields.
export interface ArtifactEnvelope {
	artifact: string;
	schema_version: string;
	simulated: true;
	disclaimer: string;
	generated_at: string;
}

export type ProfileId = string;
export type FamilyId = string;

/** A single profile's identity + content digest, as listed in index.json / overview.json. */
export interface ProfileRef {
	profile_id: ProfileId;
	profile_digest: string;
}

export interface RunInfo {
	manifest_id: string;
	manifest_digest: string;
	record_set_hash: string;
	prism_version: string;
	review_scope: string;
}

export interface ArtifactRef {
	file: string;
	content_hash: string;
}

export interface IndexArtifact extends ArtifactEnvelope {
	artifact: 'index';
	run: RunInfo;
	profiles: ProfileRef[];
	families: FamilyId[];
	case_ids: string[];
	artifacts: Record<string, ArtifactRef>;
}

/** Bootstrap / guardrail configuration shared across overview + uncertainty artifacts. */
export interface Guardrail {
	n_hard: number;
	n_stable: number;
	method: string;
	resamples: number;
	level: number;
}

export interface RuleOfThree {
	kind_lower?: number;
	kind_upper?: number;
}

/**
 * A single rate-style metric (task_success, schema_validity, correct_escalation, over_refusal).
 * ci_low / ci_high are frequently null — the guardrail suppresses the interval for small n or
 * degenerate (0% / 100%) proportions. The UI must treat a null CI as "suppressed", not as zero
 * width, and must always show the denominator + ci_flags alongside the point estimate.
 */
export interface Rate {
	metric_id: string;
	scope: 'aggregate' | 'family';
	profile_id: ProfileId;
	family: FamilyId | null;
	numerator: number;
	denominator: number;
	rate: number | null;
	display: string;
	ci_low: number | null;
	ci_high: number | null;
	ci_reliable: boolean | null;
	ci_flags: string[];
	method: string;
	seed: number | null;
	rule_of_three: RuleOfThree;
	denominator_record_ids: string[];
	passed_record_ids: string[];
}

export interface LatencyStats {
	n: number;
	p50_ms: number;
	p90_ms: number;
	p95_ms: number;
	p99_ms: number;
	min_ms: number;
	max_ms: number;
	mean_ms: number;
}

export interface TokenStats {
	n: number;
	input_mean: number;
	input_sum: number;
	output_mean: number;
	output_sum: number;
	total_sum: number;
}

export interface CostStats {
	n: number;
	total_micro_usd: number;
	mean_micro_usd: number;
	total_usd: number;
	mean_usd: number;
	price_table_id: string;
	price_table_hash: string;
	simulated: true;
}

/** Aggregate- or family-scoped metrics bundle. */
export interface GroupMetrics {
	scope: 'aggregate' | 'family';
	profile_id: ProfileId;
	family: FamilyId | null;
	n: number;
	task_success: Rate;
	schema_validity: Rate;
	correct_escalation: Rate | null;
	over_refusal: Rate | null;
	latency: LatencyStats;
	tokens: TokenStats;
	cost: CostStats;
	member_record_ids: string[];
	passed_record_ids: string[];
}

export interface OverviewProfileEntry {
	profile_id: ProfileId;
	profile_digest: string;
	aggregate: GroupMetrics;
}

export interface OverviewArtifact extends ArtifactEnvelope {
	artifact: 'overview';
	review_scope: string;
	excluded_count: number;
	guardrail: Guardrail;
	price_table_id: string;
	record_set_hash: string;
	profiles: OverviewProfileEntry[];
}

export interface FamiliesProfileEntry {
	profile_id: ProfileId;
	families: GroupMetrics[];
}

export interface FamiliesArtifact extends ArtifactEnvelope {
	artifact: 'families';
	profiles: FamiliesProfileEntry[];
}

export interface UncertaintyArtifact extends ArtifactEnvelope {
	artifact: 'uncertainty';
	guardrail: Guardrail;
	metrics: Rate[];
}

export type BehaviorClass = 'normal' | 'should_abstain' | 'should_escalate' | 'should_refuse';
export type FailedMetric = 'task_success' | 'schema_valid' | 'abstention' | 'over_refusal' | null;

export interface CaseRow {
	record_id: string;
	case_id: string;
	family: FamilyId;
	profile_id: ProfileId;
	behavior_class: BehaviorClass;
	review_label: string;
	schema_valid: boolean;
	task_success: boolean;
	abstention_correct: boolean | null;
	failed_metric: FailedMetric;
	reason: string;
	latency_ms: number;
	input_tokens: number;
	output_tokens: number;
	total_tokens: number;
	cost_micro_usd: number;
	cost_usd: number;
	input_excerpt: string;
	expected_summary: string;
	output_summary: string;
}

export interface CasesArtifact extends ArtifactEnvelope {
	artifact: 'cases';
	rows: CaseRow[];
}

export interface FailuresArtifact extends ArtifactEnvelope {
	artifact: 'failures';
	rows: CaseRow[];
}

export interface ParetoAxes {
	quality: string;
	cost_usd: string;
	latency_p90_ms: string;
}

export interface ParetoPoint {
	profile_id: ProfileId;
	quality: number;
	cost_usd: number;
	latency_p90_ms: number;
	on_frontier: boolean;
	dominated_by: ProfileId[];
}

export interface ParetoArtifact extends ArtifactEnvelope {
	artifact: 'pareto';
	axes: ParetoAxes;
	points: ParetoPoint[];
}

export interface PriceTableEntry {
	unit: string;
	input_price: string;
	output_price: string;
	notes: string;
}

export interface PriceTable {
	price_table_id: string;
	schema_version: string;
	currency: string;
	simulated: true;
	disclaimer: string;
	effective_date: string;
	entries: Record<ProfileId, PriceTableEntry>;
	content_hash: string;
}

export interface PricingArtifact extends ArtifactEnvelope {
	artifact: 'pricing';
	price_table: PriceTable;
}

/** The "mode" this build was produced under. Only `fixture` is available in this release. */
export type ExplorerMode = 'fixture' | 'replay' | 'live';
