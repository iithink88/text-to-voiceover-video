#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文案 → Remotion 工程 → 渲染 MP4（text-to-voiceover-video 第①步）
==============================================================
把一段文案自动切成"场景数组"，写入数据驱动的 Remotion 模板，再用托管 Node 渲染成
无声/带BGM的"画面视频"。整个过程无需 AI 手写组件——所有画面来自 scenes-data.ts。

依赖：托管 Node（~/.workbuddy/binaries/node/...）或系统 Node 18+；首次渲染会自动下载 Chromium。
失败不阻塞：渲染失败时仍交付完整工程 + 渲染指引（RENDER_GUIDE 标记），供手动渲染。
"""
import sys, os, re, json, argparse, shutil, subprocess

# —— Windows Python 子进程编码铁律：入口强制 UTF-8 ——
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# —— 文本编码自动探测（兼容中文 Windows 的 GBK 文案，避免中文乱码）——
try:
    from paths import read_text
except Exception:
    def read_text(path):
        with open(path, "rb") as f:
            raw = f.read()
        for enc in ("utf-8-sig", "gb18030", "utf-8"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin-1")

TEMPLATE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "remotion-template")
)

ASPECTS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "3:4": (1080, 1440),
}

# 关键词 → 图标名（对应 src/Video.tsx 的 ICONS 注册表）
ICON_KEYWORDS = {
    "rocket": ["启动", "发布", "上线", "开始", "火箭", "launch"],
    "zap": ["高效", "效率", "极速", "闪电", "加速", "快"],
    "shield": ["安全", "保护", "稳定", "可靠", "防护", "盾"],
    "target": ["目标", "定位", "精准", "瞄准", "target"],
    "users": ["用户", "客户", "团队", "人群", "粉丝", "用户量"],
    "clock": ["时间", "效率", "节省", "周期", "时刻", "秒"],
    "coins": ["钱", "价格", "成本", "收益", "利润", "收入", "币", "收费", "免费"],
    "trending": ["增长", "趋势", "上升", "数据", "提升", "涨", "翻倍"],
    "bulb": ["想法", "创意", "思考", "点子", "灵感", "建议", "思路"],
    "check": ["完成", "成功", "正确", "确认", "通过", "ok", "搞定", "达标"],
    "star": ["优秀", "最好", "顶级", "推荐", "星", "精选"],
    "heart": ["喜欢", "爱", "情感", "关怀", "用心", "贴心"],
    "book": ["学习", "知识", "书", "课程", "阅读", "教", "笔记"],
    "globe": ["全球", "世界", "国际", "网络", "联网", "全网"],
    "sparkles": ["智能", "ai", "魔法", "惊喜", "亮点", "自动", "一键", "协同", "融合"],
    "users": ["教师", "老师", "学生", "育人", "班级", "学校", "教育", "教学", "培养", "人才", "协同"],
    "book": ["课程", "专业", "能力", "素养", "知识", "学习", "成长", "发展"],
    "target": ["目标", "定位", "精准", "方向", "重点", "核心"],
    "trending": ["提升", "优化", "进步", "突破", "创新", "改革"],
    "check": ["实践", "落地", "共赢", "方案", "解决", "路径", "方法"],
}

# 关键词未命中时按索引轮转的默认图标，保证每屏都有视觉元素（对应 ICONS 注册表）。
DEFAULT_ICONS = [
    "sparkles", "rocket", "bulb", "target", "trending",
    "star", "zap", "check", "users", "book", "heart", "globe",
]


def split_sentences(text):
    """按中英文句末标点 + 换行切句。"""
    parts = re.split(r"(?<=[。！？!?；;…\n])", text)
    return [p.strip().replace("\n", " ") for p in parts if p and p.strip()]


def split_scenes(text):
    """按行切分（用户常用单行分隔要点），过短行并入上一行；超长段再按句切，每段 ~50 字。"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # 合并过短的行到上一行（避免孤字/标点单独成屏）
    merged = []
    for l in lines:
        if merged and len(l) <= 3:
            merged[-1] = merged[-1] + l
        else:
            merged.append(l)
    scenes = []
    for p in merged:
        if len(p) <= 60:
            scenes.append(p)
            continue
        subs = split_sentences(p)
        buf = ""
        for s in subs:
            if len(buf) + len(s) > 50:
                if buf:
                    scenes.append(buf.strip())
                buf = s
            else:
                buf += s
        if buf.strip():
            scenes.append(buf.strip())
    return scenes


