import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const skillRoot=path.resolve(root,'..','..');
const demos={custom:'examples/custom-rig/video.json',v1:'examples/v1-video.json',v2:'examples/character-interaction/video.json',scripted:'examples/scripted-cottage/storyboard.json'};
const key=process.argv[2];
if(!demos[key]){console.error(`Usage: node scripts/switch-demo.mjs ${Object.keys(demos).join('|')}`);process.exit(1);}
const src=path.join(skillRoot,demos[key]);
if(!fs.existsSync(src)){console.error(`Missing ${src}`);process.exit(1);}
if(key==='scripted'){
 const python=process.platform==='win32'?'python':'python3';
 const result=spawnSync(python,[path.join(skillRoot,'scripts/production_pipeline.py'),path.join(skillRoot,'examples/scripted-cottage'),'--output',path.join(root,'video.json'),'--copy-assets'],{stdio:'inherit'});
 if(result.error||result.status!==0)process.exit(result.status||1);
}else{
 fs.copyFileSync(src,path.join(root,'video.json'));
}
if(key==='custom'){
 const asset=path.join(skillRoot,'examples/custom-rig/public/robot-face.svg');
 fs.copyFileSync(asset,path.join(root,'public/robot-face.svg'));
}
console.log(`Loaded ${key} demo. Run npm run storyboard and npm run render.`);
