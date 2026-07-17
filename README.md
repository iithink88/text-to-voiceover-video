# 文案转口播视频 · text-to-voiceover-video

把**一段文案（口播稿）**一键变成 **「画面视频 + 朗读语音 + 同步字幕」的口播视频**。

> 文案同时是两件事：视频里展示的文字 + 配音/字幕的朗读内容。

本技能 = `text-to-remotion-video`（文案→画面视频）+ `video-voiceover-chatcut`（画面→加配音字幕）的合并版，**全流程脚本化、自带图形界面**。

## 朋友 3 步部署

1. **装 Python 依赖**：双击 `安装依赖.bat` → 自动建虚拟环境 + 装 `edge_tts`。
2. **准备 ffmpeg 与 Node.js**：
   - ffmpeg：下载并加入系统 PATH，或放到 `%USERPROFILE%/bin/ffmpeg/ffmpeg-*/bin`。
   - Node.js 18+：WorkBuddy 用户已自带托管 Node；其他用户请自行安装并加入 PATH。
3. **双击 `启动.bat`** → 图形界面生成口播视频。

## 图形界面用法

1. **文案**：选 txt 文件，或点「粘贴…」直接贴文本。
2. **视频比例 / 视觉风格 / 每屏时长**：按平台与观感选择（竖屏 9:16 / 横屏 16:9 / 3:4；暗色/亮色/品牌蓝；3~8 秒）。
3. **播音人 / 语速**：edge-tts 中文音色 + 0.8x~2.0x。
4. **输出目录**：默认文案同目录。
5. 点 **▶ ① 生成画面视频** → 渲染无声画面（首次需下载 Chromium，较慢）。
6. 点 **▶ ② 加入语音字幕** → 生成口播版.mp4（原画面 + 语音 + 字幕）。
7. 或点 **▶ ③ 一键全流程** → ①② 连续执行。

## 目录结构

```
text-to-voiceover-video/
├── SKILL.md              # 技能说明（AI 调用 / 工作流 / 坑位）
├── README.md             # 本文件
├── 启动.bat              # 双击启动图形界面
├── 安装依赖.bat          # 安装 edge_tts
├── setup.py              # 依赖安装脚本
├── assets/
│   └── remotion-template/  # 数据驱动 Remotion 模板（自动填充 scenes-data.ts/config.ts）
└── scripts/
    ├── gui.py            # tkinter 图形界面
    ├── generate_video.py # 第①步：文案→画面视频
    ├── make_narration.py # 第②步上部：文案→配音 mp3
    ├── merge_local.py    # 第②步下部：画面+配音+字幕→口播版
    └── paths.py          # 跨用户路径探测
```

## 无头命令版（供脚本/AI 调用）

```bash
PY="$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SKILL="$HOME/.workbuddy/skills/text-to-voiceover-video/scripts"

# ① 文案 → 画面视频
"$PY" "$SKILL/generate_video.py" --text 文案.txt --out-dir 输出目录 \
  --name 视频名 --aspect 9:16 --style dark --scene-seconds 5

# ② 画面 + 配音 + 字幕 → 口播版
"$PY" "$SKILL/make_narration.py" --text 文案.txt \
  --output 输出目录/视频名_narration/narration.mp3 --voice zh-CN-XiaoxiaoNeural --speed 1.3
"$PY" "$SKILL/merge_local.py" \
  --original 输出目录/视频名_画面.mp4 --audio 输出目录/视频名_narration/narration.mp3 \
  --text 文案.txt --output 输出目录/视频名_口播版.mp4
```

## 说明

- 第①步依赖 Node + Remotion（首次渲染下载 Chromium）。若渲染失败，技能会交付 Remotion 工程 + `渲染指引.txt`，可手动渲染后继续第②步。
- 第②步本地 ffmpeg 合成，**无需 ChatCut、无需联网**（仅 edge-tts 取微软语音需联网）。
- 模板为数据驱动：改文字改 `src/scenes-data.ts`，改风格/尺寸改 `src/config.ts`，重新渲染即可。
