import React from "react";
import { Rocket, Zap, Shield } from "lucide-react";
import { TitleCard, Caption, IconRow } from "../components/ui";

// 示例场景：展示标题卡 + 字幕 + 图标功能三联的写法。
// 实际生成时，把这里替换成由文案推导的场景组件。

export const IntroScene: React.FC = () => (
  <>
    <TitleCard title="用文字生成视频" subtitle="Remotion 驱动 · 代码即视频" />
    <Caption text="把文案一键变成可编辑的短视频" />
  </>
);

export const FeaturesScene: React.FC = () => (
  <IconRow
    items={[
      { icon: <Rocket size={96} />, label: "快速" },
      { icon: <Zap size={96} />, label: "高效" },
      { icon: <Shield size={96} />, label: "稳定" },
    ]}
  />
);
