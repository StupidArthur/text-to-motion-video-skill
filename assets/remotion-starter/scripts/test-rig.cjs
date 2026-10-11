const test = require('node:test');
const assert = require('node:assert/strict');
const {solveIK, poseAt, toWorld, contactError, rootAt} = require('../.tmp-rig/rig.js');
const path = require('node:path');
const fs = require('node:fs');
const spec = JSON.parse(fs.readFileSync(path.join(__dirname,'..','video.json'),'utf8'));
const scene = spec.scenes.find(s=>s.interactions?.length);
const event = scene.interactions[0];

test('IK returns exact reachable endpoint',()=>{
  const ik=solveIK({x:0,y:0},{x:100,y:30},90,90);
  assert.ok(ik.reachable);
  assert.ok(Math.hypot(ik.end.x-100,ik.end.y-30)<.001);
  assert.ok(Math.abs(Math.hypot(ik.mid.x,ik.mid.y)-90)<.001);
});
test('unreachable IK clamps and reports',()=>{
  const ik=solveIK({x:0,y:0},{x:400,y:0},90,90);
  assert.equal(ik.reachable,false);
  assert.ok(ik.end.x < 180);
});
test('poses deterministic at random-accessed frames',()=>{
  const girl = scene.characters[0];
  const asset=spec.characterAssets.find(a=>a.id===girl.asset);
  const frames=[120,0,40,120,70,0];
  const results=frames.map(frame=>poseAt(girl,asset,frame,scene.interactions));
  assert.deepEqual(results[0],results[3]);
  assert.deepEqual(results[1],results[5]);
});
test('contact characters meet within 1 pixel',()=>{
  const error=contactError(scene.characters,spec.characterAssets,event);
  assert.ok(error<1,`contact error is ${error}`);
});
test('same character position stable within scene',()=>{
  const girl=scene.characters[0];
  assert.deepEqual(rootAt(girl,100),rootAt(girl,100));
});
