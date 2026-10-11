import React from 'react';
import {Composition} from 'remotion';
import videoJSON from '../video.json';
import {Video} from './Video';
import type {VideoSpec} from './types';

const spec = videoJSON as unknown as VideoSpec;
const durationInFrames = spec.scenes.reduce((total, scene) => total + scene.durationFrames, 0);

export const RemotionRoot: React.FC = () => <Composition
  id="Main"
  component={Video}
  durationInFrames={durationInFrames}
  width={spec.meta.width}
  height={spec.meta.height}
  fps={spec.meta.fps}
  defaultProps={{spec}}
/>;
