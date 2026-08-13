#!/usr/bin/env node
// Prebuild step: refresh static/data/*.json from ../artifacts if that directory
// exists (i.e. the Python backend has regenerated fresher fixtures). This is a
// no-op-safe copy — if ../artifacts is absent (or empty), the already-committed
// files under static/data/ are left untouched and the build proceeds normally.
import { existsSync, mkdirSync, readdirSync, copyFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const explorerRoot = join(__dirname, '..');
const artifactsDir = join(explorerRoot, '..', 'artifacts');
const targetDir = join(explorerRoot, 'static', 'data');

function main() {
	if (!existsSync(artifactsDir)) {
		console.log('[copy-artifacts] ../artifacts not found — skipping (static/data/ left as-is).');
		return;
	}

	const jsonFiles = readdirSync(artifactsDir).filter((name) => name.endsWith('.json'));
	if (jsonFiles.length === 0) {
		console.log('[copy-artifacts] ../artifacts exists but has no .json files — skipping.');
		return;
	}

	mkdirSync(targetDir, { recursive: true });

	for (const file of jsonFiles) {
		copyFileSync(join(artifactsDir, file), join(targetDir, file));
		console.log(`[copy-artifacts] copied ${file} -> static/data/${file}`);
	}
}

main();
