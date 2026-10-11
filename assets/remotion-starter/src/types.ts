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

export type ShotLayer = {
  id: string; file: string; assetId?: string; x: number; y: number; width: number; height: number;
  plane?: 'back'|'front'; motion?: Motion[];
};

export type Scene = {
  layers?: ShotLayer[];
  id: string;
  durationFrames: number;
  background?: string;
  audio?: AudioRef;
  elements: VideoElement[];
  characters?: CharacterInstance[];
  interactions?: HighFive[];
  camera?: CameraFrame[];
  props?: PropInstance[];
  attachments?: Attachment[];
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
  propAssets?: PropAsset[];
};

/** V2 character animation. V1 documents without these fields still render unchanged. */
export type Point = {x: number; y: number};
export type CharacterKind = 'human' | 'dog' | 'custom';
export type CharacterDefinition = {
  id: string;
  kind: CharacterKind;
  colors?: {body?: string; skin?: string; accent?: string; outline?: string};
  rig?: CharacterRig;
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
  jointActions?: JointAction[];
  behaviors?: CharacterBehavior[];
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

/** Fully declarative, parented rig for custom human, animal and prop-like sprites. */
export type RigVisual =
  | {type:'path'; d:string; fill:string; stroke?:string; strokeWidth?:number}
  | {type:'ellipse'; cx:number; cy:number; rx:number; ry:number; fill:string}
  | {type:'rect'; x:number; y:number; width:number; height:number; fill:string; radius?:number}
  | {type:'svg'; file:string; x:number; y:number; width:number; height:number};
export type RigBone = {
  id:string; parent?:string; pivot:Point; visual?:RigVisual;
  anchors?:Record<string,Point>; layer?:number;
};
export type IKChain = {id:string; upper:string; lower:string; effector:string; bend?:1|-1};
export type CharacterRig = {bones:RigBone[]; ikChains?:IKChain[]};
export type JointKey = {frame:number; angle:number};
export type JointAction = {name:string; from:number; to:number; strength?:number;
  joints:Record<string,JointKey[]>; fadeFrames?:number};
export type CharacterBehavior = {type:'lookAt'|'reachTo'|'moveTo'; from:number; to:number;
  target:Point; hand?:'right'|'left'; strength?:number};
export type PropAsset = {id:string; visual:RigVisual};
export type PropInstance = {id:string; asset:string; x:number; y:number; scale?:number;
  rotation?:number; layer?:'back'|'front'};
export type Attachment = {id:string; prop:string; character:string; anchor:string;
  from:number; to:number; offset?:Point; releaseTo?:Point; releaseEnd?:number};
