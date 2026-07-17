---
name: text-to-voiceover-video
description: 文案转口播视频（Remotion 画面 + 配音字幕）。输入一段文案（既是画面文字也是口播稿），先用数据驱动 Remotion 自动生成画面视频，再叠加 edge-tts 配音与同步字幕，产出"原画面 + 朗读语音 + 字幕"的口播视频。当用户说"把这段文案做成口播视频""文案转视频还要配音""文字自动出带解说的视频""给一段文本生成带语音字幕的短视频"等时使用。基于 text-to-remotion-video（画面生成）与 video-voiceover-chatcut（配音合成）两个技能合并而成，自带 tkinter 图形界面（双击 启动.bat 即用）。
agent_created: true
---

# 文案转口播视频（text-to-voiceover-video）

把**一段文案（口播稿）**变成**「画面视频 + 朗读语音 + 同步字幕」的口播视频**。文案同时充当两件事：视频里展示的文字、以及配音/字幕的朗读内容。

本技能 = **text-to-remotion-video（第①步：文案→画面视频）** + **video-voiceover-chatcut（第②步：画面→加配音字幕）** 的合并版，全流程脚本化、自带图形界面，朋友双击即用。

## 何时使用

- 用户给一段文案/口播稿，想直接得到"带语音字幕的成片"（不需要先手动画面）。
- 触发语示例：把这段文案做成口播视频、文案转视频还要配音、文字自动出带解说的视频、给文本生成短视频（画面+配音）。

## 图形界面（推荐，双击即用）

双击技能目录里的 **`启动.bat`**，弹出窗口后：

1. **文案**：选 txt 文件，或点「粘贴…」直接贴文本（既是画面文字，也是口播稿/字幕）
2. **视频比例**：抖音竖屏 9:16 / YouTube 横屏 16:9 / 小红书 3:4
3. **视觉风格**：科技暗色 / 简约亮色 / 品牌蓝
4. **每屏时长**：滑块 3~8 秒（默认 5s，决定总时长 = 场景数 × 每屏秒）
5. **播音人**：edge-tts 中文音色（晓晓/晓伊/云希/云扬/云健/东北/陕西/台湾）
6. **语速**：滑块 0.8x~2.0x（默认 1.3x）
7. **输出目录**：默认文案同目录
8. 点 **▶ ① 生成画面视频** → 文案切场景 → Remotion 渲染无声画面（约 1~5 分钟，首次下载 Chromium）
9. 点 **▶ ② 加入语音字幕** → 同一文案 edge-tts 配音 + 烧录字幕 → 口播版.mp4
10. 或点 **▶ ③ 一键全流程** → ①+② 连续执行

> 第②步**无需 ChatCut、无需联网**（仅 edge-tts 需联网取微软 CDN 语音）。ffmpeg 负责本地合成。

GUI 文件：`scripts/gui.py`（tkinter，托管 venv 自带 tkinter 8.6）。防闪退要点：托管 python + 入口 UTF-8 重配置 + 重活放后台线程 + 顶层 try/except 弹窗报错。

## 无头命令版（AI 在对话里调用）

路径均由 `scripts/paths.py` 自动探测，无需写死。

```bash
PY="$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SKILL="$HOME/.workbuddy/skills/text-to-voiceover-video/scripts"

# 第①步：文案 → 画面视频
"$PY" "$SKILL/generate_video.py" \
  --text  "文案.txt" \
  --out-dir "输出目录" \
  --name  "视频名" \
  --aspect "9:16" --style "dark" --scene-seconds 5

# 第②步：画面 + 配音 + 字幕 → 口播版
"$PY" "$SKILL/make_narration.py" --text "文案.txt" \
  --output "输出目录/视频名_narration/narration.mp3" \
  --voice "zh-CN-XiaoxiaoNeural" --speed 1.3

"$PY" "$SKILL/merge_local.py" \
  --original "输出目录/视频名_画面.mp4" \
  --audio   "输出目录/视频名_narration/narration.mp3" \
  --text    "文案.txt" \
  --output  "输出目录/视频名_口播版.mp4"
```

输出：`视频名_画面.mp4`（无声画面）+ `视频名_口播版.mp4`（原画面 + 朗读语音 + 白字黑描边字幕，底部居中）。

