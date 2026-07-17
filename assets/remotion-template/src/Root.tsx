import React from "react";
import { Composition } from "remotion";
import { Video } from "./Video";
import { scenes } from "./scenes-data";
import { FPS, WIDTH, HEIGHT, SCENE_SECONDS, SCENE_DURATIONS } from "./config";

// 总时长优先用 SCENE_DURATIONS（音画同步：每屏时长按配音时长比例适配），
// 否则回退 场景数 × 每屏秒数（未提供配音时长时）。
export const RemotionRoot: React.FC = () => {
  const totalSeconds =
    SCENE_DURATIONS && SCENE_DURATIONS.length > 0
      ? SCENE_DURATIONS.reduce((a, b) => a + b, 0)
      : Math.max(1, scenes.length) * SCENE_SECONDS;
  const durationInFrames = Math.max(1, Math.round(totalSeconds * FPS));
  return (
    <Composition
      id="TextToVideo"
      component={Video}
      durationInFrames={durationInFrames}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
};
