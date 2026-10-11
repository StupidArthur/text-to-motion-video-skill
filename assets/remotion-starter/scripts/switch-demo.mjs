import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const skillRoot=path.resolve(root,'..','..');
const demos={custom:'examples/custom-rig/video.json',v1:'examples/v1-video.json',v2:'examples/character-interaction/video.json'};
const key=process.argv[2];
if(!demos[key]){console.error(`Usage: node scripts/switch-demo.mjs ${Object.keys(demos).join('|')}`);process.exit(1);}
const src=path.join(skillRoot,demos[key]);
if(!fs.existsSync(src)){console.error(`Missing ${src}`);process.exit(1);}
fs.copyFileSync(src,path.join(root,'video.json'));
if(key==='custom'){
 const asset=path.join(skillRoot,'examples/custom-rig/public/robot-face.svg');
 fs.copyFileSync(asset,path.join(root,'public/robot-face.svg'));
}
console.log(`Loaded ${key} demo. Run npm run storyboard and npm run render.`);
