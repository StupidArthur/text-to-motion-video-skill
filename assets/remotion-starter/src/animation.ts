import type {Motion, VideoElement} from './types';

type MotionProperty = 'dx' | 'dy' | 'opacity' | 'scale' | 'rotate';

const defaults: Record<MotionProperty, number> = {
  dx: 0,
  dy: 0,
  opacity: 1,
  scale: 1,
  rotate: 0,
};

/** Linear interpolation, with independent keyframe tracks per property. */
export const animatedValue = (
  motion: Motion[] | undefined,
  property: MotionProperty,
  frame: number,
): number => {
  const points = (motion ?? [])
    .filter((key): key is Motion & Record<typeof property, number> =>
      typeof key[property] === 'number',
    )
    .sort((a, b) => a.frame - b.frame);
  if (points.length === 0) return defaults[property];
  if (frame <= points[0].frame) return points[0][property];
  for (let i = 1; i < points.length; i++) {
    const right = points[i];
    if (frame <= right.frame) {
      const left = points[i - 1];
      const progress = (frame - left.frame) / (right.frame - left.frame);
      return left[property] + (right[property] - left[property]) * progress;
    }
  }
  return points[points.length - 1][property];
};

const centerOf = (element: VideoElement): {x: number; y: number} => {
  if (element.type === 'circle') return {x: element.x, y: element.y};
  if (element.type === 'line') {
    return {x: (element.x + element.x2) / 2, y: (element.y + element.y2) / 2};
  }
  return {x: element.x + element.width / 2, y: element.y + element.height / 2};
};

export const animationAt = (element: VideoElement, frame: number) => {
  const {x, y} = centerOf(element);
  const dx = animatedValue(element.motion, 'dx', frame);
  const dy = animatedValue(element.motion, 'dy', frame);
  const rotation = animatedValue(element.motion, 'rotate', frame);
  const scale = animatedValue(element.motion, 'scale', frame);
  const opacity = animatedValue(element.motion, 'opacity', frame);
  const transform = [
    `translate(${dx} ${dy})`,
    `translate(${x} ${y})`,
    `rotate(${rotation})`,
    `scale(${scale})`,
    `translate(${-x} ${-y})`,
  ].join(' ');
  return {opacity, transform};
};
