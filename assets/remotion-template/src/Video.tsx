import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Background, SceneCard } from "./components/ui";
import { scenes } from "./scenes-data";
import { STYLE, SCENE_SECONDS, SCENE_DURATIONS, FPS } from "./config";
import {
  Rocket,
  Zap,
  Shield,
  Target,
  Users,
  Clock,
  Coins,
  TrendingUp,
  Lightbulb,
  CheckCircle,
  Star,
  Heart,
  BookOpen,
  Globe,
  Sparkles,
} from "lucide-react";

// 图标注册表：scenes-data.ts 里的 icon 字符串映射到 lucide 组件。
// 颜色由 SceneCard 按主题统一设置，这里不写死。
const ICONS: Record<string, React.ReactNode> = {
  rocket: <Rocket size={96} />,
  zap: <Zap size={96} />,
  shield: <Shield size={96} />,
  target: <Target size={96} />,
  users: <Users size={96} />,
  clock: <Clock size={96} />,
  coins: <Coins size={96} />,
  trending: <TrendingUp size={96} />,
  bulb: <Lightbulb size={96} />,
  check: <CheckCircle size={96} />,
  star: <Star size={96} />,
  heart: <Heart size={96} />,
  book: <BookOpen size={96} />,
  globe: <Globe size={96} />,
  sparkles: <Sparkles size={96} />,
};

// 数据驱动：每个场景一个 <Sequence>，时长由 config.ts 决定。
// 音画同步时 SCENE_DURATIONS[i] 为逐屏秒数（按字数比例），否则回退 SCENE_SECONDS。
// 无需手写组件——所有画面都来自 scenes-data.ts 的数据。
export const Video: React.FC = () => {
  // 计算每屏帧数与累计起始帧
  const durations = scenes.map(
    (_, i) => (SCENE_DURATIONS && SCENE_DURATIONS[i]) || SCENE_SECONDS
  );
  const framesOf = durations.map((sec) => Math.max(1, Math.round(sec * FPS)));
  const starts: number[] = [];
  let acc = 0;
  for (const f of framesOf) {
    starts.push(acc);
    acc += f;
  }
  return (
    <AbsoluteFill>
      <Background styleKey={STYLE} />
      {scenes.map((s, i) => (
        <Sequence
          key={i}
          from={starts[i]}
          durationInFrames={framesOf[i]}
        >
          <SceneCard
            scene={s}
            styleKey={STYLE}
            iconNode={s.icon ? ICONS[s.icon] : undefined}
            framesPerScene={framesOf[i]}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