## 内置脚本

| 脚本 | 作用 |
|------|------|
| `scripts/generate_video.py` | 第①步：文案 → 切场景 → 写 `scenes-data.ts`/`config.ts` → 拷贝模板 → `npm install` → `npx remotion render` 出画面 MP4 |
| `scripts/make_narration.py` | 第②步上部：文案 → edge-tts → 配音 mp3 |
| `scripts/merge_local.py` | 第②步下部：画面 + 配音 + 字幕 → 口播版 mp4（ffmpeg 本地合成，无需 ChatCut） |
| `scripts/paths.py` | 跨用户路径探测（python venv / ffmpeg / node） |
| `scripts/gui.py` | tkinter 图形界面 |

## 数据驱动模板（关键设计）

`assets/remotion-template/` 是**数据驱动**的 Remotion 工程：

- `src/config.ts`：比例/尺寸/风格/每屏秒数（由脚本写入）
- `src/scenes-data.ts`：场景数组（由脚本把文案切分后写入）
- `src/Video.tsx`：读 `scenes-data` + `config`，自动渲染每个场景为一张卡（标题卡/正文卡 + 可选 lucide 图标），无需人工写组件

这样整个"文案→视频"过程可脚本化，朋友双击 GUI 即可用，**不依赖 AI 在环手写代码**。

## 前置依赖

- **托管 Node 18+**：WorkBuddy 自带（`~/.workbuddy/binaries/node/versions/...`）；换机器自行装 Node 18+ 并加入 PATH。首次渲染会下载 Chromium（较慢，需联网）。
- **托管 venv 含 edge_tts**：默认 `~/.workbuddy/binaries/python/envs/default`，双击 `安装依赖.bat` 自动建好。
- **ffmpeg**：需在 PATH，或放到 `%USERPROFILE%/bin/ffmpeg/ffmpeg-*/bin`（本地合成必需）。
- 联网：edge-tts 微软 CDN + Remotion 首次 Chromium 下载。

## 字幕默认样式（已固化，勿随意改小）

不传 `--fontsize` 时：白字黑描边、底部居中、智能换行最多两行；字号按分辨率自适应（约 60px 实际像素基准，`fs = max(4.0, round(60×288/vh))`）。详见 `merge_local.py` 内注释。

## 已知限制 / 坑位

- **Remotion 渲染首次需下载 Chromium**（数十 MB~百 MB），离线/受限网络会失败 → 技能**不阻塞**：照常交付 Remotion 工程 + `渲染指引.txt`，用户可手动渲染后再跑第②步。
- **第②步需要语音 CDN 联网**：edge-tts 调用微软接口；断网则配音失败，给出友好提示。
- **文案为空/只有一句**：仍会生成至少 1 个场景；超长段落自动按句切分为多屏，每屏 ≤ ~50 字以保可读性。
- **ffmpeg/libass 的 FontSize 不是像素值**：`实际像素 = FontSize × (video_height / 288)`，不要加 PlayResX/Y（会破坏换算）。要调字号用 `--fontsize`。
- **文本文件 UTF-8 无 BOM**；带 BOM 首字可能异常（脚本已用 `utf-8-sig` 读取规避）。
- 第①步渲染是重活，GUI 放后台线程并流式打印日志；请勿在渲染中途关闭窗口。

## 分享给朋友（把技能拷过去就能用）

本技能**自包含**：所有脚本与模板都在目录内，不依赖 text-to-remotion-video / video-voiceover-chatcut 已安装。

朋友 3 步部署：
1. 双击 **`安装依赖.bat`** → 建 venv + 装 edge_tts。
2. 准备 **ffmpeg**（加入 PATH）与 **Node.js 18+**（WorkBuddy 用户已自带托管 Node）。
3. 双击 **`启动.bat`** → 用图形界面生成口播视频。

## 边界

- 输出默认 MP4 H.264；画面无声（可选加 BGM 需手动改模板 `public/bgm.mp3` + `Root.tsx`）。
- 复杂转场/混音/调色建议用剪映/PR；本技能擅长"文案快速成片"。
- 第①步依赖 Node + Chromium，环境不可用自动降级为"交付工程 + 渲染指引"。
