#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text-to-voiceover-video 一键安装依赖（给朋友用）
================================================
做两件事：
  1. 建虚拟环境  ~/.workbuddy/binaries/python/envs/default（若尚未存在）
  2. 装 edge_tts（清华镜像，国内快）——第②步配音所必需

注意：
  · ffmpeg（第②步本地合成所必需）不在本脚本内下载，请自行安装并加入 PATH，
    或放到 %USERPROFILE%/bin/ffmpeg/ffmpeg-*/bin。
  · Node.js（第①步 Remotion 渲染所必需）由 WorkBuddy 托管 Node 提供；
    若换机器自行安装 Node 18+ 并加入 PATH。
"""
import os
import sys
import shutil
import subprocess


home = os.path.expanduser("~")
venv = os.path.join(home, ".workbuddy", "binaries", "python", "envs", "default")
py = os.path.join(venv, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv, "bin", "python")


def run(msg, cmd):
    print(f"[*] {msg} ...", flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"[!] {msg} 失败（返回码 {r.returncode}）")
        sys.exit(1)


# 1. 建 venv（若尚未存在）
if not os.path.exists(py):
    print(f"[*] 创建虚拟环境：{venv}", flush=True)
    base = sys.executable
    r = subprocess.run([base, "-m", "venv", venv])
    if r.returncode != 0:
        alt = shutil.which("python") or shutil.which("python3")
        if alt:
            r = subprocess.run([alt, "-m", "venv", venv])
        if r.returncode != 0:
            print("[!] 无法创建虚拟环境，请先安装 Python 3.11+。")
            sys.exit(1)

# 2. 装 edge_tts
run("安装 edge_tts（清华镜像）",
    [py, "-m", "pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "edge_tts"])

print("\n[完成] Python 依赖已安装（edge_tts）。", flush=True)
print("    仍需自行准备：ffmpeg（合成必需）、Node.js 18+（渲染必需，WorkBuddy 已自带）。", flush=True)
