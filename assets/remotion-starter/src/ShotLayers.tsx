import React from 'react';
import {staticFile} from 'remotion';
import {animatedValue} from './animation';
import type {ShotLayer} from './types';

/** Per-shot images, generated on demand by the Code Agent and placed in public/.
 * Do not reinterpret visual-bible descriptions as assets; only real files render.
 */
export const ShotLayers: React.FC<{layers: ShotLayer[] | undefined; frame: number; plane:'back'|'front'}> = ({layers,frame,plane}) => {
  return <>{(layers??[]).filter(l=>(l.plane??'back')===plane).map(layer=>{
    const motion=layer.motion;
    const dx=animatedValue(motion,'dx',frame);
    const dy=animatedValue(motion,'dy',frame);
    const opacity=animatedValue(motion,'opacity',frame);
    const scale=animatedValue(motion,'scale',frame);
    const angle=animatedValue(motion,'rotate',frame);
    const cx=layer.x+layer.width/2;
    const cy=layer.y+layer.height/2;
    const transform=`translate(${dx} ${dy}) translate(${cx} ${cy}) rotate(${angle}) scale(${scale}) translate(${-cx} ${-cy})`;
    return <g key={layer.id} opacity={opacity} transform={transform}>
      <image href={staticFile(layer.file)} x={layer.x} y={layer.y} width={layer.width} height={layer.height}
        preserveAspectRatio="xMidYMid meet" />
    </g>;
  })}</>;
};
