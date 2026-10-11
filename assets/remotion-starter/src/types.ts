/** The supported, intentionally small JSON schema. See <SKILL_ROOT>/references/SCENE_DSL.md */
export type Motion = {
  frame: number;
  dx?: number;
  dy?: number;
  opacity?: number;
  scale?: number;
  rotate?: number;
};

type BaseElement = {
  id: string;
  visibleFrom?: number;
  visibleUntil?: number;
  motion?: Motion[];
};

type BaseBox = {x: number; y: number; width: number; height: number};

export type TextElement = BaseElement &
  BaseBox & {
    type: 'text';
    text: string;
    fill: string;
    fontSize: number;
    fontWeight?: number;
    fontFamily?: string;
    lineHeight?: number;
    align?: 'left' | 'center' | 'right';
    verticalAlign?: 'top' | 'middle' | 'bottom';
  };

export type RectElement = BaseElement &
  BaseBox & {
    type: 'rect';
    fill: string;
    radius?: number;
  };

export type CircleElement = BaseElement & {
  type: 'circle';
  x: number;
  y: number;
  r: number;
  fill: string;
  stroke?: string;
  strokeWidth?: number;
};

export type LineElement = BaseElement & {
  type: 'line';
  x: number;
  y: number;
  x2: number;
  y2: number;
  stroke: string;
  strokeWidth?: number;
  arrowHead?: boolean;
};

export type VideoElement = TextElement | RectElement | CircleElement | LineElement;
export type AudioRef = {file: string; volume?: number};

export type Scene = {
  id: string;
  durationFrames: number;
  background?: string;
  audio?: AudioRef;
  elements: VideoElement[];
  characters?: CharacterInstance[];
  interactions?: HighFive[];
  camera?: CameraFrame[];
};

export type VideoSpec = {
  meta: {
    title: string;
    width: number;
    height: number;
    fps: number;
    background?: string;
    music?: AudioRef;
  };
  scenes: Scene[];
  characterAssets?: CharacterDefinition[];
};

/** V2 character animation. V1 documents without these fields still render unchanged. */
export type Point = {x: number; y: number};
export type CharacterKind = 'human' | 'dog';
export type CharacterDefinition = {
  id: string;
  kind: CharacterKind;
  colors?: {body?: string; skin?: string; accent?: string; outline?: string};
};
export type CharacterKeyframe = {frame: number; x: number; y: number; scale?: number; facing?: 1 | -1};
export type CharacterActionName = 'idle' | 'walk' | 'run' | 'wave' | 'sit' | 'reach' | 'pawRaise' | 'blink' | 'headTurn' | 'tailWag';
export type CharacterAction = {name: CharacterActionName; from: number; to: number; strength?: number};
export type CharacterInstance = {
  id: string;
  asset: string;
  x: number;
  y: number;
  scale?: number;
  facing?: 1 | -1;
  motion?: CharacterKeyframe[];
  actions?: CharacterAction[];
};
export type HighFive = {
  id: string;
  type: 'highFive';
  actors: [string, string];
  frame: number;
  target: Point;
  holdFrames?: number;
};
export type CameraFrame = {frame: number; x?: number; y?: number; zoom?: number};
