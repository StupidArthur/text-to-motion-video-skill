import type {
  CharacterActionName, CharacterInstance, CharacterDefinition,
  HighFive, Point,
} from './types';

export type {Point};
export type JointChain = {root: Point; mid: Point; end: Point; reachable: boolean};
export type RootPose = {x: number; y: number; scale: number; facing: 1 | -1};
export type CharacterPose = {
  root: RootPose;
  rightArm: JointChain;
  leftArm: JointChain;
  frontLeg: JointChain;
  backLeg: JointChain;
  blink: number;
  tilt: number;
  tail: number;
  sit: number;
  gait: number;
  kind: CharacterDefinition['kind'];
};

export const clamp = (x: number, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, x));
export const smooth = (v: number) => { const t = clamp(v); return t * t * (3 - 2 * t); };
export const mix = (a: number, b: number, weight: number) => a + (b - a) * weight;
export const distance = (a: Point, b: Point) => Math.hypot(b.x - a.x, b.y - a.y);
export const interpolatePoint = (a: Point, b: Point, weight: number): Point => ({x: mix(a.x, b.x, weight), y: mix(a.y, b.y, weight)});

/** Stable, order-independent two-link IK. Unreachable targets are clamped at the limb boundary. */
export function solveIK(origin: Point, target: Point, upper: number, lower: number, bend = 1): JointChain {
  const deltaX = target.x - origin.x;
  const deltaY = target.y - origin.y;
  const rawDist = Math.hypot(deltaX, deltaY);
  const minimum = Math.abs(upper - lower) + 0.00001;
  const maximum = upper + lower - 0.00001;
  const d = clamp(rawDist, minimum, maximum);
  const dx = rawDist < 1e-7 ? 1 : deltaX / rawDist;
  const dy = rawDist < 1e-7 ? 0 : deltaY / rawDist;
  const projection = (upper * upper + d * d - lower * lower) / (2 * d);
  const normal = Math.sqrt(Math.max(0, upper * upper - projection * projection));
  const mid = {x: origin.x + dx * projection - dy * normal * bend,
               y: origin.y + dy * projection + dx * normal * bend};
  const end = {x: origin.x + dx * d, y: origin.y + dy * d};
  return {root: origin, mid, end, reachable: rawDist >= minimum && rawDist <= maximum};
}

/** Explicit frame keyframes avoid CSS / wall-clock based motion. */
export function rootAt(char: CharacterInstance, frame: number): RootPose {
  const defaults = {x: char.x, y: char.y, scale: char.scale ?? 1, facing: char.facing ?? 1 as 1 | -1};
  const points = char.motion ?? [];
  if (!points.length || frame < points[0].frame) return defaults;
  const property = (i: number) => ({
    x: points[i].x, y: points[i].y,
    scale: points[i].scale ?? defaults.scale,
    facing: points[i].facing ?? defaults.facing,
  });
  if (frame >= points[points.length - 1].frame) return property(points.length - 1);
  for (let i = 1; i < points.length; i++) {
    if (frame <= points[i].frame) {
      const a = property(i - 1), b = property(i);
      const t = smooth((frame - points[i - 1].frame) / (points[i].frame - points[i - 1].frame));
      return {x: mix(a.x,b.x,t), y: mix(a.y,b.y,t), scale: mix(a.scale,b.scale,t),
              facing: t < 0.5 ? a.facing : b.facing};
    }
  }
  return defaults;
}

export function toLocal(world: Point, root: RootPose): Point {
  return {x: (world.x - root.x) / (root.scale * root.facing), y: (world.y - root.y) / root.scale};
}
export function toWorld(local: Point, root: RootPose): Point {
  return {x: root.x + local.x * root.scale * root.facing, y: root.y + local.y * root.scale};
}

export function actionWeight(ch: CharacterInstance, name: CharacterActionName, frame: number) {
  const matches = (ch.actions ?? []).filter(a => a.name === name && frame >= a.from && frame <= a.to);
  return matches.reduce((max, action) => {
    const envelope = Math.min(1, (frame - action.from) / 9, (action.to - frame) / 9);
    return Math.max(max, smooth(envelope) * (action.strength ?? 1));
  }, 0);
}

