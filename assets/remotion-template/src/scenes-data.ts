// 自动生成，请勿手动修改（由生成脚本 text-to-voiceover-video/scripts/generate_video.py 写入）。
// 每个场景对应视频一屏：kind=title 为大字标题卡，kind=body 为要点正文卡。
// icon 为 lucide 图标名（见 src/Video.tsx 的 ICONS 注册表），可省略。

export interface SceneData {
  kind: "title" | "body";
  title?: string;
  body?: string;
  icon?: string;
}

export const scenes: SceneData[] = [
  { kind: "title", title: "用文字生成视频", icon: "rocket" },
  { kind: "body", body: "把一段文案，自动变成可编辑的短视频。", icon: "bulb" },
  { kind: "body", body: "画面由 Remotion 代码驱动，随时可改。", icon: "sparkles" },
];
