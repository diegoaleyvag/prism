#!/usr/bin/env node
/**
 * Rebuild the redacted Prism explorer from a clean generated-data state.
 * This script is intentionally the one supported bridge between the offline
 * fixture pipeline and SvelteKit's static build.
 */
import { existsSync, readdirSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url));
const generated = ['explorer/static/data', 'explorer/build'];
const artifactsDir = join(root, 'artifacts');
const requiredArtifacts = [
	'index.json',
	'overview.json',
	'families.json',
	'uncertainty.json',
	'cases.json',
	'failures.json',
	'pareto.json',
	'pricing.json'
];

function run(command, args, cwd = root) {
	const result = spawnSync(command, args, { cwd, stdio: 'inherit' });
	if (result.status !== 0) process.exit(result.status ?? 1);
}

for (const path of generated) rmSync(join(root, path), { recursive: true, force: true });
for (const directory of ['runs', 'artifacts']) {
	const absolute = join(root, directory);
	if (!existsSync(absolute)) continue;
	for (const entry of readdirSync(absolute)) {
		if (entry !== '.gitkeep') rmSync(join(absolute, entry), { recursive: true, force: true });
	}
}

run('uv', ['run', 'prism', 'validate', 'manifests/example.manifest.json']);
run('uv', ['run', 'prism', 'run', 'manifests/example.manifest.json', '--out', 'runs']);
run('uv', ['run', 'prism', 'verify', 'runs']);
run('uv', ['run', 'prism', 'metrics', 'manifests/example.manifest.json', '--runs', 'runs']);
run('uv', ['run', 'prism', 'export', 'manifests/example.manifest.json', '--runs', 'runs', '--out', 'artifacts']);

const artifactFiles = existsSync(artifactsDir)
	? readdirSync(artifactsDir).filter((name) => name.endsWith('.json')).sort()
	: [];
if (artifactFiles.join('\n') !== [...requiredArtifacts].sort().join('\n')) {
	console.error(`[build-explorer] expected exactly eight exports; found: ${artifactFiles.join(', ') || 'none'}`);
	process.exit(1);
}

run('pnpm', ['run', 'build'], join(root, 'explorer'));
