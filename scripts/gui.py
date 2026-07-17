#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文案转口播视频 · 图形界面（tkinter）
====================================
把"文案 → Remotion 画面视频 → 加配音字幕口播版"做成双击可用的窗口。

流程（两步走，可一键全流程）：
  ① 生成画面视频：文案 → 数据驱动 Remotion 工程 → 渲染 MP4（无声/带BGM，每屏固定时长）。
  ② 加入语音字幕：给已生成的画面配音 + 烧字幕（时长按配音对齐，末屏冻结兜底）。
  ③ 一键全流程（推荐·音画同步）：先配音拿时长 → 画面每屏时长按配音适配 → 合成口播版。
     文字多的屏停留更久，配音与画面节奏一致，不再"声音还在念、画面已切走"。

模仿 video-voiceover-chatcut 的界面与防闪退要点：入口 UTF-8 重配置；顶层 try/except
弹窗报错；重活放后台线程；UI 线程安全更新日志。
"""
import sys, os, re, threading, tempfile, subprocess, tkinter as tk
from paths import detect_paths, read_text
from tkinter import filedialog, messagebox, ttk, scrolledtext

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SKILL_DIR, "scripts")
DEFAULTS = detect_paths()

VOICES = [
    ("晓晓（女·温柔知性）", "zh-CN-XiaoxiaoNeural"),
    ("晓伊（女·亲切活泼）", "zh-CN-XiaoyiNeural"),
    ("云希（男·阳光少年）", "zh-CN-YunxiNeural"),
    ("云扬（男·沉稳新闻）", "zh-CN-YunyangNeural"),
    ("云健（男·运动激昂）", "zh-CN-YunjianNeural"),
    ("辽宁·小贝（女·东北话）", "zh-CN-liaoning-XiaobeiNeural"),
    ("陕西·小妮（女·陕西方言）", "zh-CN-shaanxi-XiaoniNeural"),
    ("台湾·小玉（女·台湾腔）", "zh-TW-HsiaoYuNeural"),
]

ASPECTS = [
    ("抖音竖屏 9:16", "9:16"),
    ("YouTube 横屏 16:9", "16:9"),
    ("小红书 3:4", "3:4"),
]

STYLES = [
    ("科技暗色", "dark"),
    ("简约亮色", "light"),
    ("品牌蓝", "brand"),
]


def sanitize_name(name):
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name).strip()
    return name[:30].strip() or "文案视频"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("文案转口播视频  (text-to-voiceover-video)")
        self.root.geometry("800x680")
        try:
            self.root.iconbitmap()
        except Exception:
            pass

        self.text_path = tk.StringVar()
        self.text_pasted = ""
        self.out_dir = tk.StringVar()
        self.aspect_var = tk.StringVar(value=ASPECTS[0][0])
        self.style_var = tk.StringVar(value=STYLES[0][0])
        self.scene_var = tk.DoubleVar(value=5.0)
        self.scene_label = tk.StringVar(value="5.0s")
        self.voice_var = tk.StringVar(value=VOICES[0][0])
        self.speed_var = tk.DoubleVar(value=1.3)
        self.speed_label = tk.StringVar(value="1.3x")

        self.remotion_video = None   # ① 生成的画面视频
        self.name = "文案视频"
        self.busy = False

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        f = ttk.Frame(self.root, padding=10)
        f.pack(fill="both", expand=True)

        row = 0
        ttk.Label(f, text="① 文案（口播稿，也是视频画面文字）：").grid(row=row, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.text_path, width=54).grid(row=row, column=1, sticky="we")
        ttk.Button(f, text="选文件…", command=self.pick_textfile).grid(row=row, column=2, padx=2)
        ttk.Button(f, text="粘贴…", command=self.paste_text).grid(row=row, column=3, padx=2)
        row += 1

        ttk.Label(f, text="② 视频比例：").grid(row=row, column=0, sticky="w")
        cb = ttk.Combobox(f, textvariable=self.aspect_var, width=22, state="readonly")
        cb["values"] = [a[0] for a in ASPECTS]
        cb.grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(f, text="③ 视觉风格：").grid(row=row, column=0, sticky="w")
        cb2 = ttk.Combobox(f, textvariable=self.style_var, width=22, state="readonly")
        cb2["values"] = [s[0] for s in STYLES]
        cb2.grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(f, text="④ 每屏时长：").grid(row=row, column=0, sticky="w")
        sl = ttk.Scale(f, from_=3, to=8, variable=self.scene_var, orient="horizontal",
                       length=220, command=self._on_scene)
        sl.grid(row=row, column=1, sticky="w")
        ttk.Label(f, textvariable=self.scene_label, width=8).grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(f, text="⑤ 播音人：").grid(row=row, column=0, sticky="w")
        cb3 = ttk.Combobox(f, textvariable=self.voice_var, width=30, state="readonly")
        cb3["values"] = [v[0] for v in VOICES]
        cb3.grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(f, text="⑥ 语速：").grid(row=row, column=0, sticky="w")
        sl2 = ttk.Scale(f, from_=0.8, to=2.0, variable=self.speed_var, orient="horizontal",
                        length=220, command=self._on_speed)
        sl2.grid(row=row, column=1, sticky="w")
        ttk.Label(f, textvariable=self.speed_label, width=8).grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(f, text="⑦ 输出目录：").grid(row=row, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.out_dir, width=54).grid(row=row, column=1, sticky="we")
        ttk.Button(f, text="浏览…", command=self.pick_outdir).grid(row=row, column=2, padx=2)
        row += 1

        bf = ttk.Frame(f)
        bf.grid(row=row, column=0, columnspan=4, sticky="w", pady=8)
        self.btn_gen = ttk.Button(bf, text="▶ ① 生成画面视频", command=self.on_generate, width=20)
        self.btn_gen.pack(side="left", padx=3)
        self.btn_merge = ttk.Button(bf, text="▶ ② 加入语音字幕", command=self.on_voiceover, width=20)
        self.btn_merge.pack(side="left", padx=3)
        self.btn_full = ttk.Button(bf, text="▶ ③ 一键全流程", command=self.on_full, width=18)
        self.btn_full.pack(side="left", padx=3)
        row += 1

        ttk.Label(f, text="运行日志：").grid(row=row, column=0, sticky="w", pady=(4, 0))
        row += 1
        self.log = scrolledtext.ScrolledText(f, height=20, wrap="word")
        self.log.grid(row=row, column=0, columnspan=4, sticky="nsew")
        f.rowconfigure(row, weight=1)
        f.columnconfigure(1, weight=1)

    def _on_scene(self, *_):
        self.scene_label.set(f"{self.scene_var.get():.1f}s")

    def _on_speed(self, *_):
        self.speed_label.set(f"{self.speed_var.get():.1f}x")

    # ---------- 选择 ----------
    def pick_textfile(self):
        p = filedialog.askopenfilename(title="选择文案 txt",
                                       filetypes=[("文本", "*.txt *.md"), ("全部", "*.*")])
        if p:
            self.text_path.set(p)
            self.text_pasted = ""
            d = os.path.dirname(p)
            if not self.out_dir.get():
                self.out_dir.set(d)

    def pick_outdir(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.out_dir.set(d)

    def paste_text(self):
        win = tk.Toplevel(self.root)
        win.title("粘贴文案")
        win.geometry("560x360")
        st = scrolledtext.ScrolledText(win, wrap="word")
        st.insert("1.0", self.text_pasted)
        st.pack(fill="both", expand=True, padx=8, pady=8)
        bb = ttk.Frame(win); bb.pack(pady=6)

        def ok():
            self.text_pasted = st.get("1.0", "end").strip()
            if self.text_pasted:
                d = self.out_dir.get() or tempfile.gettempdir()
                tp = os.path.join(d, "_文案.txt")
                open(tp, "w", encoding="utf-8").write(self.text_pasted)
                self.text_path.set(tp)
                self.log_ui(f"[ok] 已用粘贴文本（{len(self.text_pasted)} 字）")
            win.destroy()

        ttk.Button(bb, text="确定", command=ok).pack(side="left", padx=8)
        ttk.Button(bb, text="取消", command=win.destroy).pack(side="left", padx=8)

    # ---------- 校验/取值 ----------
    def _validate(self):
        if not self.text_path.get() or not os.path.exists(self.text_path.get()):
            messagebox.showerror("缺文案", "请先选择或粘贴文案文本。")
            return False
        if not self.out_dir.get():
            self.out_dir.set(tempfile.gettempdir())
        return True

    def _aspect(self):
        for label, val in ASPECTS:
            if label == self.aspect_var.get():
                return val
        return ASPECTS[0][1]

    def _style(self):
        for label, val in STYLES:
            if label == self.style_var.get():
                return val
        return STYLES[0][1]

    def _voice_id(self):
        for name, vid in VOICES:
            if name == self.voice_var.get():
                return vid
        return VOICES[0][1]

    def _derive_name(self):
        raw = read_text(self.text_path.get())
        first = raw.split("\n", 1)[0].strip()[:30]
        self.name = sanitize_name(first)

    # ---------- 线程包装 ----------
    def _run_thread(self, target, btn_enable=True):
        if self.busy:
            return
        self.busy = True
        for b in (self.btn_gen, self.btn_merge, self.btn_full):
            b.config(state="disabled")
        threading.Thread(target=self._wrap, args=(target, btn_enable), daemon=True).start()

    def _wrap(self, target, btn_enable):
        try:
            target()
        except Exception as e:
            self.log_ui(f"[错误] {e}")
            self.root.after(0, lambda: messagebox.showerror("运行出错", str(e)))
        finally:
            self.busy = False
            if btn_enable:
                self.root.after(0, self._enable_buttons)

    def _enable_buttons(self):
        for b in (self.btn_gen, self.btn_merge, self.btn_full):
            b.config(state="normal")

    def log_ui(self, msg):
        self.root.after(0, lambda: self._append(msg))

    def _append(self, msg):
        self.log.insert("end", str(msg).rstrip() + "\n")
        self.log.see("end")

    def _run_capture(self, cmd, env, cwd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             encoding="utf-8", errors="replace", env=env, cwd=cwd)
        for line in p.stdout:
            self.log_ui(line.rstrip())
        p.wait()
        if p.returncode != 0:
            raise RuntimeError(f"步骤失败（返回码 {p.returncode}）")
        return p.returncode

    def _env(self):
        env = dict(os.environ)
        ff = DEFAULTS.get("ffmpeg_bin")
        if ff:
            env["PATH"] = ff + os.pathsep + env.get("PATH", "")
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    # ---------- ① 生成画面视频 ----------
    def on_generate(self):
        if not self._validate():
            return
        self._run_thread(self._do_generate)

    def _do_generate(self):
        self._derive_name()
        txt = self.text_path.get()
        out_dir = os.path.abspath(self.out_dir.get())
        os.makedirs(out_dir, exist_ok=True)
        remotion_video = os.path.join(out_dir, self.name + "_画面.mp4")
        self.log_ui(f"[开始] ① 生成画面视频 → {remotion_video}")
        self.log_ui(f"       比例={self._aspect()}  风格={self._style()}  每屏={self.scene_var.get():.1f}s")

        env = self._env()
        gen = os.path.join(SCRIPTS, "generate_video.py")
        self._run_capture([
            DEFAULTS["venv_py"], gen,
            "--text", txt,
            "--out-dir", out_dir,
            "--name", self.name,
            "--aspect", self._aspect(),
            "--style", self._style(),
            "--scene-seconds", str(self.scene_var.get()),
        ], env, out_dir)

        if os.path.isfile(remotion_video):
            self.remotion_video = remotion_video
            self.log_ui(f"[完成] 画面视频已生成：{remotion_video}")
            self.log_ui(f"        下一步点『② 加入语音字幕』生成口播版")
        else:
            self.log_ui("[!] 画面视频未生成（渲染失败或缺少 Node）。")
            self.log_ui("    已交付 Remotion 工程，可手动渲染后重试第②步。")
            self.remotion_video = None

    # ---------- ② 加入语音字幕（口播版） ----------
    def on_voiceover(self):
        if not self._validate():
            return
        # 若还没生成画面视频，先生成
        if not (self.remotion_video and os.path.exists(self.remotion_video)):
            self.log_ui("[提示] 尚未生成画面视频，先执行①……")
            self._do_generate()
            if not (self.remotion_video and os.path.exists(self.remotion_video)):
                raise RuntimeError("画面视频未生成，无法加入语音字幕。")
        self._run_thread(self._do_voiceover, btn_enable=False)

    def _do_voiceover(self):
        txt = self.text_path.get()
        out_dir = os.path.abspath(self.out_dir.get())
        remotion_video = self.remotion_video
        workdir = os.path.join(out_dir, self.name + "_narration")
        os.makedirs(workdir, exist_ok=True)
        mp3 = os.path.join(workdir, "narration.mp3")
        final = os.path.join(out_dir, self.name + "_口播版.mp4")

        # 2.1 生成配音
        self.log_ui(f"[开始] 生成配音 → {mp3}")
        env = self._env()
        self._run_capture([
            DEFAULTS["venv_py"], os.path.join(SCRIPTS, "make_narration.py"),
            "--text", txt,
            "--output", mp3,
            "--voice", self._voice_id(),
            "--speed", str(self.speed_var.get()),
        ], env, workdir)

        # 2.2 合成口播版
        self.log_ui(f"[开始] 合成口播版 → {final}")
        self._run_capture([
            DEFAULTS["venv_py"], os.path.join(SCRIPTS, "merge_local.py"),
            "--original", remotion_video,
            "--audio", mp3,
            "--text", txt,
            "--output", final,
        ], env, out_dir)

        self.log_ui(f"[完成] 口播视频已生成：{final}")
        self.root.after(0, lambda: messagebox.showinfo("完成", f"口播视频已生成：\n{final}"))

    # ---------- ③ 一键全流程（音画同步模式） ----------
    def on_full(self):
        if not self._validate():
            return
        self._run_thread(self._do_full, btn_enable=False)

    def _do_full(self):
        """音画同步最佳路径：先生成配音拿到时长 → 画面按配音时长适配 → 合成。

        这样画面每屏停留时间 = 该屏文字量 ∝ 配音念到该屏的时长，彻底解决
        '声音还在念上一段、画面已切到下一段' 的不同步问题。
        """
        self._derive_name()
        txt = self.text_path.get()
        out_dir = os.path.abspath(self.out_dir.get())
        os.makedirs(out_dir, exist_ok=True)
        remotion_video = os.path.join(out_dir, self.name + "_画面.mp4")
        workdir = os.path.join(out_dir, self.name + "_narration")
        os.makedirs(workdir, exist_ok=True)
        mp3 = os.path.join(workdir, "narration.mp3")
        final = os.path.join(out_dir, self.name + "_口播版.mp4")
        env = self._env()

        self.log_ui("===== 一键全流程（音画同步模式）=====")

        # 步骤1：配音
        self.log_ui("【步骤1/3】生成配音（edge-tts）……")
        self._run_capture([
            DEFAULTS["venv_py"], os.path.join(SCRIPTS, "make_narration.py"),
            "--text", txt, "--output", mp3,
            "--voice", self._voice_id(), "--speed", str(self.speed_var.get()),
        ], env, workdir)
        if not os.path.isfile(mp3):
            raise RuntimeError("配音未生成，流程中止。请查看上方日志。")
        self.log_ui(f"        配音：{mp3}")

        # 步骤2：画面（按配音时长适配）
        self.log_ui("【步骤2/3】生成画面视频（按配音时长适配，保证音画同步）……")
        self.log_ui(f"       比例={self._aspect()}  风格={self._style()}")
        self._run_capture([
            DEFAULTS["venv_py"], os.path.join(SCRIPTS, "generate_video.py"),
            "--text", txt, "--out-dir", out_dir, "--name", self.name,
            "--aspect", self._aspect(), "--style", self._style(),
            "--scene-seconds", str(self.scene_var.get()),
            "--audio-path", mp3,
        ], env, out_dir)
        if not os.path.isfile(remotion_video):
            raise RuntimeError("画面视频未生成，流程中止。请查看上方日志。")
        self.remotion_video = remotion_video
        self.log_ui(f"        画面：{remotion_video}")

        # 步骤3：合成
        self.log_ui("【步骤3/3】合成口播版（配音+字幕，时长对齐）……")
        self._run_capture([
            DEFAULTS["venv_py"], os.path.join(SCRIPTS, "merge_local.py"),
            "--original", remotion_video, "--audio", mp3,
            "--text", txt, "--output", final,
        ], env, out_dir)

        self.log_ui(f"[完成] 音画同步口播视频已生成：{final}")
        self.root.after(0, lambda: messagebox.showinfo("完成", f"音画同步口播视频已生成：\n{final}"))
        self.log_ui("===== 一键全流程结束 =====")


def main():
    try:
        import subprocess  # noqa
        root = tk.Tk()
        py = DEFAULTS.get("venv_py", "")
        if not py or not os.path.isfile(py):
            import shutil
            py = shutil.which("python") or shutil.which("python3") or ""
        try:
            import edge_tts
            has_edge = True
        except ImportError:
            has_edge = False

        warnings = []
        if not has_edge:
            warnings.append("• 缺少 edge_tts 库 → 请双击『安装依赖.bat』安装")
        ff = DEFAULTS.get("ffmpeg_bin", "")
        if not ff or not os.path.isfile(os.path.join(ff, "ffmpeg.exe")):
            warnings.append("• 缺少 ffmpeg → 请安装并加入 PATH")
        nb = DEFAULTS.get("node_bin", "")
        if not nb:
            warnings.append("• 未检测到 Node.js → 第①步渲染需要 Node 18+（WorkBuddy 托管 Node 或自行安装）")

        if warnings:
            messagebox.showwarning(
                "部分依赖缺失",
                "以下依赖暂时缺少，不影响基本使用（运行时再提示）：\n\n"
                + "\n".join(warnings)
                + "\n\n建议双击『安装依赖.bat』一键安装（ffmpeg/Node 需另行准备）。")

        App(root)
        root.mainloop()
    except Exception as e:
        try:
            messagebox.showerror("启动失败", str(e))
        except Exception:
            pass
        try:
            open(os.path.join(tempfile.gettempdir(), "text_to_voiceover_gui_error.log"),
                 "w", encoding="utf-8").write(repr(e))
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
