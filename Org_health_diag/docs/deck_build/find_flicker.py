# -*- coding: utf-8 -*-
"""영상의 깜빡임(순간적인 밝기 급변)을 찾아낸다.

눈으로 훑으면 놓치기 쉬우므로, 프레임을 촘촘히 뽑아 평균 밝기를 재고
'어두워졌다가 곧바로 밝아지는' 구간과 '밝았다가 곧바로 어두워지는' 구간을
자동으로 집어낸다.
"""

import os
import shutil
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image

SRC = sys.argv[1]
FPS = 12
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_flick")

ff = imageio_ffmpeg.get_ffmpeg_exe()
if os.path.exists(TMP):
    shutil.rmtree(TMP)
os.makedirs(TMP)

subprocess.run(
    [ff, "-y", "-i", SRC, "-vf", f"fps={FPS},scale=64:36", f"{TMP}/f%05d.png",
     "-loglevel", "error"],
    check=True,
)

files = sorted(os.listdir(TMP))
lum = []
for f in files:
    im = Image.open(os.path.join(TMP, f)).convert("L")
    px = list(im.getdata())
    lum.append(sum(px) / len(px))

print(f"프레임 {len(lum)}개 ({FPS}fps, {len(lum)/FPS:.1f}초)")


def t(i):
    return i / FPS


# 1) 급격한 변화 지점
JUMP = 28  # 0~255 기준
jumps = []
for i in range(1, len(lum)):
    d = lum[i] - lum[i - 1]
    if abs(d) >= JUMP:
        jumps.append((i, d))

# 2) 깜빡임 = 짧은 구간 안에서 반대 방향 변화가 되돌아오는 것
print(f"\n=== 급변 지점 {len(jumps)}건 (|Δ| >= {JUMP}) ===")
flicks = []
for a in range(len(jumps) - 1):
    i1, d1 = jumps[a]
    for b in range(a + 1, len(jumps)):
        i2, d2 = jumps[b]
        gap = t(i2) - t(i1)
        if gap > 1.2:
            break
        if d1 * d2 < 0 and abs(d1) > JUMP and abs(d2) > JUMP:
            flicks.append((t(i1), t(i2), gap, d1, d2))
            break

# 중복 제거
merged = []
for f in flicks:
    if merged and f[0] - merged[-1][0] < 0.6:
        continue
    merged.append(f)

print(f"\n=== 깜빡임 후보 {len(merged)}건 (1.2초 이내 왕복) ===")
for s, e, gap, d1, d2 in merged:
    kind = "어두워졌다 복귀" if d1 < 0 else "밝아졌다 복귀"
    print(f"  {s:6.2f}s → {e:6.2f}s  ({gap:.2f}초, {kind}, Δ{d1:+.0f}/{d2:+.0f})")

# 3) 완전 검정 구간
BLACK = 18
runs, st = [], None
for i, v in enumerate(lum):
    if v < BLACK and st is None:
        st = i
    elif v >= BLACK and st is not None:
        if t(i) - t(st) >= 0.15:
            runs.append((t(st), t(i)))
        st = None
if st is not None:
    runs.append((t(st), t(len(lum))))
print(f"\n=== 검정 구간 {len(runs)}건 (0.15초 이상) ===")
for s, e in runs:
    print(f"  {s:6.2f}s → {e:6.2f}s  ({e-s:.2f}초)")

shutil.rmtree(TMP, ignore_errors=True)
