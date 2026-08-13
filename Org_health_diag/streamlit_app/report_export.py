# -*- coding: utf-8 -*-
"""리포트 + 챗봇 대화 내용을 파일로 저장하기 위한 HTML 생성기.

로컬 시연 환경에는 사내 SMTP 서버 정보가 없어 실제 메일 발송은 지원하지 않는다.
대신 다운로드한 HTML 파일을 본인 이메일에 직접 첨부해 보관/공유하는 방식을 사용한다.
"""

import datetime as dt
import html


def _esc(text) -> str:
    return html.escape(str(text))


def build_report_html(
    org: str,
    company: str,
    overall: dict,
    top_pos_df,
    top_neg_df,
    executive_summary: str,
    chat_history: list,
    year: str = "2026",
    chat_summary: str | None = None,
) -> str:
    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    pos_rows = "".join(
        f"<li><b>{_esc(r['중분류'])}</b> — 긍정 {r['긍정']}% · 중립 {r['중립']}% · 부정 {r['부정']}%</li>"
        for _, r in top_pos_df.iterrows()
    )
    neg_rows = "".join(
        f"<li><b>{_esc(r['중분류'])}</b> — 긍정 {r['긍정']}% · 중립 {r['중립']}% · 부정 {r['부정']}%</li>"
        for _, r in top_neg_df.iterrows()
    )

    if chat_history:
        chat_rows = "".join(
            f'<div class="msg {_esc(role)}"><span class="role">{"도우미" if role=="assistant" else "나"}</span>'
            f"<div>{_esc(content).replace(chr(10), '<br>')}</div></div>"
            for role, content in chat_history
        )
    else:
        chat_rows = "<p>대화 기록이 없습니다.</p>"

    if chat_summary:
        summary_html = _esc(chat_summary).replace(chr(10), "<br>")
        chat_section = f"""
<h2>조직운영 챗봇 대화 요약</h2>
<div class="summary-box">{summary_html}</div>
<details class="raw-chat">
<summary>전체 대화 원문 보기</summary>
{chat_rows}
</details>
"""
    elif chat_history:
        chat_section = f"""
<h2>조직운영 챗봇 대화 기록</h2>
<p class="note">요약을 생성하지 못해 대화 원문을 표시합니다.</p>
{chat_rows}
"""
    else:
        chat_section = f"""
<h2>조직운영 챗봇 대화 기록</h2>
{chat_rows}
"""

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{_esc(org)} {_esc(year)} 조직건강도 진단 리포트</title>
<style>
body {{ font-family: -apple-system, "Malgun Gothic", sans-serif; max-width: 800px; margin: 40px auto; color: #222; line-height: 1.6; }}
h1 {{ font-size: 1.6rem; border-bottom: 3px solid #3E8E5A; padding-bottom: 8px; }}
h2 {{ font-size: 1.2rem; margin-top: 2rem; }}
.badge {{ display:inline-block; padding:2px 10px; border-radius:999px; background:#3E8E5A; color:white; font-size:0.85rem; }}
.msg {{ margin-bottom: 10px; padding: 8px 12px; border-radius: 8px; background: #f4f6f8; }}
.msg .role {{ font-weight: 700; margin-right: 6px; }}
.msg.user {{ background: #eaf3ff; }}
.summary-box {{ background: #eaf3ff; border-radius: 8px; padding: 12px 16px; }}
.raw-chat {{ margin-top: 1rem; }}
.raw-chat summary {{ cursor: pointer; color: #555; font-size: 0.9rem; }}
.note {{ color: #888; font-size: 0.85rem; }}
.footer {{ margin-top: 3rem; color: #777; font-size: 0.85rem; border-top: 1px solid #ddd; padding-top: 1rem; }}
</style>
</head>
<body>
<h1>{_esc(company)} · {_esc(org)} — {_esc(year)} 조직건강도 진단 리포트</h1>
<p>생성 시각: {generated_at} · 본인 담당 조직 전용 · 개인 응답 원문 미노출</p>

<h2>전체 응답 비중</h2>
<p><span class="badge">긍정 {overall['긍정']}%</span>
&nbsp;중립 {overall['중립']}%&nbsp; 부정 {overall['부정']}%&nbsp; (표본 n={overall['n']})</p>

<h2>긍정 응답 Top3 영역</h2>
<ul>{pos_rows}</ul>

<h2>부정 응답 Top3 영역</h2>
<ul>{neg_rows}</ul>

<h2>AI Executive Summary</h2>
<p>{_esc(executive_summary)}</p>

{chat_section}

<div class="footer">
본 리포트는 시연용 데모이며 평가 점수·등급·순위를 제공하지 않습니다. AI 해석 문장은 사전 정의된
해석 로직 기반 예시입니다. 개인 응답 원문은 포함되어 있지 않습니다.
</div>
</body>
</html>"""
