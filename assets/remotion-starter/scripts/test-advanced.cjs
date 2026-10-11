const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {rigFrameAt, rigAnchorAt, boneAngleAt, project, identity} = require('../.tmp-rig/rig-hierarchy.js');
const {propPlacementAt, characterAnchorAt} = require('../.tmp-rig/props.js');
const {poseAt, toWorld, footTargetAt, rootAt} = require('../.tmp-rig/rig.js');
const sceneDoc = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', '..', 'examples', 'custom-rig', 'video.json')));
const demo = require('../video.json');
const scene = sceneDoc.scenes[0], robot = scene.characters[0], asset=sceneDoc.characterAssets[0], star=scene.props[0];

test('custom rig hierarchical world transforms compose accurately',()=>{
  const frame=rigFrameAt(robot,asset,0);
  const head=frame.bones.head;
  assert.ok(Math.abs(head.matrix.e-800)<1e-6);
  assert.ok(Math.abs(head.matrix.f-510)<1e-6);
  assert.ok(Math.abs(rigAnchorAt(robot,asset,0,'forearm.grip').x-1029)<1e-6);
});
test('custom rig human-dog high-five has <1px contact at target frame',()=>{
  const ev=scene.interactions[0], f=ev.frame;
  const robotEnd=rigAnchorAt(robot,asset,f,'forearm.grip',scene.interactions);
  const dog=scene.characters[1]; const da=sceneDoc.characterAssets[1];
  const dogEnd=characterAnchorAt(dog,da,f,'paw',scene.interactions);
  assert.ok(Math.hypot(robotEnd.x-dogEnd.x,robotEnd.y-dogEnd.y)<1);
  assert.ok(Math.hypot(robotEnd.x-ev.target.x,robotEnd.y-ev.target.y)<1);
});
test('rig can be evaluated in any frame order and never mutates inputs',()=>{
  const original=JSON.stringify(robot);
  const samples=[170,0,100,12,170,100,0].map(f=>rigFrameAt(robot,asset,f,scene.interactions));
  assert.deepEqual(samples[0],samples[4]);
  assert.deepEqual(samples[2],samples[5]);
  assert.deepEqual(samples[1],samples[6]);
  assert.equal(JSON.stringify(robot),original);
});
test('joint action layers blend and are deterministic',()=>{
  const withAction={...robot,jointActions:[
    {name:'A',from:0,to:40,fadeFrames:1,joints:{tail:[{frame:0,angle:0},{frame:20,angle:40}]}},
    {name:'B',from:0,to:40,fadeFrames:1,strength:0.5,joints:{tail:[{frame:0,angle:0},{frame:20,angle:-40}]}}
  ]};
  assert.ok(Math.abs(boneAngleAt(withAction,'tail',20))<1e-6);
});
test('attachment tracks joint and deterministic release trajectory',()=>{
  for(const f of [135,142,155,170]){
    const prop=propPlacementAt(star,scene,sceneDoc.characterAssets,f);
    const grip=rigAnchorAt(robot,asset,f,'forearm.grip',scene.interactions);
    assert.ok(Math.hypot(prop.x-grip.x,prop.y-grip.y)<0.001);
  }
  const released=propPlacementAt(star,scene,sceneDoc.characterAssets,225);
  assert.deepEqual(released,{x:1280,y:560});
  assert.deepEqual(propPlacementAt(star,scene,sceneDoc.characterAssets,239),released);
});
test('moveTo and lookAt are pure, bounded behaviors',()=>{
  const withMove={...robot,behaviors:[{type:'moveTo',from:0,to:40,target:{x:900,y:780}}]};
  assert.deepEqual(rootAt(withMove,40),{...rootAt(robot,40),x:900,y:780});
  assert.deepEqual(rootAt(withMove,40),rootAt(withMove,40));
  assert.ok(Math.abs(rigFrameAt(robot,asset,100).bones.head.angle)<=24);
});
test('planted running feet stay fixed during stance frames',()=>{
  const run=demo.scenes.find(s=>s.id==='running');
  const dog=run.characters.find(c=>c.asset==='puppy');
  const da=demo.characterAssets.find(a=>a.id==='puppy');
  const x=[];
  for(let f=45;f<=52;f++){
    const pose=poseAt(dog,da,f,run.interactions??[]);
    const end=toWorld(pose.frontLeg.end,pose.root);
    x.push(end);
  }
  for(const item of x)assert.ok(Math.hypot(item.x-x[0].x,item.y-x[0].y)<0.005);
});
