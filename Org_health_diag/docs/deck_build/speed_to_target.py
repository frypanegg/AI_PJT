# -*- coding: utf-8 -*-
"""녹화본을 목표 길이에 맞춰 배속 조정한다.

원본 길이를 재서 필요한 배속을 역산하므로, 녹화 시간이 회차마다 달라져도
결과 길이는 항상 목표에 맞는다 (LLM 응답 대기가 매번 다르기 때문).
"""

import os
import re
import subprocess
import sys

import imageio_ffmpeg

SRC = (r"C:\Users\admin\Desktop\AI 활용 전문가\프로젝트과제"
       r"\Org_health_diag\docs\demo\2026_조직건강도_AI_Agent_시연.mp4")
OUT = (r"C:\Users\admin\Desktop\AI 활용 전문가\프로젝트과제"
       r"\Org_health_diag\docs\demo\2026_조직건강도_AI_Agent_시연_2min.mp4")
TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0

ff = imageio_ffmpeg.get_ffmpeg_exe()

probe = subprocess.run([ff, "-i", SRC], capture_output=True, text=True)
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe.stderr)
h, mm, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
dur = h * 3600 + mm * 60 + s
speed = dur / TARGET

print(f"원본 길이 : {dur:.1f}초")
print(f"목표 길이 : {TARGET:.0f}초")
print(f"필요 배속 : {speed:.3f}x")

cmd = [ff, "-y", "-i", SRC,
       "-vf", f"setpts=PTS/{speed:.5f},format=yuv420p",
       "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
       "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

probe2 = subprocess.run([ff, "-i", OUT], capture_output=True, text=True)
m2 = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe2.stderr)
h2, mm2, s2 = int(m2.group(1)), int(m2.group(2)), float(m2.group(3))
print(f"\n결과 길이 : {h2*3600+mm2*60+s2:.1f}초")
print(f"파일      : {OUT}  ({os.path.getsize(OUT)/1e6:.1f}MB)")
