#!/usr/bin/env node
// Prebuild step: copy the exact redacted artifact set produced by `prism export`.
// Static data is generated, never a committed fallback: a clean build must fail
// rather than silently display stale evaluation evidence.
import { existsSync, mkdirSync, readdirSync, copyFileSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const explorerRoot = join(__dirname, '..');
const artifactsDir = join(explorerRoot, '..', 'artifacts');
const targetDir = join(explorerRoot, 'static', 'data');
const REQUIRED_ARTIFACTS = [
	'index.json',
	'overview.json',
	'families.json',
	'uncertainty.json',
	'cases.json',
	'failures.json',
	'pareto.json',
	'pricing.json'
];

function main() {
	if (!existsSync(artifactsDir)) {
		throw new Error('[copy-artifacts] ../artifacts not found. Run the root reproducible build first.');
	}

	const jsonFiles = readdirSync(artifactsDir).filter((name) => name.endsWith('.json'));
	const missing = REQUIRED_ARTIFACTS.filter((name) => !jsonFiles.includes(name));
	const unexpected = jsonFiles.filter((name) => !REQUIRED_ARTIFACTS.includes(name));
	if (missing.length || unexpected.length) {
		throw new Error(
			`[copy-artifacts] expected exactly eight artifact files; missing: ${missing.join(', ') || 'none'}; unexpected: ${unexpected.join(', ') || 'none'}.`
		);
	}

	rmSync(targetDir, { recursive: true, force: true });
	mkdirSync(targetDir, { recursive: true });

	for (const file of REQUIRED_ARTIFACTS) {
		copyFileSync(join(artifactsDir, file), join(targetDir, file));
		console.log(`[copy-artifacts] copied ${file} -> static/data/${file}`);
	}
}

main();
