import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const spec = JSON.parse(fs.readFileSync(path.join(projectRoot, 'video.json'), 'utf8'));
const outDir = path.join(projectRoot, 'out', 'storyboard');
fs.mkdirSync(outDir, {recursive: true});

let start = 0;
const saved = [];
for (const scene of spec.scenes) {
  const last = Math.max(0, scene.durationFrames - 1);
  const candidates = [0, Math.floor(last / 2), last];
  const uniqueFrames = [...new Set(candidates)];
  for (const relativeFrame of uniqueFrames) {
    const globalFrame = start + relativeFrame;
    const safeSceneID = String(scene.id).replace(/[^a-zA-Z0-9_-]/g, '-');
    const filename = `${String(globalFrame).padStart(6, '0')}-${safeSceneID}.png`;
    const target = path.join(outDir, filename);
    const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx';
    const args = ['--no-install', 'remotion', 'still', 'src/index.ts', 'Main', target, `--frame=${globalFrame}`];
    const result = spawnSync(npx, args, {cwd: projectRoot, stdio: 'inherit'});
    if (result.error || result.status !== 0) {
      console.error(`Failed at global frame ${globalFrame}:`, result.error?.message ?? `status ${result.status}`);
      process.exit(result.status || 1);
    }
    saved.push(path.relative(projectRoot, target));
  }
  start += scene.durationFrames;
}
console.log(`\nSaved ${saved.length} storyboard frames:`);
for (const filename of saved) console.log('  ' + filename);
