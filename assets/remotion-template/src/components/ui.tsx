import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
} from "remotion";

// ============ 主题 ============
// dark=科技暗色 / light=简约亮色 / brand=品牌蓝。
export const THEMES: Record<
  string,
  { bg: [string, string]; title: string; body: string; accent: string }
> = {
  dark: { bg: ["#0f172a", "#1e293b"], title: "#ffffff", body: "#e2e8f0", accent: "#38bdf8" },
  light: { bg: ["#f8fafc", "#e2e8f0"], title: "#0f172a", body: "#334155", accent: "#2563eb" },
  brand: { bg: ["#1e3a8a", "#3b82f6"], title: "#ffffff", body: "#dbeafe", accent: "#fbbf24" },
};

export const getTheme = (styleKey?: string) =>
  THEMES[styleKey || "dark"] || THEMES.dark;

// ============ 动画背景 ============
// 缓慢色相偏移 + 渐变角度旋转 + 三个漂浮光晕 + 细网格 + 暗角，整体"活"起来。
export const Background: React.FC<{ styleKey?: string }> = ({ styleKey }) => {
  const frame = useCurrentFrame();
  const t = getTheme(styleKey);

  const hue = interpolate(frame, [0, 600], [0, 28], { extrapolateRight: "clamp" });
  const angle = interpolate(frame, [0, 600], [135, 215], { extrapolateRight: "clamp" });

  const orbs = [
    { seed: 0.0, color: t.accent, size: 560 },
    { seed: 2.1, color: "#1d4ed8", size: 460 },
    { seed: 4.2, color: "#a855f7", size: 380 },
  ];

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${angle}deg, ${t.bg[0]}, ${t.bg[1]})`,
        filter: `hue-rotate(${hue}deg)`,
        overflow: "hidden",
      }}
    >
      {orbs.map((o, i) => {
        const x = Math.sin(frame / 50 + o.seed) * 170 + (i % 2 ? 240 : -150);
        const y = Math.cos(frame / 64 + o.seed) * 150 + (i % 2 ? -90 : 180);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `calc(50% + ${x}px)`,
              top: `calc(50% + ${y}px)`,
              width: o.size,
              height: o.size,
              marginLeft: -o.size / 2,
              marginTop: -o.size / 2,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${o.color}55 0%, ${o.color}00 70%)`,
              filter: "blur(40px)",
              opacity: 0.55,
            }}
          />
        );
      })}

      {/* 细网格缓慢移动，增加科技感 */}
      <div
        style={{
          position: "absolute",
          inset: -40,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          backgroundPosition: `${Math.sin(frame / 80) * 30}px ${Math.cos(frame / 90) * 30}px`,
          opacity: 0.5,
        }}
      />

      {/* 暗角，增加层次 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.45) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// 四角 HUD 装饰框
const CornerBrackets: React.FC<{ color: string; opacity: number }> = ({
  color,
  opacity,
}) => {
  const base: React.CSSProperties = {
    position: "absolute",
    width: 48,
    height: 48,
    borderColor: color,
    opacity,
  };
  const w = 5;
  return (
    <>
      <div
        style={{
          ...base,
          top: 56,
          left: 56,
          borderTop: `${w}px solid ${color}`,
          borderLeft: `${w}px solid ${color}`,
          borderTopLeftRadius: 8,
        }}
      />
      <div
        style={{
          ...base,
          top: 56,
          right: 56,
          borderTop: `${w}px solid ${color}`,
          borderRight: `${w}px solid ${color}`,
          borderTopRightRadius: 8,
        }}
      />
      <div
        style={{
          ...base,
          bottom: 56,
          left: 56,
          borderBottom: `${w}px solid ${color}`,
          borderLeft: `${w}px solid ${color}`,
          borderBottomLeftRadius: 8,
        }}
      />
      <div
        style={{
          ...base,
          bottom: 56,
          right: 56,
          borderBottom: `${w}px solid ${color}`,
          borderRight: `${w}px solid ${color}`,
          borderBottomRightRadius: 8,
        }}
      />
    </>
  );
};

// 强调色下划线（生长动画）
const Underline: React.FC<{ color: string; frame: number; delay: number }> = ({
  color,
  frame,
  delay,
}) => {
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 120 } });
  const w = interpolate(p, [0, 1], [0, 280], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        height: 6,
        width: w,
        borderRadius: 3,
        background: color,
        marginTop: 16,
        boxShadow: `0 0 16px ${color}`,
      }}
    />
  );
};

// 底部进度条
const ProgressBar: React.FC<{ color: string; progress: number; opacity: number }> = ({
  color,
  progress,
  opacity,
}) => (
  <div
    style={{
      position: "absolute",
      bottom: 56,
      left: 56,
      right: 56,
      height: 5,
      borderRadius: 3,
      background: "rgba(255,255,255,0.15)",
      opacity,
    }}
  >
    <div
      style={{
        height: "100%",
        width: `${progress * 100}%`,
        borderRadius: 3,
        background: color,
        boxShadow: `0 0 12px ${color}`,
      }}
    />
  </div>
);

// 把正文按标点切成"分句"，用于逐句递进浮现
function splitClauses(s: string): string[] {
  const re = /[^，。；、！？\n]+[，。；、！？\n]?/g;
  const m = s.match(re);
  return m && m.length ? m : [s];
}

// ============ 场景卡（自动生成路径使用） ============
// 一屏一卡：图标弹出+悬浮 → 标题逐字浮现+下划线生长 → 正文分句递进；
// 末尾缩放淡出，与下一屏交叉转场。
export const SceneCard: React.FC<{
  scene: { kind: "title" | "body"; title?: string; body?: string };
  styleKey?: string;
  iconNode?: React.ReactNode;
  framesPerScene: number;
}> = ({ scene, styleKey, iconNode, framesPerScene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = getTheme(styleKey);

  const EXIT = 16;
  const exitStart = Math.max(1, framesPerScene - EXIT);

  // 退出进度
  const exitP = interpolate(frame, [exitStart, framesPerScene], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cardOpacity = 1 - exitP;
  const cardScale = interpolate(exitP, [0, 1], [1, 0.92]);
  const cardY = interpolate(exitP, [0, 1], [0, -28]);

  // 图标弹出（带轻微过冲）+ 持续悬浮
  const iconSpring = spring({
    frame: frame - 3,
    fps,
    config: { damping: 11, stiffness: 150, mass: 0.7 },
  });
  const iconScale = interpolate(iconSpring, [0, 1], [0, 1], { extrapolateRight: "clamp" });
  const iconFloat = Math.sin(frame / 16) * 5;

  const isTitle = scene.kind === "title";
  const titleSize = isTitle ? 96 : 70;
  const bodySize = isTitle ? 40 : 46;

  const titleChars = scene.title ? Array.from(scene.title) : [];
  const clauses = scene.body ? splitClauses(scene.body) : [];
  // 分句错峰：总窗口控制在 ~60 帧内
  const clauseStagger = Math.max(4, Math.min(7, 60 / Math.max(1, clauses.length)));

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: 96,
        flexDirection: "column",
        gap: 26,
        opacity: cardOpacity,
        transform: `translateY(${cardY}px) scale(${cardScale})`,
      }}
    >
      <CornerBrackets color={t.accent} opacity={1 - exitP} />

      {iconNode && (
        <div
          style={{
            color: t.accent,
            transform: `translateY(${iconFloat}px) scale(${iconScale})`,
            opacity: iconScale,
            filter: `drop-shadow(0 0 16px ${t.accent}88)`,
            marginBottom: 10,
          }}
        >
          {iconNode}
        </div>
      )}

      {scene.title && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <h1
            style={{
              fontSize: titleSize,
              fontWeight: 800,
              color: t.title,
              textAlign: "center",
              lineHeight: 1.18,
              margin: 0,
              letterSpacing: 2,
            }}
          >
            {titleChars.map((ch, i) => {
              const start = 6 + i * 2.2;
              const p = interpolate(frame, [start, start + 9], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              const y = interpolate(p, [0, 1], [26, 0]);
              const sc = interpolate(p, [0, 1], [0.85, 1]);
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    opacity: p,
                    transform: `translateY(${y}px) scale(${sc})`,
                  }}
                >
                  {ch === " " ? " " : ch}
                </span>
              );
            })}
          </h1>
          <Underline color={t.accent} frame={frame} delay={6 + titleChars.length * 2.2} />
        </div>
      )}

      {scene.body && (
        <div
          style={{
            marginTop: scene.title ? 22 : 0,
            display: "flex",
            flexDirection: "column",
            gap: 14,
            maxWidth: "90%",
          }}
        >
          {clauses.map((cl, i) => {
            const start = 10 + i * clauseStagger;
            const p = interpolate(frame, [start, start + 12], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const x = interpolate(p, [0, 1], [-30, 0]);
            return (
              <p
                key={i}
                style={{
                  fontSize: bodySize,
                  color: t.body,
                  textAlign: "center",
                  lineHeight: 1.5,
                  margin: 0,
                  fontWeight: 600,
                  opacity: p,
                  transform: `translateX(${x}px)`,
                }}
              >
                {cl}
              </p>
            );
          })}
        </div>
      )}

      <ProgressBar
        color={t.accent}
        progress={interpolate(frame, [0, framesPerScene], [0, 1], {
          extrapolateRight: "clamp",
        })}
        opacity={1 - exitP}
      />
    </AbsoluteFill>
  );
};

// ============ 以下为手动编辑时可复用的组件（自动路径未使用，保留） ============
export const TitleCard: React.FC<{ title: string; subtitle?: string }> = ({
  title,
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const slide = spring({ frame, fps, config: { damping: 12, stiffness: 120 } });
  const y = interpolate(slide, [0, 1], [40, 0]);
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
        opacity,
        transform: `translateY(${y}px)`,
      }}
    >
      <h1 style={{ fontSize: 84, fontWeight: 800, color: "white", textAlign: "center", lineHeight: 1.1, margin: 0 }}>
        {title}
      </h1>
      {subtitle && (
        <p style={{ fontSize: 40, color: "#cbd5e1", textAlign: "center", marginTop: 24 }}>{subtitle}</p>
      )}
    </AbsoluteFill>
  );
};

export const BulletList: React.FC<{ items: { icon?: React.ReactNode; text: string }[] }> = ({
  items,
}) => (
  <AbsoluteFill style={{ justifyContent: "center", padding: 100, gap: 28, flexDirection: "column" }}>
    {items.map((it, i) => (
      <BulletItem key={i} icon={it.icon} text={it.text} />
    ))}
  </AbsoluteFill>
);

const BulletItem: React.FC<{ icon?: React.ReactNode; text: string }> = ({ icon, text }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const x = interpolate(frame, [0, 12], [-40, 0], { extrapolateRight: "clamp" });
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 24, opacity, transform: `translateX(${x}px)` }}>
      {icon && <div style={{ flexShrink: 0, color: "#38bdf8" }}>{icon}</div>}
      <span style={{ fontSize: 44, color: "white", fontWeight: 600 }}>{text}</span>
    </div>
  );
};

export const Caption: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 80, opacity }}>
      <div style={{ background: "rgba(0,0,0,0.55)", color: "white", fontSize: 38, fontWeight: 600, padding: "16px 32px", borderRadius: 16, maxWidth: "85%", textAlign: "center" }}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const IconRow: React.FC<{ items: { icon: React.ReactNode; label: string }[] }> = ({
  items,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ flexDirection: "row", justifyContent: "space-around", alignItems: "center", padding: 80 }}>
      {items.map((it, i) => {
        const enter = spring({ frame: frame - i * 8, fps, config: { damping: 14, stiffness: 100 } });
        const scale = interpolate(enter, [0, 1], [0.6, 1], { extrapolateRight: "clamp" });
        return (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, transform: `scale(${scale})` }}>
            <div style={{ color: "#38bdf8" }}>{it.icon}</div>
            <span style={{ color: "white", fontSize: 36, fontWeight: 700 }}>{it.label}</span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