def pick_icon(text):
    for icon, kws in ICON_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in text.lower():
                return icon
    return None


def build_scenes(text, override_title):
    raw = split_scenes(text)
    scenes = []
    if override_title:
        scenes.append({"kind": "title", "title": override_title, "icon": pick_icon(override_title)})
        for s in raw:
            scenes.append({"kind": "body", "body": s, "icon": pick_icon(s)})
    else:
        for i, s in enumerate(raw):
            if i == 0 and len(s) <= 16:
                scenes.append({"kind": "title", "title": s, "icon": pick_icon(s)})
            elif len(s) <= 10 and not re.search(r"[。！？!?；;]", s):
                scenes.append({"kind": "title", "title": s, "icon": pick_icon(s)})
            else:
                scenes.append({"kind": "body", "body": s, "icon": pick_icon(s)})
    return scenes


def ts_str(s):
    return json.dumps(s, ensure_ascii=False)


def write_scenes(path, scenes):
    lines = [
        "// 自动生成，请勿手动修改（由 generate_video.py 写入）。",
        "export interface SceneData {",
        '  kind: "title" | "body";',
        "  title?: string;",
        "  body?: string;",
        "  icon?: string;",
        "}",
        "",
        "export const scenes: SceneData[] = [",
    ]
    for s in scenes:
        parts = [f'  {{ kind: "{s["kind"]}"']
        if s.get("title"):
            parts.append(f', title: {ts_str(s["title"])}')
        if s.get("body"):
            parts.append(f', body: {ts_str(s["body"])}')
        if s.get("icon"):
            parts.append(f', icon: {ts_str(s["icon"])}')
        parts.append(" },")
        lines.append("".join(parts))
    lines.append("];")
    open(path, "w", encoding="utf-8").write("\n".join(lines))


def write_config(path, aspect, style, scene_seconds, scene_durations=None):
    w, h = ASPECTS.get(aspect, ASPECTS["9:16"])
    content = (
        "// 自动生成，请勿手动修改（由 generate_video.py 写入）。\n"
        f"export const ASPECT = {json.dumps(aspect)};\n"
        f"export const WIDTH = {w};\n"
        f"export const HEIGHT = {h};\n"
        "export const FPS = 30;\n"
        f"export const SCENE_SECONDS = {scene_seconds};\n"
    )
    if scene_durations:
        content += f"export const SCENE_DURATIONS: number[] = {json.dumps(scene_durations)};\n"
    else:
        content += "export const SCENE_DURATIONS: number[] = [];\n"
    content += f"export const STYLE = {json.dumps(style)};\n"
    open(path, "w", encoding="utf-8").write(content)


def compute_scene_durations(scenes, audio_dur, fps):
    """按每屏字数比例分配时长，使画面总时长 ≈ 配音时长（音画同步核心）。

    - 过场（每屏末尾淡出）由 SceneCard 在 durationInFrames 内部处理，这里只管总时长对齐。
    - 首屏标题卡给一个下限，避免一闪而过。
    - 末尾把取整误差补到最长的一屏，保证 Σ ≈ audio_dur。
    """
    n = len(scenes)
    if n == 0 or audio_dur <= 0:
        return None
    total_frames = int(round(audio_dur * fps))
    weights = []
    for s in scenes:
        txt = (s.get("title") or s.get("body") or "")
        weights.append(max(1, len(txt)))
    total_w = sum(weights) or 1
    frames = []
    for w in weights:
        f = int(round(total_frames * w / total_w))
        frames.append(max(f, 75))  # 每屏至少 2.5s（75 帧@30fps），过场 16 帧只占约 1/5
    # 修正常量误差
    diff = total_frames - sum(frames)
    if frames and diff != 0:
        idx = frames.index(max(frames))
        frames[idx] = max(75, frames[idx] + diff)
    return [round(f / fps, 2) for f in frames]


