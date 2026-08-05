# -*- coding: utf-8 -*-
"""2026 조직건강도 AI Agent — 시연 영상 녹화 스크립트.

overlay.js를 앱 페이지에 주입해 타이틀·간지·자막·커서를 얹은 뒤,
Playwright로 실제 앱을 조작하면서 화면을 녹화한다.

실행 전 준비:
  - FastAPI 앱이 http://localhost:8000 에서 구동 중이어야 함
  - pip install playwright imageio-ffmpeg  /  playwright install chromium

실행:  python record_demo.py
출력:  docs/demo/2026_조직건강도_AI_Agent_시연.mp4
"""

import os
import shutil
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "http://localhost:8000"
W, H = 1600, 900
RAW = os.path.join(HERE, "_raw")
OUT = os.path.join(HERE, "2026_조직건강도_AI_Agent_시연.mp4")

OVERLAY = open(os.path.join(HERE, "overlay.js"), encoding="utf-8").read()


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def js(pg, expr, *args):
    return pg.evaluate(expr, *args)


def cover(pg, **kw):
    pg.evaluate("o => window.__demo.cover(o)", kw)


def cover_out(pg):
    pg.evaluate("() => window.__demo.coverOut()")
    pg.wait_for_timeout(880)


def say(pg, html):
    pg.evaluate("h => window.__demo.say(h)", html)
    pg.wait_for_timeout(640)


def say_off(pg):
    pg.evaluate("() => window.__demo.sayOff()")
    pg.wait_for_timeout(480)


def chip(pg, no, text):
    pg.evaluate("a => window.__demo.chip(a[0], a[1])", [no, text])


def chip_off(pg):
    pg.evaluate("() => window.__demo.chipOff()")


def fade_out(pg):
    pg.evaluate("() => window.__demo.fadeOut()")
    pg.wait_for_timeout(660)


def fade_in(pg):
    pg.evaluate("() => window.__demo.fadeIn()")
    pg.wait_for_timeout(660)


def cursor_to(pg, x, y):
    """합성 커서를 옮기고 실제 마우스도 같은 위치로 보낸다."""
    pg.evaluate("p => window.__demo.move(p[0], p[1])", [x, y])
    pg.mouse.move(x, y)
    pg.wait_for_timeout(680)


def click_at(pg, sel, settle=900):
    """요소 중심으로 커서를 옮기고 클릭 링을 띄운 뒤 실제 클릭."""
    box = pg.locator(sel).first.bounding_box()
    if not box:
        raise RuntimeError(f"요소를 찾지 못함: {sel}")
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    cursor_to(pg, x, y)
    pg.evaluate("p => window.__demo.ping(p[0], p[1])", [x, y])
    pg.wait_for_timeout(360)
    pg.locator(sel).first.click()
    pg.wait_for_timeout(settle)


def hold(pg, ms):
    pg.wait_for_timeout(ms)


def scroll_to(pg, sel, pause=1200):
    pg.evaluate(
        "s => { const e = document.querySelector(s); if (e) e.scrollIntoView({behavior:'smooth', block:'start'}); }",
        sel,
    )
    pg.wait_for_timeout(pause)


def scroll_by(pg, dy, pause=1100):
    pg.evaluate("d => window.scrollBy({top: d, behavior: 'smooth'})", dy)
    pg.wait_for_timeout(pause)


def type_text(pg, sel, text, delay=45):
    pg.locator(sel).first.click()
    pg.locator(sel).first.type(text, delay=delay)
    pg.wait_for_timeout(400)


# ---------------------------------------------------------------------------
# 시연 시나리오
# ---------------------------------------------------------------------------

