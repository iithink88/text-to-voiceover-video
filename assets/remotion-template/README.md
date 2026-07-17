# 文案转口播视频 · Remotion 模板（数据驱动）

由 `text-to-voiceover-video` 技能的生成脚本自动填充。代码即视频——所有画面都是可编辑的 React 组件，**但场景数据来自 `src/scenes-data.ts`，无需手写组件**。

## 目录结构

```
.
├── package.json
├── tsconfig.json
├── remotion.config.ts
├── public/            # 放静态资源（如 bgm.mp3）
└── src/
    ├── index.ts       # 入口（registerRoot）
    ├── Root.tsx       # 定义 Composition（尺寸/时长/fps，由 config 推导）
    ├── config.ts      # 自动生成：比例/尺寸/风格/每屏秒数
    ├── scenes-data.ts # 自动生成：场景数组（文案切分结果）
    ├── Video.tsx      # 数据驱动渲染：读 scenes-data + config
    └── components/
        └── ui.tsx      # 复用组件：Background/SceneCard/...
```

## 自动生成后如何改

- **改文字/节奏**：编辑 `src/scenes-data.ts`（或重新跑生成脚本）。
- **改尺寸/风格/每屏秒数**：编辑 `src/config.ts`。
- **换主题配色**：编辑 `src/components/ui.tsx` 的 `THEMES`。
- **加背景音乐**：放 `public/bgm.mp3`，在 `Root.tsx` 的 `Video` 内加 `<Bgm src="bgm.mp3" />`。

## 运行

预览（浏览器）：
```bash
npm run dev
```

渲染 MP4：
```bash
npx remotion render src/index.ts TextToVideo out/video.mp4
```
