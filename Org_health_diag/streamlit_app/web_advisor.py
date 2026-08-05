# -*- coding: utf-8 -*-
"""일반 리더십/조직관리 질문을 위한 웹검색 기반 자문 Tool.

챗봇의 14개 중분류 키워드와 매칭되지 않는, 조직 진단 데이터와 무관한 일반적인
리더십/조직관리 질문에 한해 사용한다. Tavily로 웹을 검색하고 OpenAI 모델로
검색 결과를 종합해 답변한다 (03_ai_agent_design.md의 Action Guide Agent를
웹 검색 능력으로 확장한 형태 — Search Tool + LLM 조합).

API 키가 없거나 호출이 실패하면 None을 반환하며, 상위 로직(chatbot.py)이
오프라인 fallback으로 대체한다. 절대 예외를 밖으로 던지지 않는다.
"""

import os

# 이 프로젝트(Org_health_diag)는 상위 폴더의 .env(OPENAI_API_KEY, TAVILY_API_KEY 등)를
# 공유해서 쓴다. python-dotenv로 한 번만 로드하고, 이미 설정된 값은 덮어쓰지 않는다.
try:
    from dotenv import load_dotenv

    _ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(_ENV_PATH, override=False)
except Exception:
    pass

SYSTEM_PROMPT = (
    "당신은 부서장의 조직 운영/리더십 고민을 돕는 자문 도구입니다. "
    "지금 받은 질문은 특정 조직의 진단 데이터나 평가와는 무관한 일반적인 "
    "리더십/조직관리 주제입니다. "
    "아래 제공된 웹 검색 결과를 참고하여 신뢰할 수 있는 내용을 바탕으로 "
    "한국어로 400자 내외로 간결하게 답변하세요. "
    "다음을 반드시 지키세요: "
    "1) 특정 개인이나 조직을 평가하거나 단정하지 않는다. "
    "2) 징계, 처벌적 관리 방식을 권장하지 않는다. "
    "3) 일방적 처방이 아니라 점검해볼 방향과 대화 방법을 제안한다. "
    "4) 점수, 등급, 순위 표현을 사용하지 않는다. "
    "5) 검색 결과에 없는 내용을 지어내지 않는다."
)

DEFAULT_MODEL = "gpt-4.1-mini"

GROUNDED_SYSTEM_PROMPT = (
    "당신은 부서장의 조직 운영 고민에 대화 상대가 되어주는 도우미입니다. "
    "아래에 이 부서의 실제 진단 데이터 요약이 주어집니다. 이를 근거로 부서장의 "
    "질문에 구체적이고 실질적으로 답변하세요. 주어진 데이터를 요약해서 되풀이하지 "
    "말고, 질문에서 실제로 묻는 내용(원인 가설, 조율 방법, 대화 방식 등)에 답하세요. "
    "다음을 반드시 지키세요: "
    "1) 주어진 데이터에 없는 구체적 수치·사실을 지어내지 않는다. "
    "2) 특정 개인을 지목하거나 평가·단정하지 않는다 — 이 데이터는 익명 집계이며 "
    "개인 식별 정보가 없다. "
    "3) 징계, 처벌적 관리 방식을 권장하지 않는다. "
    "4) 일방적 처방이 아니라 점검해볼 방향과 대화 방법을 제안한다. "
    "5) 점수, 등급, 순위 표현을 사용하지 않는다. "
    "6) 한국어로 300~450자 내외로 간결하게 답변한다."
)

SUMMARY_SYSTEM_PROMPT = (
    "당신은 부서장과 조직운영 챗봇 사이의 대화를 요약하는 보조 역할입니다. "
    "아래 대화 전체를 읽고, 부서장이 궁금해했던 주제와 챗봇이 제안한 방향을 "
    "한국어 불릿 포인트로 간결하게 정리하세요. "
    "형식: '- 주제: 한 줄 요지' 를 대화당 최대 6개 항목까지. "
    "새로운 조언을 추가하거나 원 대화에 없는 내용을 지어내지 마세요. "
    "점수·등급·순위 표현은 쓰지 않습니다."
)


def _get_secret(name: str):
    try:
        import streamlit as st

        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.environ.get(name)


def available() -> bool:
    return bool(_get_secret("OPENAI_API_KEY") and _get_secret("TAVILY_API_KEY"))


def llm_available() -> bool:
    """웹검색 없이 OpenAI 호출만 필요한 기능(근거 기반 대화, 대화 요약)의 가용 여부."""
    return bool(_get_secret("OPENAI_API_KEY"))


def _complete(messages: list[dict], max_tokens: int, temperature: float) -> str | None:
    """OpenAI 호출 공통 처리. 실패 시 조용히 None을 반환한다(상위에서 폴백)."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=_get_secret("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_get_secret("OPENAI_MODEL") or DEFAULT_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception:
        return None
    if not response.choices:
        return None
    text = (response.choices[0].message.content or "").strip()
    return text or None


def answer_grounded(question: str, context: str) -> str | None:
    """웹 검색 없이, 호출자가 제공한 조직 데이터 컨텍스트만 근거로 답변한다."""
    if not llm_available():
        return None
    user_prompt = f"[이 부서의 진단 데이터]\n{context}\n\n[부서장의 질문]\n{question}"
    return _complete(
        [
            {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=600,
        temperature=0.5,
    )


def summarize_conversation(history: list[tuple[str, str]]) -> str | None:
    """챗봇 대화 전체를 요점 위주로 요약한다. 다운로드 리포트에서 사용."""
    if not llm_available() or not history:
        return None
    transcript = "\n".join(
        f"{'부서장' if role == 'user' else '챗봇'}: {text}" for role, text in history
    )
    return _complete(
        [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        max_tokens=500,
        temperature=0.3,
    )


def _search_web(query: str, max_results: int = 4):
    from tavily import TavilyClient

    client = TavilyClient(api_key=_get_secret("TAVILY_API_KEY"))
    result = client.search(query=query, search_depth="basic", max_results=max_results)
    return result.get("results", []) if result else []


def answer(question: str) -> str | None:
    """Tavily 검색 + OpenAI 종합으로 답변 생성. 실패 시 조용히 None을 반환한다."""
    if not available():
        return None

    try:
        results = _search_web(question)
    except Exception:
        return None

    if not results:
        return None

    context_blocks = []
    sources = []
    for r in results:
        title = r.get("title") or r.get("url") or "출처"
        url = r.get("url")
        content = (r.get("content") or "")[:600]
        context_blocks.append(f"[{title}]({url})\n{content}")
        if url and (title, url) not in sources:
            sources.append((title, url))

    context = "\n\n".join(context_blocks)
    user_prompt = f"질문: {question}\n\n다음은 웹 검색 결과입니다. 참고하여 답변하세요.\n\n{context}"

    text = _complete(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=700,
        temperature=0.4,
    )
    if not text:
        return None

    if sources:
        src_lines = "\n".join(f"- [{title}]({url})" for title, url in sources[:4])
        text += f"\n\n**참고 자료**\n{src_lines}"
    return text
