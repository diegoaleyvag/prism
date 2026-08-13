#!/usr/bin/env node
// Guardrail: Prism must never surface a named model/provider anywhere in the
// built site or in the fixture data it ships. Run after `pnpm build`:
//
//   pnpm run check:names
//
// Scans build/**/*.html and static/data/**/*.json for a denylist of model /
// provider names (matched as whole or hyphen-delimited tokens, case
// insensitive) and exits non-zero on any hit. Also asserts that every built
// HTML page contains the string "SIMULATED", since the SimBanner is supposed
// to render on every prerendered page.
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const explorerRoot = join(__dirname, '..');
const buildDir = join(explorerRoot, 'build');
const dataDir = join(explorerRoot, 'static', 'data');

const DENYLIST = [
	'openai',
	'gpt',
	'chatgpt',
	'anthropic',
	'claude',
	'sonnet',
	'opus',
	'haiku',
	'gemini',
	'bard',
	'palm',
	'llama',
	'mistral',
	'mixtral',
	'cohere',
	'grok',
	'deepseek',
	'qwen'
];

// \b already treats hyphens as boundaries (they are non-word characters), so
// this matches whole tokens and hyphenated compounds like "gpt-4" or
// "claude-3" without matching inside unrelated words (e.g. "campus").
const DENY_PATTERN = new RegExp(`\\b(${DENYLIST.join('|')})\\b`, 'i');

/** @returns {string[]} absolute file paths */
function listFilesRecursive(root, predicate) {
	if (!existsSync(root)) return [];
	return readdirSync(root, { recursive: true })
		.map((entry) => join(root, entry))
		.filter((full) => {
			try {
				return statSync(full).isFile() && predicate(full);
			} catch {
				return false;
			}
		});
}

function main() {
	if (!existsSync(buildDir)) {
		console.error(`[check:names] Build directory not found at ${buildDir}. Run "pnpm build" first.`);
		process.exit(1);
	}

	const htmlFiles = listFilesRecursive(buildDir, (f) => f.endsWith('.html'));
	const jsonFiles = listFilesRecursive(dataDir, (f) => f.endsWith('.json'));

	if (htmlFiles.length === 0) {
		console.error(`[check:names] No .html files found under ${buildDir} — did the build succeed?`);
		process.exit(1);
	}

	let violations = 0;
	let missingSimulated = 0;

	for (const file of [...htmlFiles, ...jsonFiles]) {
		const contents = readFileSync(file, 'utf8');
		const match = contents.match(DENY_PATTERN);
		if (match) {
			violations += 1;
			console.error(
				`[check:names] DENYLIST HIT: "${match[0]}" found in ${relative(explorerRoot, file)}`
			);
		}
	}

	for (const file of htmlFiles) {
		const contents = readFileSync(file, 'utf8');
		if (!contents.includes('SIMULATED')) {
			missingSimulated += 1;
			console.error(`[check:names] MISSING "SIMULATED": ${relative(explorerRoot, file)}`);
		}
	}

	console.log(
		`[check:names] scanned ${htmlFiles.length} html file(s) and ${jsonFiles.length} json file(s).`
	);

	if (violations > 0 || missingSimulated > 0) {
		console.error(
			`[check:names] FAILED — ${violations} denylist hit(s), ${missingSimulated} page(s) missing "SIMULATED".`
		);
		process.exit(1);
	}

	console.log('[check:names] OK — no denylisted model/provider names, "SIMULATED" present on every page.');
}

main();
