import React from 'react';
import type {CharacterDefinition, CharacterInstance, HighFive, Point} from './types';
import {poseAt} from './rig';
import type {JointChain} from './rig';

const LineBone: React.FC<{a: Point; b: Point; color: string; thick: number}> = ({a,b,color,thick}) =>
  <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={color} strokeWidth={thick} strokeLinecap="round"/>;
const Chain: React.FC<{chain: JointChain; color: string; thick?: number}> = ({chain,color,thick=21}) => <g>
  <LineBone a={chain.root} b={chain.mid} color={color} thick={thick}/>
  <LineBone a={chain.mid} b={chain.end} color={color} thick={thick*0.83}/>
  <circle cx={chain.end.x} cy={chain.end.y} r={thick*.52} fill={color}/>
</g>;

export const DrawCharacter: React.FC<{
  character: CharacterInstance;
  asset: CharacterDefinition;
  frame: number;
  interactions: HighFive[];
}> = ({character,asset,frame,interactions}) => {
  const p = poseAt(character,asset,frame,interactions);
  const {root} = p;
  const body = asset.colors?.body ?? (asset.kind==='human' ? '#8B5CF6' : '#DCA269');
  const skin = asset.colors?.skin ?? (asset.kind==='human' ? '#F0BA8B' : '#F5CE9B');
  const accent = asset.colors?.accent ?? (asset.kind==='human' ? '#402F7A' : '#774D31');
  const stroke = asset.colors?.outline ?? '#1E293B';
  return <g transform={`translate(${root.x} ${root.y}) scale(${root.scale * root.facing} ${root.scale})`}>
    {asset.kind === 'human' ? <g>
      {/* Back limbs, torso, front limbs, head: stable SVG painter order */}
      <Chain chain={p.leftArm} color={skin} thick={24}/>
      <Chain chain={p.backLeg} color={accent} thick={29}/>
      <Chain chain={p.frontLeg} color={accent} thick={29}/>
      <ellipse cx={0} cy={-172} rx={55} ry={82} fill={body} stroke={stroke} strokeWidth={3}/>
      <rect x={-42} y={-122} width={84} height={24} rx={12} fill={accent}/>
      <Chain chain={p.rightArm} color={skin} thick={23}/>
      <g transform={`rotate(${p.tilt} 0 -280)`}>
        <rect x={-19} y={-262} width={38} height={30} rx={14} fill={skin}/>
        <ellipse cx={0} cy={-310} rx={66} ry={71} fill={skin} stroke={stroke} strokeWidth={3}/>
        <path d="M-65,-317 Q-60,-403 8,-388 Q71,-384 60,-317 Q24,-353 -25,-343 Z" fill={accent}/>
        <ellipse cx={-21} cy={-307} rx={5} ry={p.blink>0.55?1.2:7} fill={stroke}/>
        <ellipse cx={25} cy={-307} rx={5} ry={p.blink>0.55?1.2:7} fill={stroke}/>
        <path d="M-15,-283 Q0,-270 19,-284" fill="none" stroke={stroke} strokeWidth={3} strokeLinecap="round"/>
        <circle cx={-63} cy={-302} r={10} fill={skin}/>
      </g>
    </g> : <g>
      {/* Dog anatomy is in its own local 2D rig coordinate space */}
      <Chain chain={p.backLeg} color={body} thick={29}/>
      <Chain chain={p.leftArm} color={body} thick={25}/>
      <path d={`M-105,-135 Q-175,${-190 + p.tail*55} -172,${-245 + p.tail*45}`}
        stroke={body} strokeWidth={29} fill="none" strokeLinecap="round"/>
      <ellipse cx={0} cy={-122 + p.sit*19} rx={130} ry={75+p.sit*6} fill={body} stroke={stroke} strokeWidth={3}/>
      <circle cx={-88} cy={-90 + p.sit*20} r={44} fill={body}/>
      <Chain chain={p.frontLeg} color={skin} thick={25}/>
      <g transform={`rotate(${p.tilt} 80 -182)`}>
        <ellipse cx={92} cy={-170+p.sit*7} rx={62} ry={68} fill={body} stroke={stroke} strokeWidth={3}/>
        <path d="M47,-222 Q26,-291 52,-271 Q74,-265 78,-232" fill={accent}/>
        <path d="M122,-215 Q150,-278 159,-257 Q166,-223 135,-197" fill={accent}/>
        <ellipse cx={139} cy={-149} rx={55} ry={34} fill={skin}/>
        <circle cx={178} cy={-165} r={12} fill={stroke}/>
        <ellipse cx={111} cy={-192} rx={6} ry={p.blink>0.55?1.5:9} fill={stroke}/>
        <path d="M160,-136 Q132,-119 118,-141" fill="none" stroke={stroke} strokeWidth={3}/>
      </g>
    </g>}
  </g>;
};
