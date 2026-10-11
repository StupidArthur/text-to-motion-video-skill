import React from 'react';
import {staticFile} from 'remotion';
import type {RigVisual} from './types';

/** All imported SVG art stays as an image asset; arbitrary SVG XML is never evaluated. */
export const AssetVisual:React.FC<{visual:RigVisual}>=({visual})=>{
  if(visual.type==='path')return <path d={visual.d} fill={visual.fill} stroke={visual.stroke??'none'} strokeWidth={visual.strokeWidth??0}/>;
  if(visual.type==='rect')return <rect x={visual.x} y={visual.y} width={visual.width} height={visual.height} rx={visual.radius??0} fill={visual.fill}/>;
  if(visual.type==='ellipse')return <ellipse cx={visual.cx} cy={visual.cy} rx={visual.rx} ry={visual.ry} fill={visual.fill}/>;
  return <image x={visual.x} y={visual.y} width={visual.width} height={visual.height}
    href={staticFile(visual.file)} preserveAspectRatio="xMidYMid meet"/>;
};
