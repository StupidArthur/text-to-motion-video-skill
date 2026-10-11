import type {Attachment, CharacterDefinition, CharacterInstance, HighFive, Point, PropInstance, Scene} from './types';
import {mix, poseAt, toWorld, smooth} from './rig';
import {rigAnchorAt} from './rig-hierarchy';

export const characterAnchorAt=(character:CharacterInstance,asset:CharacterDefinition,
  frame:number,anchor:string,events:HighFive[]=[]):Point|null=>{
 if(asset.kind==='custom')return rigAnchorAt(character,asset,frame,anchor,events);
 const pose=poseAt(character,asset,frame,events);
 const targets:Record<string,Point>={
  rightHand:pose.rightArm.end,leftHand:pose.leftArm.end,
  paw:pose.frontLeg.end,head:asset.kind==='human'?{x:0,y:-310}:{x:92,y:-170},
  root:{x:0,y:0},frontFoot:pose.frontLeg.end,backFoot:pose.backLeg.end,
 };
 const point=targets[anchor];return point?toWorld(point,pose.root):null;
};
export const propPlacementAt=(prop:PropInstance,scene:Scene,defs:CharacterDefinition[],frame:number):Point=>{
 const base={x:prop.x,y:prop.y};
 let location=base;
 const attachments=(scene.attachments??[]).filter(a=>a.prop===prop.id).sort((a,b)=>a.from-b.from);
 for(const a of attachments){
  if(frame<a.from)break;
  const ch=scene.characters?.find(c=>c.id===a.character);
  const asset=defs.find(d=>d.id===ch?.asset);
  if(!ch||!asset)continue;
  const grasp=(f:number)=>{
   const pt=characterAnchorAt(ch,asset,f,a.anchor,scene.interactions);
   return pt?{x:pt.x+(a.offset?.x??0),y:pt.y+(a.offset?.y??0)}:location;
  };
  if(frame<a.to)return grasp(frame);
  location=grasp(a.to-1);
  if(a.releaseTo && a.releaseEnd && frame<=a.releaseEnd){
   const t=smooth((frame-a.to)/Math.max(1,a.releaseEnd-a.to));
   return {x:mix(location.x,a.releaseTo.x,t),y:mix(location.y,a.releaseTo.y,t)};
  }
  if(a.releaseTo && a.releaseEnd && frame>a.releaseEnd)location=a.releaseTo;
 }
 return location;
};
