import type {CharacterDefinition, CharacterInstance, JointAction, Point, RigBone} from './types';
import {clamp, mix, rootAt, smooth, solveIK, contactWeight, type RootPose} from './rig';
import type {HighFive} from './types';

export type Matrix = {a:number; b:number; c:number; d:number; e:number; f:number};
export const identity = ():Matrix => ({a:1,b:0,c:0,d:1,e:0,f:0});
export const mul = (p:Matrix,q:Matrix):Matrix=>({
 a:p.a*q.a+p.c*q.b, b:p.b*q.a+p.d*q.b,
 c:p.a*q.c+p.c*q.d, d:p.b*q.c+p.d*q.d,
 e:p.a*q.e+p.c*q.f+p.e, f:p.b*q.e+p.d*q.f+p.f,
});
export const translate=(x:number,y:number):Matrix=>({...identity(),e:x,f:y});
export const rotate=(angle:number):Matrix=>{const a=angle*Math.PI/180;return {a:Math.cos(a),b:Math.sin(a),c:-Math.sin(a),d:Math.cos(a),e:0,f:0};};
export const scale=(x:number,y:number):Matrix=>({a:x,b:0,c:0,d:y,e:0,f:0});
export const project=(m:Matrix,p:Point):Point=>({x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f});
const easeWindow=(f:number,from:number,to:number,fade:number)=>
 smooth(Math.min(1,(f-from)/Math.max(1,fade),(to-f)/Math.max(1,fade)));
export const interpolateKeys=(keys:{frame:number;angle:number}[], frame:number):number=>{
 if(!keys.length)return 0;
 if(frame<=keys[0].frame)return keys[0].angle;
 for(let i=1;i<keys.length;i++)if(frame<=keys[i].frame){
  const a=keys[i-1],b=keys[i],t=smooth((frame-a.frame)/(b.frame-a.frame));
  return mix(a.angle,b.angle,t);
 }
 return keys[keys.length-1].angle;
};
/** Blends joint action layers in order, each in their own action-local time. */
export const boneAngleAt=(ch:CharacterInstance, boneId:string, frame:number):number=>{
 let angle=0;
 for(const action of ch.jointActions??[]){
  const keys=action.joints[boneId];
  if(!keys || frame<action.from || frame>action.to)continue;
  const weight=clamp((action.strength??1)*easeWindow(frame,action.from,action.to,action.fadeFrames??8));
  angle=mix(angle,interpolateKeys(keys,frame-action.from),weight);
 }
 return angle;
};
export type RigFrame = {root:RootPose; bones:Record<string,{matrix:Matrix;angle:number;bone:RigBone}>};
export const rigFrameAt=(ch:CharacterInstance,asset:CharacterDefinition,frame:number,events:HighFive[]=[]):RigFrame=>{
 const rig=asset.rig;
 if(!rig)throw Error(`Asset ${asset.id} has no rig`);
 const root=rootAt(ch,frame);
 const rootM=mul(translate(root.x,root.y),scale(root.scale*root.facing,root.scale));
 const bones:RigFrame['bones']={};
 const ikOverrides:Record<string,number>={};
 const pending=new Map(rig.bones.map(b=>[b.id,b]));
 const visit=(id:string,stack:string[]=[]):Matrix=>{
  if(bones[id])return bones[id].matrix;
  if(stack.includes(id))throw Error(`Rig cycle: ${[...stack,id].join(' -> ')}`);
  const bone=pending.get(id);
  if(!bone)throw Error(`Unknown bone ${id}`);
  let angle=ikOverrides[id]??boneAngleAt(ch,id,frame);
  if(id==='head')for(const b of ch.behaviors??[])if(b.type==='lookAt'&&frame>=b.from&&frame<=b.to){
   const aim=Math.atan2(b.target.y-root.y,b.target.x-root.x)*180/Math.PI;
   angle+=clamp((aim-(root.facing===1?0:180))/4,-24,24)*(b.strength??1)*easeWindow(frame,b.from,b.to,8);
  }
  const parent=bone.parent?visit(bone.parent,[...stack,id]):rootM;
  const matrix=mul(parent,mul(translate(bone.pivot.x,bone.pivot.y),rotate(angle)));
  bones[id]={matrix,angle,bone};return matrix;
 };
 // Solve arbitrary declared two-link chains in their parent's local coordinate space.
 // This composes correctly with translated, scaled and horizontally flipped roots.
 for(const chain of rig.ikChains??[]){
  let target:Point|undefined,weight=0;
  for(const event of events)if(event.actors.includes(ch.id)){
   const w=contactWeight(event,frame);
   if(w>weight){target=event.target;weight=w;}
  }
  for(const behavior of ch.behaviors??[])if(behavior.type==='reachTo'&&frame>=behavior.from&&frame<=behavior.to){
   const w=(behavior.strength??1)*easeWindow(frame,behavior.from,behavior.to,8);
   if(w>weight){target=behavior.target;weight=w;}
  }
  if(!target||weight===0)continue;
  const upper=rig.bones.find(b=>b.id===chain.upper);
  const lower=rig.bones.find(b=>b.id===chain.lower);
  if(!upper||!lower||lower.parent!==upper.id)continue;
  const name=chain.effector.split('.');
  if(name[0]!==lower.id)continue;
  const endpoint=lower.anchors?.[name[1]??'origin'] ?? (name[1]===undefined?{x:0,y:0}:undefined);
  if(!endpoint)continue;
  // Parent frame is evaluated with normal actions, before this IK override.
  const parentMatrix=upper.parent ? visit(upper.parent):rootM;
  const base=mul(parentMatrix,translate(upper.pivot.x,upper.pivot.y));
  const determinant=base.a*base.d-base.b*base.c;
  if(Math.abs(determinant)<1e-9)continue;
  const vx=target.x-base.e,vy=target.y-base.f;
  const local={x:(base.d*vx-base.c*vy)/determinant,y:(-base.b*vx+base.a*vy)/determinant};
  const L1=Math.hypot(lower.pivot.x,lower.pivot.y),L2=Math.hypot(endpoint.x,endpoint.y);
  if(L1<1e-5||L2<1e-5)continue;
  const solved=solveIK({x:0,y:0},local,L1,L2,chain.bend??1);
  const desiredUpper=(Math.atan2(solved.mid.y,solved.mid.x)-Math.atan2(lower.pivot.y,lower.pivot.x))*180/Math.PI;
  const desiredLower=(Math.atan2(solved.end.y-solved.mid.y,solved.end.x-solved.mid.x)-Math.atan2(endpoint.y,endpoint.x))*180/Math.PI-desiredUpper;
  ikOverrides[upper.id]=mix(boneAngleAt(ch,upper.id,frame),desiredUpper,weight);
  ikOverrides[lower.id]=mix(boneAngleAt(ch,lower.id,frame),desiredLower,weight);
 }

 for(const bone of rig.bones)visit(bone.id);
 return {root,bones};
};
export function rigAnchorAt(ch:CharacterInstance,asset:CharacterDefinition,frame:number,anchor:string,events:HighFive[]=[]):Point|null{
 const [boneId,anchorName='origin']=anchor.split('.');
 const entry=rigFrameAt(ch,asset,frame,events).bones[boneId];
 if(!entry)return null;
 const p=anchorName==='origin'?{x:0,y:0}:entry.bone.anchors?.[anchorName];
 return p?project(entry.matrix,p):null;
}