export function contactWeight(interaction: HighFive, frame: number): number {
  const rise = smooth((frame - (interaction.frame - 13)) / 13);
  const fall = 1 - smooth((frame - (interaction.frame + (interaction.holdFrames ?? 8))) / 13);
  return clamp(rise * fall);
}

/** Positions and limbs are returned numerically; they can be tested without Chromium. */
export function poseAt(
  character: CharacterInstance, asset: CharacterDefinition,
  frame: number, interactions: HighFive[] = [],
): CharacterPose {
  const root = rootAt(character, frame);
  const run = actionWeight(character, 'run', frame);
  const walk = actionWeight(character, 'walk', frame);
  const gaitStrength = Math.max(run, walk * 0.55);
  const gait = Math.sin(frame * (run > walk ? 0.42 : 0.25)) * gaitStrength;
  const sit = actionWeight(character, 'sit', frame);
  const wave = actionWeight(character, 'wave', frame);
  const reach = actionWeight(character, 'reach', frame);
  const raise = actionWeight(character, 'pawRaise', frame);
  const blink = actionWeight(character, 'blink', frame) ||
    ((frame + (asset.kind === 'human' ? 2 : 47)) % 103 < 4 ? 1 : 0);
  const tilt = actionWeight(character, 'headTurn', frame) * 12;
  const tail = Math.sin(frame * 0.32) * (actionWeight(character, 'tailWag', frame) || 0.25);
  let rightArm: JointChain;
  let leftArm: JointChain;
  let frontLeg: JointChain;
  let backLeg: JointChain;
  let highFive: {weight: number; target: Point} | undefined;
  for (const interaction of interactions) {
    if (interaction.actors.includes(character.id)) {
      const w = contactWeight(interaction, frame);
      if (w > (highFive?.weight ?? 0)) highFive = {weight: w, target: toLocal(interaction.target,root)};
    }
  }
  if (asset.kind === 'human') {
    const shoulder = {x: 39, y: -219};
    const wavingEnd = {x: 86 + Math.sin(frame * 0.48) * 11, y: -325};
    const neutral = {x: 73 + gait * 20, y: -116};
    const reaching = {x: 176, y: -211};
    const destination = interpolatePoint(interpolatePoint(neutral,wavingEnd,wave),reaching,reach);
    const point = highFive ? interpolatePoint(destination,highFive.target,highFive.weight) : destination;
    rightArm = solveIK(shoulder,point,101,103,-1);
    const leftShoulder = {x:-39,y:-219};
    leftArm = solveIK(leftShoulder,{x:-67-gait*18,y:-115},99,102,1);
    frontLeg = solveIK({x:27,y:-108},{x:27+gait*35,y:-5},85,88,1);
    backLeg = solveIK({x:-27,y:-108},{x:-27-gait*35,y:-5},85,88,-1);
  } else {
    const frontShoulder = {x:66,y:-110};
    const neutral = {x:85 + gait*27,y:-11};
    const lifted = {x:210,y:-137};
    const destination = interpolatePoint(neutral,lifted,raise);
    const point = highFive ? interpolatePoint(destination,highFive.target,highFive.weight) : destination;
    frontLeg = solveIK(frontShoulder,point,115,115,-1);
    backLeg = solveIK({x:-65,y:-105},{x:-83-gait*28,y:-5},95,92,1);
    rightArm = frontLeg;
    leftArm = solveIK({x:45,y:-103},{x:45-gait*25,y:-5},96,99,1);
  }
  return {root,rightArm,leftArm,frontLeg,backLeg,blink,tilt,tail,sit,gait,kind:asset.kind};
}

export function contactError(chars: CharacterInstance[], assets: CharacterDefinition[], event: HighFive): number {
  const participants = event.actors.map(id => chars.find(c=>c.id===id));
  if (participants.some(c=>!c)) return Infinity;
  const endpoints = participants.map(char => {
    const asset = assets.find(a=>a.id===char!.asset);
    if (!asset) return null;
    const pose = poseAt(char!, asset,event.frame,[event]);
    return toWorld(asset.kind==='human' ? pose.rightArm.end : pose.frontLeg.end,pose.root);
  });
  if (!endpoints[0] || !endpoints[1]) return Infinity;
  return distance(endpoints[0],endpoints[1]);
}
