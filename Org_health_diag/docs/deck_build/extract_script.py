# -*- coding: utf-8 -*-
"""시연 영상 시나리오에서 화면에 보이는 텍스트만 뽑아 편집용 TXT를 만든다.

record_demo.py를 ast로 파싱해 cover/say/chip/type_text 호출을 소스 순서대로 훑는다.
편집분을 되돌려 넣을 수 있도록 각 항목의 (줄번호, 인자명)을 JSON에 함께 남긴다.
"""

import ast
import io
import json
import os
import re

SRC = (r"C:\Users\admin\Desktop\AI 활용 전문가\프로젝트과제"
       r"\Org_health_diag\docs\demo\record_demo.py")
OUT_TXT = (r"C:\Users\admin\Desktop\AI 활용 전문가\프로젝트과제"
           r"\Org_health_diag\docs\demo\영상_스크립트.txt")
OUT_MAP = (r"C:\Users\admin\AppData\Local\Temp\claude"
           r"\C--Users-admin-Desktop-AI--------------"
           r"\51175629-3fba-444a-a3f3-2fe3dfc78b5a\scratchpad\script_map.json")

source = open(SRC, encoding="utf-8").read()
lines = source.splitlines()
tree = ast.parse(source)

# 소스의 섹션 주석(# ===== ... =====)을 줄번호와 함께 수집
sections = {}
for i, ln in enumerate(lines, start=1):
    m = re.match(r"\s*#\s*=====\s*(.+?)\s*=====\s*$", ln)
    if m:
        sections[i] = m.group(1)

KIND_LABEL = {
    "kicker": "커버·상단라벨",
    "no": "커버·큰번호",
    "title": "커버·제목",
    "sub": "커버·부제",
    "meta": "커버·하단",
    "say": "자막",
    "chip": "챕터라벨",
    "type": "입력문구",
}

entries = []


def const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


run_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")

for node in ast.walk(run_fn):
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        continue
    fn = node.func.id
    ln = node.lineno

    if fn == "cover":
        for kw in node.keywords:
            if kw.arg in ("kicker", "no", "title", "sub", "meta"):
                v = const_str(kw.value)
                if v:
                    entries.append({"lineno": ln, "field": kw.arg,
                                    "kind": kw.arg, "text": v})
    elif fn == "say":
        if node.args and len(node.args) >= 2:
            v = const_str(node.args[1])
            if v:
                entries.append({"lineno": ln, "field": "arg1",
                                "kind": "say", "text": v})
    elif fn == "chip":
        if len(node.args) >= 3:
            v = const_str(node.args[2])
            if v:
                entries.append({"lineno": ln, "field": "arg2",
                                "kind": "chip", "text": v})
    elif fn == "type_text":
        if len(node.args) >= 3:
            v = const_str(node.args[2])
            if v:
                entries.append({"lineno": ln, "field": "arg2",
                                "kind": "type", "text": v})

entries.sort(key=lambda e: (e["lineno"], list(KIND_LABEL).index(e["kind"])))
for i, e in enumerate(entries, start=1):
    e["id"] = f"{i:03d}"

# ---------------------------------------------------------------- TXT 생성
buf = io.StringIO()
W = 68


def rule(ch="─"):
    buf.write(ch * W + "\n")


n_say = sum(1 for e in entries if e["kind"] == "say")
n_cov = sum(1 for e in entries if e["kind"] == "title")

rule("═")
buf.write(" 2026 조직건강도 AI Agent — 시연 영상 스크립트\n")
buf.write(f" 항목 {len(entries)}개 (자막 {n_say} · 커버/간지 {n_cov} · 그 외)\n")
rule("═")
buf.write("""
■ 편집 방법

  · [번호]와 그 옆 종류 표시는 그대로 두고, 바로 아래 줄의 내용만 고쳐주세요.
  · <b>이렇게</b> 감싸면 자막에서 파란색으로 강조됩니다.
  · 자막은 한 문장으로 짧게 쓰는 게 좋습니다 (한 줄에 약 40자까지 들어갑니다).
  · '커버·제목'은 줄바꿈해도 됩니다. 나머지는 한 줄로 써주세요.
  · 항목을 빼고 싶으면 내용 자리에 (삭제) 라고만 적어주세요.
  · 항목을 새로 넣고 싶으면 원하는 위치에 [신규] 자막 이라고 쓰고
    다음 줄에 내용을 적어주세요.

■ 종류 설명

  커버·상단라벨   전체화면 카드 맨 위의 작은 영문 라벨
  커버·큰번호     간지 배경에 크게 깔리는 챕터 번호
  커버·제목       전체화면 카드의 큰 제목
  커버·부제       제목 아래 한 줄 설명
  커버·하단       카드 맨 아래 작은 글씨
  자막            화면 하단 중앙에 뜨는 내레이션
  챕터라벨        화면 왼쪽 아래 알약 모양 라벨
  입력문구        시연 중 실제로 타이핑되는 문장 (챗봇 질문 등)

■ 화면 노출 시간은 제가 글자 수에 맞춰 자동으로 다시 계산합니다.
  특정 항목을 더 길게/짧게 두고 싶으면 내용 뒤에 (3초) 처럼 적어주세요.

""")

cur_section = None
for e in entries:
    # 이 항목 앞에 나오는 섹션 주석이 있으면 구분선을 넣는다
    newest = None
    for sec_ln, name in sections.items():
        if sec_ln <= e["lineno"]:
            if newest is None or sec_ln > newest[0]:
                newest = (sec_ln, name)
    if newest and newest[1] != cur_section:
        cur_section = newest[1]
        buf.write("\n")
        rule()
        buf.write(f" {cur_section}\n")
        rule()
        buf.write("\n")

    buf.write(f"[{e['id']}] {KIND_LABEL[e['kind']]}\n")
    buf.write(e["text"] + "\n\n")

rule("═")
buf.write(" 수정 후 이 파일을 그대로 보내주시면 영상에 반영해 다시 녹화합니다.\n")
rule("═")

os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)
with open(OUT_TXT, "w", encoding="utf-8") as f:
    f.write(buf.getvalue())

with open(OUT_MAP, "w", encoding="utf-8") as f:
    json.dump({"source": SRC, "entries": entries}, f, ensure_ascii=False, indent=1)

print(f"항목 {len(entries)}개 → {OUT_TXT}")
print(f"매핑 → {OUT_MAP}")
print(f"크기 {os.path.getsize(OUT_TXT):,} bytes")