def find_node():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from paths import detect_paths
        nb = detect_paths().get("node_bin")
        if nb and os.path.isfile(os.path.join(nb, "node.exe")):
            return nb
    except Exception:
        pass
    import shutil
    nw = shutil.which("node")
    if nw:
        return os.path.dirname(nw)
    return ""


def stream(cmd, cwd, env, prefix=""):
    """实时把子进程输出打到 stdout（供 GUI 流式日志）。"""
    p = subprocess.Popen(
        cmd, cwd=cwd, env=env, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
    )
    for line in p.stdout:
        print(prefix + line.rstrip(), flush=True)
    p.wait()
    return p.returncode


def run_render(project, out_video, node_bin):
    env = dict(os.environ)
    if node_bin:
        env["PATH"] = node_bin + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    npm = "npm"
    if node_bin and os.path.isfile(os.path.join(node_bin, "npm.cmd")):
        npm = os.path.join(node_bin, "npm.cmd")

    if not os.path.isdir(os.path.join(project, "node_modules")):
        print("[*] 安装依赖 (npm install) ...", flush=True)
        rc = stream(f'"{npm}" install', cwd=project, env=env, prefix="   ")
        if rc != 0:
            raise RuntimeError("npm install 失败（返回码 %d）" % rc)

    print("[*] 渲染视频 (npx remotion render) ...", flush=True)
    os.makedirs(os.path.dirname(out_video), exist_ok=True)
    cmd = f'npx remotion render src/index.ts TextToVideo "{out_video}"'
    rc = stream(cmd, cwd=project, env=env, prefix="   ")
    if rc != 0 or not os.path.isfile(out_video):
        raise RuntimeError("渲染失败（返回码 %d）" % rc)


def write_render_guide(project, out_video):
    guide = (
        "本工程已生成，但视频渲染未成功完成（可能是缺少 Node 或网络无法下载依赖/Chromium）。\n\n"
        "手动渲染步骤：\n"
        "1. 安装 Node.js 18+ 并加入 PATH。\n"
        "2. 在该工程目录执行：\n"
        "     cd <工程目录>\n"
        "     npm install\n"
        "     npx remotion render src/index.ts TextToVideo out/video.mp4\n"
        "3. 把 out/video.mp4 用作『加入语音字幕』步骤的原视频即可。\n\n"
        f"工程目录：{project}\n"
    )
    gpath = os.path.join(project, "渲染指引.txt")
    open(gpath, "w", encoding="utf-8").write(guide)
    print(f"RENDER_GUIDE={gpath}", flush=True)


def sanitize(name):
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name).strip()
    name = name[:30].strip() or "文案视频"
    return name


