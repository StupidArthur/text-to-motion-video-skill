import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {animationAt} from './animation';
import {DrawCharacter} from './Characters';
import {mix, smooth} from './rig';
import type {Scene, VideoElement, VideoSpec} from './types';

const DEFAULT_FONT = '"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", Arial, sans-serif';

const shapeFor = (element: VideoElement): React.ReactNode => {
  if (element.type === 'rect') {
    return <rect x={element.x} y={element.y} width={element.width} height={element.height}
      rx={element.radius ?? 0} fill={element.fill} />;
  }
  if (element.type === 'circle') {
    return <circle cx={element.x} cy={element.y} r={element.r}
      fill={element.fill} stroke={element.stroke ?? 'none'} strokeWidth={element.strokeWidth ?? 0} />;
  }
  if (element.type === 'line') {
    const sw = element.strokeWidth ?? 6;
    const dx = element.x2 - element.x;
    const dy = element.y2 - element.y;
    const length = Math.hypot(dx, dy);
    const tip = Math.max(sw * 3, 14);
    const hx = length > 0 ? dx / length : 1;
    const hy = length > 0 ? dy / length : 0;
    const bx = element.x2 - hx * tip;
    const by = element.y2 - hy * tip;
    const px = -hy * tip * 0.45;
    const py = hx * tip * 0.45;
    const points = `${element.x2},${element.y2} ${bx + px},${by + py} ${bx - px},${by - py}`;
    return <>
      <line x1={element.x} y1={element.y} x2={element.x2} y2={element.y2}
        stroke={element.stroke} strokeWidth={sw} strokeLinecap="round" />
      {element.arrowHead ? <polygon points={points} fill={element.stroke} /> : null}
    </>;
  }
  // SVG foreignObject with CSS layout is better for Chinese line breaks than bare SVG <text>.
  const alignItems = element.verticalAlign === 'middle' ? 'center'
    : element.verticalAlign === 'bottom' ? 'flex-end' : 'flex-start';
  return <foreignObject x={element.x} y={element.y} width={element.width} height={element.height}>
    <div style={{
      width: '100%', height: '100%', display: 'flex', alignItems,
      justifyContent: element.align === 'center' ? 'center' : element.align === 'right' ? 'flex-end' : 'flex-start',
      fontFamily: element.fontFamily || DEFAULT_FONT,
      fontWeight: element.fontWeight ?? 600,
      fontSize: element.fontSize,
      lineHeight: element.lineHeight ?? 1.22,
      color: element.fill,
      textAlign: element.align ?? 'left',
      overflow: 'hidden',
      whiteSpace: 'pre-wrap',
      overflowWrap: 'anywhere',
      wordBreak: 'break-word',
      boxSizing: 'border-box',
    }}>
      <span style={{display: 'block', width: '100%'}}>{element.text}</span>
    </div>
  </foreignObject>;
};

const AnimatedElement: React.FC<{element: VideoElement; frame: number}> = ({element, frame}) => {
  if (frame < (element.visibleFrom ?? 0) || frame >= (element.visibleUntil ?? Number.POSITIVE_INFINITY)) {
    return null;
  }
  const {opacity, transform} = animationAt(element, frame);
  if (opacity <= 0) return null;
  return <g opacity={opacity} transform={transform}>{shapeFor(element)}</g>;
};

const SceneFrame: React.FC<{scene: Scene; spec: VideoSpec}> = ({scene, spec}) => {
  const frame = useCurrentFrame();
  const {width, height} = spec.meta;
  const camera = scene.camera ?? [];
  const interpolated = (prop: 'x' | 'y' | 'zoom', fallback: number): number => {
    const keys = camera.filter(k => typeof k[prop] === 'number');
    if (!keys.length) return fallback;
    if (frame <= keys[0].frame) return keys[0][prop] ?? fallback;
    for (let i=1;i<keys.length;i++) if(frame<=keys[i].frame) {
      const p=smooth((frame-keys[i-1].frame)/(keys[i].frame-keys[i-1].frame));
      return mix(keys[i-1][prop] ?? fallback,keys[i][prop] ?? fallback,p);
    }
    return keys[keys.length-1][prop] ?? fallback;
  };
  const zoom = interpolated('zoom', 1);
  const cameraX = interpolated('x',width/2);
  const cameraY = interpolated('y',height/2);
  const transform = `translate(${width/2} ${height/2}) scale(${zoom}) translate(${-cameraX} ${-cameraY})`;
  const assets = new Map((spec.characterAssets ?? []).map(asset=>[asset.id,asset]));
  return <AbsoluteFill style={{backgroundColor: scene.background ?? spec.meta.background ?? '#090F1D'}}>
    <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet" style={{display: 'block', overflow: 'hidden'}}>
      <g transform={transform}>
        {scene.elements.map((element) => <AnimatedElement key={element.id} element={element} frame={frame} />)}
        {(scene.characters ?? []).map(character => {
          const asset = assets.get(character.asset);
          return asset ? <DrawCharacter key={character.id} character={character} asset={asset}
            frame={frame} interactions={scene.interactions ?? []}/> : null;
        })}
      </g>
    </svg>
    {scene.audio ? <Audio src={staticFile(scene.audio.file)} volume={scene.audio.volume ?? 1} /> : null}
  </AbsoluteFill>;
};

export const Video: React.FC<{spec: VideoSpec}> = ({spec}) => {
  let startFrame = 0;
  return <AbsoluteFill style={{backgroundColor: spec.meta.background ?? '#090F1D'}}>
    {spec.meta.music ? <Audio src={staticFile(spec.meta.music.file)} volume={spec.meta.music.volume ?? 0.2} /> : null}
    {spec.scenes.map((scene) => {
      const from = startFrame;
      startFrame += scene.durationFrames;
      return <Sequence key={scene.id} from={from} durationInFrames={scene.durationFrames}>
        <SceneFrame scene={scene} spec={spec} />
      </Sequence>;
    })}
  </AbsoluteFill>;
};