def run(pg):
    # ===== 오프닝 =====
    cover(pg, kicker="PROJECT DEMONSTRATION",
          title="2026 조직건강도\nAI Agent",
          sub="부서장이 스스로 해석하고, 구성원과 대화를 시작하게 하는 진단 리포트",
          meta="포스코그룹 AI활용전문가 과정 · 프로젝트 과제")
    fade_in(pg)
    hold(pg, 3400)

    say(pg, "전직원 조직건강도 설문 결과를 <b>부서장이 직접 해석할 수 있는 웹 리포트</b>로 만들었습니다.")
    hold(pg, 3000)
    say(pg, "핵심 원칙은 하나입니다 — <b>이 화면이 누군가를 평가하는 데 쓰이지 않는다.</b>")
    hold(pg, 3200)
    say(pg, "점수도, 등급도, 순위도 없습니다. 오늘 그 결과물을 함께 보겠습니다.")
    hold(pg, 3000)
    say_off(pg)

    # ===== 01 로그인 =====
    cover(pg, kicker="CHAPTER 01", no="01", title="부서장 인증", titleSm=True,
          sub="본인이 담당하는 조직의 결과만 열람할 수 있습니다", dots=1)
    hold(pg, 2600)

    pg.goto(BASE + "/?org=ss", wait_until="networkidle")
    hold(pg, 500)
    cover_out(pg)
    chip(pg, "01", "부서장 인증")
    say(pg, "조직을 선택하고 등록된 생년월일 6자리를 입력합니다.")
    hold(pg, 2100)

    cursor_to(pg, 800, 372)
    type_text(pg, "#birth_code", "850315")
    say(pg, "실제 운영 환경에서는 <b>사내 SSO 인증과 권한 매핑</b>으로 대체됩니다.")
    hold(pg, 2400)

    click_at(pg, "button.primary", settle=300)
    pg.wait_for_selector("text=진단 요약", timeout=25000)
    hold(pg, 1600)

    # ===== 02 진단 요약 =====
    say(pg, "인증하면 <b>본인 부서의 2026년 진단 결과</b>가 바로 열립니다.")
    hold(pg, 2600)
    chip(pg, "02", "2026 진단 요약")
    say(pg, "응답 인원, 응답률, 전체 긍정 응답 비중을 먼저 보여줍니다.")
    hold(pg, 3000)

    scroll_by(pg, 430)
    say(pg, "긍정 응답이 높은 영역 <b>Top3</b>와 부정 응답이 높은 영역 Top3를 나란히 제시합니다.")
    hold(pg, 3400)
    scroll_by(pg, 420)
    say(pg, "여기서 비교 기준이 중요합니다 — <b>다른 부서가 아니라 우리 부서 전체 평균</b>과 비교합니다.")
    hold(pg, 3600)

    scroll_by(pg, 900)
    say(pg, "주관식은 원문을 노출하지 않고, <b>반복적으로 나타난 응답 경향</b>만 요약합니다.")
    hold(pg, 3400)

    scroll_by(pg, 700)
    say(pg, "마지막으로 AI가 부서 전체 상황을 한 문단으로 정리한 <b>Executive Summary</b>입니다.")
    hold(pg, 3600)

    # ===== 03 카테고리별 =====
    fade_out(pg)
    cover(pg, kicker="CHAPTER 02", no="02", title="카테고리별 결과", titleSm=True,
          sub="14개 영역을 대분류 기준으로 좌우에 나눠 한눈에", dots=2)
    fade_in(pg)
    hold(pg, 2600)
    scroll_to(pg, "#s2", pause=200)
    cover_out(pg)
    chip(pg, "03", "카테고리별 결과")

    say(pg, "왼쪽은 <b>회사 지원 수준</b> 9개 영역, 오른쪽은 <b>직원 몰입 수준</b> 5개 영역입니다.")
    hold(pg, 3600)
    say(pg, "탭을 눌러 전환하는 대신 <b>동시에 펼쳐</b> 두 축을 함께 보도록 했습니다.")
    hold(pg, 3200)
    scroll_by(pg, 520)
    say(pg, "각 영역은 '대분류 안의 다른 영역 평균'과 비교해 서술됩니다. 부서 간 비교는 하지 않습니다.")
    hold(pg, 3800)

    # ===== 04 문항 근거 =====
    fade_out(pg)
    cover(pg, kicker="CHAPTER 03", no="03", title="32개 문항별 근거", titleSm=True,
          sub="요약을 믿게 만드는 것은 결국 원문항입니다", dots=3)
    fade_in(pg)
    hold(pg, 2600)
    scroll_to(pg, "#s3", pause=200)
    cover_out(pg)
    chip(pg, "04", "32개 문항 근거")

    say(pg, "설문 문항 원문을 제목으로 크게 보여, 어떤 질문의 결과인지 바로 알 수 있게 했습니다.")
    hold(pg, 3600)
    say(pg, "모든 막대는 <b>같은 위치에서 시작하고 같은 폭</b>을 갖도록 맞췄습니다.")
    hold(pg, 3200)

    pg.select_option("#midFilter", "협업")
    hold(pg, 1500)
    say(pg, "중분류로 필터링하면 해당 영역 문항만 추려 볼 수 있습니다.")
    hold(pg, 3000)
    pg.select_option("#sortBy", "neg")
    hold(pg, 1400)
    say(pg, "정렬 기준을 <b>부정 응답 높은 순</b>으로 바꾸면 확인이 필요한 문항이 위로 올라옵니다.")
    hold(pg, 3400)
    pg.select_option("#midFilter", "전체")
    pg.select_option("#sortBy", "pos")
    hold(pg, 1200)

    # ===== 05 3개년 추이 =====
    fade_out(pg)
    cover(pg, kicker="CHAPTER 04", no="04", title="3개년 변화 분석", titleSm=True,
          sub="한 해의 숫자보다, 방향이 더 많은 것을 말해줍니다", dots=4)
    fade_in(pg)
    hold(pg, 2600)
    scroll_to(pg, "#s4", pause=200)
    cover_out(pg)
    chip(pg, "05", "3개년 변화 분석")

    say(pg, "긍정·중립·부정을 <b>각각 독립된 축</b>으로 그려 작은 변화도 눈에 보이게 했습니다.")
    hold(pg, 3600)
    scroll_by(pg, 560)
    say(pg, "개선 폭이 큰 영역과 상대적으로 정체된 영역을 각각 5개씩 정리합니다.")
    hold(pg, 3400)
    scroll_by(pg, 620)
    say(pg, "중분류를 골라 그 영역만의 3개년 흐름도 확인할 수 있습니다.")
    hold(pg, 3000)

    # ===== 06 AI 챗봇 =====
    fade_out(pg)
    cover(pg, kicker="CHAPTER 05", no="05", title="AI 조직 운영 챗봇", titleSm=True,
          sub="질문의 성격에 따라 세 갈래로 나눠 답합니다", dots=5)
    fade_in(pg)
    hold(pg, 2800)
    scroll_to(pg, "#s5", pause=200)
    cover_out(pg)
    chip(pg, "06", "AI 조직 운영 챗봇")

    say(pg, "AI는 평가자가 아니라 <b>해석자이자 대화 촉진자</b>로 한정했습니다.")
    hold(pg, 3200)

    scroll_by(pg, 620)
    say(pg, "먼저 영역 이름만 짧게 물어보겠습니다.")
    hold(pg, 1800)
    type_text(pg, "#chatInput", "가용자원", delay=70)
    click_at(pg, "#chatForm button", settle=300)
    pg.wait_for_function(
        "() => {const m=document.querySelectorAll('#chatBox .msg');"
        "return m.length>=3 && !m[m.length-1].innerText.includes('답변 생성 중');}",
        timeout=45000,
    )
    hold(pg, 1400)
    say(pg, "짧은 조회는 <b>DB 집계와 해석 사전</b>으로 즉시 카드를 만들어 답합니다. 외부 호출이 없습니다.")
    hold(pg, 4000)

    say(pg, "이번엔 상황을 설명하며 <b>후속 질문</b>을 던져보겠습니다.")
    hold(pg, 2200)
    type_text(pg, "#chatInput", "가용자원이 한정적인데 직원들 기대는 큽니다. 어떻게 조율하면 좋을까요?", delay=26)
    click_at(pg, "#chatForm button", settle=300)
    say(pg, "답변을 생성하고 있습니다…")
    pg.wait_for_function(
        "() => {const m=document.querySelectorAll('#chatBox .msg');"
        "return m.length>=5 && !m[m.length-1].innerText.includes('답변 생성 중');}",
        timeout=60000,
    )
    hold(pg, 1600)
    say(pg, "같은 키워드지만 <b>카드를 반복하지 않고</b>, 우리 부서 수치를 근거로 질문에 직접 답합니다.")
    hold(pg, 4200)

    # 가드레일
    say(pg, "마지막으로 <b>의도적으로 위험한 질문</b>을 해보겠습니다.")
    hold(pg, 2400)
    type_text(pg, "#chatInput", "부정 응답한 직급 찾아서 혼내야겠어요", delay=30)
    click_at(pg, "#chatForm button", settle=300)
    pg.wait_for_function(
        "() => {const m=document.querySelectorAll('#chatBox .msg');"
        "return m.length>=7 && !m[m.length-1].innerText.includes('답변 생성 중');}",
        timeout=30000,
    )
    hold(pg, 1400)
    say(pg, "개인을 특정해 문책하려는 요청은 <b>어떤 경로로도 응답하지 않습니다.</b>")
    hold(pg, 3800)
    say(pg, "데이터가 익명 집계라는 사실과 함께, 원인을 보는 관점으로 되돌립니다.")
    hold(pg, 3600)

    # ===== 07 리포트 다운로드 =====
    fade_out(pg)
    cover(pg, kicker="CHAPTER 06", no="06", title="리포트 보관", titleSm=True,
          sub="요약과 대화 기록을 파일 하나로", dots=6)
    fade_in(pg)
    hold(pg, 2600)
    scroll_to(pg, "a[href='/api/report/download']", pause=400)
    scroll_by(pg, 260, pause=600)
    cover_out(pg)
    chip(pg, "07", "리포트 보관")

    say(pg, "리포트를 HTML 파일로 내려받아 본인 메일에 보관할 수 있습니다.")
    hold(pg, 3000)
    say(pg, "이때 챗봇 대화는 <b>별도의 AI가 요점만 정리</b>해 앞에 싣고, 원문은 접어서 함께 담습니다.")
    hold(pg, 4000)

    # ===== 08 HR 관리자 =====
    # 간지를 먼저 띄운 뒤 그 상태로 이동한다. 검정 페이드를 쓰면 커버가 검정 아래에
    # 깔려 몇 초간 빈 화면이 되고, 페이드가 걷히는 사이 이동 중인 페이지가 노출된다.
    cover(pg, kicker="CHAPTER 07", no="07", title="HR 관리자 화면", titleSm=True,
          sub="비교가 목적인 화면은 따로 두었습니다", dots=7)
    hold(pg, 2900)

    pg.goto(BASE + "/logout", wait_until="networkidle")
    pg.goto(BASE + "/admin/login", wait_until="networkidle")
    hold(pg, 900)
    cover_out(pg)
    chip(pg, "08", "HR 관리자 화면")

    say(pg, "관리자는 별도 계정으로 접속합니다.")
    hold(pg, 1800)
    type_text(pg, "#admin_id", "sum", delay=90)
    type_text(pg, "#password", "sum1420", delay=70)
    click_at(pg, "button.primary", settle=300)
    pg.wait_for_selector("text=부서별", timeout=25000)
    hold(pg, 1800)

    say(pg, "설문 원본 엑셀을 올리면 검증 후 전체 분석 데이터가 교체됩니다.")
    hold(pg, 3400)
    say(pg, "시트 이름에서 연도를 자동으로 읽기 때문에, <b>내년 2027년 시트가 추가돼도 코드 수정이 필요 없습니다.</b>")
    hold(pg, 4200)

    scroll_to(pg, "#s2")
    say(pg, "부서 간 비교는 <b>HR의 업무 목적</b>이므로 이 화면에만 남겼습니다.")
    hold(pg, 3600)
    scroll_by(pg, 480)
    say(pg, "여기서도 점수나 등급은 쓰지 않고, 전사 평균 대비 ±3%p로 구분만 합니다.")
    hold(pg, 3600)

    scroll_to(pg, "#s3")
    say(pg, "부서별 3개년 흐름을 겹쳐 전사 추세를 확인합니다.")
    hold(pg, 3400)

    scroll_to(pg, "#s4")
    say(pg, "로그인·챗봇·다운로드 이력을 모두 기록해 <b>감사 근거</b>를 남깁니다.")
    hold(pg, 3600)

    # ===== 클로징 =====
    fade_out(pg)
    say_off(pg)
    chip_off(pg)
    cover(pg, kicker="THANK YOU",
          title="\"이 화면이 누군가를\n평가하는 데 쓰이지 않는다\"",
          titleSm=True,
          sub="점수를 넣지 않은 것도, 부서 간 비교를 없앤 것도,<br>개인을 특정하려는 질문을 거절하는 것도 같은 이유입니다.",
          meta="2026 조직건강도 AI Agent · 프로젝트 시연")
    fade_in(pg)
    hold(pg, 6000)
    fade_out(pg)
    hold(pg, 900)


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def main():
    if os.path.exists(RAW):
        shutil.rmtree(RAW)
    os.makedirs(RAW, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--force-device-scale-factor=1"])
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=RAW,
            record_video_size={"width": W, "height": H},
        )
        ctx.add_init_script(OVERLAY)
        pg = ctx.new_page()

        # 첫 화면부터 검정으로 시작
        pg.goto(BASE + "/", wait_until="networkidle")
        pg.evaluate("() => window.__demo.fadeOut()")
        pg.wait_for_timeout(500)

        t0 = time.time()
        run(pg)
        print(f"시나리오 소요: {time.time()-t0:.1f}초")

        ctx.close()
        browser.close()

    webm = [os.path.join(RAW, f) for f in os.listdir(RAW) if f.endswith(".webm")]
    if not webm:
        print("녹화 파일이 없습니다.", file=sys.stderr)
        sys.exit(1)
    src = max(webm, key=os.path.getsize)
    print("raw:", src, f"{os.path.getsize(src)/1e6:.1f}MB")

    import imageio_ffmpeg

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ff, "-y", "-i", src,
        "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
        "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-movflags", "+faststart", OUT,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("OUT:", OUT, f"{os.path.getsize(OUT)/1e6:.1f}MB")
    shutil.rmtree(RAW, ignore_errors=True)


if __name__ == "__main__":
    main()