def main():
    ap = argparse.ArgumentParser(description="文案 → Remotion 画面视频")
    ap.add_argument("--text", required=True, help="文案文件路径（UTF-8，内容即视频画面+口播稿）")
    ap.add_argument("--out-dir", required=True, help="输出根目录（工程与视频放这里）")
    ap.add_argument("--name", default="", help="视频名（用于工程/文件名，留空自动取首行）")
    ap.add_argument("--aspect", default="9:16", help="比例：9:16 / 16:9 / 3:4")
    ap.add_argument("--style", default="dark", help="风格：dark / light / brand")
    ap.add_argument("--scene-seconds", type=float, default=5, help="每屏时长（秒，未提供配音时长时使用）")
    ap.add_argument("--title", default="", help="可选总标题（覆盖首屏为标题卡）")
    ap.add_argument("--audio-path", default="", help="配音 mp3 路径：若提供，画面每屏时长按配音时长适配（音画同步）")
    ap.add_argument("--audio-duration", type=float, default=0, help="配音时长（秒）：直接指定，效果同 --audio-path")
    args = ap.parse_args()

    text_path = os.path.abspath(args.text)
    if not os.path.isfile(text_path):
        sys.exit(f"[!] 文案文件不存在：{text_path}")
    raw = read_text(text_path).strip()
    if not raw:
        sys.exit(f"[!] 文案为空：{text_path}")

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    first_line = raw.split("\n", 1)[0].strip()[:30]
    name = args.name or sanitize(first_line)
    project = os.path.join(out_dir, name + "_remotion")

    if os.path.exists(project):
        shutil.rmtree(project)

    print(f"[start] 文案：{text_path}（{len(raw)} 字）", flush=True)
    print(f"        比例={args.aspect}  风格={args.style}  每屏={args.scene_seconds}s", flush=True)

    # 确定配音时长（用于画面适配，实现音画同步）
    audio_dur = 0.0
    if args.audio_duration and args.audio_duration > 0:
        audio_dur = float(args.audio_duration)
    elif args.audio_path and os.path.isfile(args.audio_path):
        try:
            from paths import detect_paths
            fp_bin = detect_paths().get("ffprobe_bin")
            if fp_bin and os.path.isfile(os.path.join(fp_bin, "ffprobe.exe")):
                d = subprocess.check_output(
                    [os.path.join(fp_bin, "ffprobe.exe"), "-v", "error",
                     "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", args.audio_path],
                    encoding="utf-8", errors="replace",
                ).strip()
                if d:
                    audio_dur = float(d)
        except Exception as e:
            print(f"[warn] 读取配音时长失败，按固定每屏时长渲染：{e}", flush=True)
    if audio_dur > 0:
        print(f"        🔊 配音时长 {audio_dur:.1f}s → 画面将按此适配（音画同步）", flush=True)

    # 拷贝模板
    shutil.copytree(TEMPLATE, project)
    print(f"[ok] 已复制模板到：{project}", flush=True)

    # 写配置 + 场景
    scenes = build_scenes(raw, args.title)
    # 关键词未命中时按索引轮转默认图标，保证每屏都有视觉元素
    for i, sc in enumerate(scenes):
        if not sc.get("icon"):
            sc["icon"] = DEFAULT_ICONS[i % len(DEFAULT_ICONS)]
    scene_durations = None
    if audio_dur > 0:
        scene_durations = compute_scene_durations(scenes, audio_dur, 30)
        if scene_durations:
            print(f"        画面每屏时长（按字数比例）：{scene_durations}", flush=True)
    write_config(os.path.join(project, "src", "config.ts"), args.aspect, args.style, args.scene_seconds, scene_durations)
    write_scenes(os.path.join(project, "src", "scenes-data.ts"), scenes)
    print(f"[ok] 已写入 {len(scenes)} 个场景到 scenes-data.ts", flush=True)

    out_video = os.path.join(out_dir, name + "_画面.mp4")
    node_bin = find_node()
    if not node_bin:
        print("[!] 未找到 Node.js，跳过渲染。已交付工程，请安装 Node 18+ 后手动渲染。", flush=True)
        write_render_guide(project, out_video)
        sys.exit(2)

    print(f"[info] 使用 Node：{node_bin}", flush=True)
    try:
        run_render(project, out_video, node_bin)
    except Exception as e:
        print(f"[!] 渲染失败：{e}", flush=True)
        write_render_guide(project, out_video)
        sys.exit(1)

    print(f"RENDERED_VIDEO={out_video}", flush=True)
    print(f"[完成] 画面视频已生成：{out_video}", flush=True)


if __name__ == "__main__":
    main()
