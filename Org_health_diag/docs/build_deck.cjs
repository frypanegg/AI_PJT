/* 2026 조직건강도 AI Agent — 프로젝트 수행 결과 보고서 생성기
   팔레트는 실제 제품에 쓴 POSCO 브랜드 색을 그대로 사용하고,
   시각 모티프는 앱 화면의 '번호 배지 + 라운드 카드'를 반복한다. */

const pptx = require("pptxgenjs");
const path = require("path");

const pres = new pptx();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.author = "AI활용전문가 과정";
pres.title = "2026 조직건강도 AI Agent 수행 결과";

// ---------- 팔레트 ----------
const NAVY = "002D5A";
const BLUE = "004381";
const CYAN = "0098D9";
const ICE = "E8F1F8";
const INK = "172033";
const MUTED = "65708A";
const LINE = "DFE5EF";
const BG = "F5F7FB";
const POS = "00A950";
const NEG = "C94B5F";
const WARN = "E8912D";
const WHITE = "FFFFFF";

const HEAD = "Malgun Gothic";
const BODY = "Malgun Gothic";

const SHOTS = path.join(__dirname, "shots");
const M = 0.62; // 좌우 여백
const W = 13.333 - M * 2; // 12.093

let pageNo = 0;

function shadow() {
  return { type: "outer", color: "8894A8", blur: 10, offset: 2, angle: 90, opacity: 0.18 };
}

/** 표준 콘텐츠 슬라이드: 배경 + 커커 + 타이틀 + 페이지번호 */
function contentSlide(kicker, title) {
  pageNo += 1;
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText(kicker.toUpperCase(), {
    x: M, y: 0.4, w: W, h: 0.24, fontFace: HEAD, fontSize: 11, bold: true,
    color: CYAN, charSpacing: 1.6, margin: 0,
  });
  s.addText(title, {
    x: M, y: 0.66, w: W, h: 0.62, fontFace: HEAD, fontSize: 30, bold: true,
    color: NAVY, margin: 0,
  });
  s.addText(String(pageNo), {
    x: 13.333 - M - 0.6, y: 6.95, w: 0.6, h: 0.28, align: "right",
    fontFace: BODY, fontSize: 10, color: MUTED, margin: 0,
  });
  return s;
}

/** 번호 배지 (제품 화면의 섹션 번호 모티프) */
function badge(s, n, x, y, size = 0.42, fill = BLUE, txtColor = WHITE) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w: size, h: size, rectRadius: 0.1, fill: { color: fill },
  });
  s.addText(String(n), {
    x, y, w: size, h: size, align: "center", valign: "middle",
    fontFace: HEAD, fontSize: size > 0.5 ? 16 : 13, bold: true, color: txtColor, margin: 0,
  });
}

/** 라운드 카드 */
function card(s, x, y, w, h, fill = WHITE, radius = 0.08) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: radius,
    fill: { color: fill }, line: { color: LINE, width: 1 }, shadow: shadow(),
  });
}

// =====================================================================
// 1. 타이틀
// =====================================================================
{
  pageNo = 0;
  const s = pres.addSlide();
  s.background = { color: NAVY };
  // 그래픽모티프 느낌의 사선 블록
  s.addShape(pres.ShapeType.rect, {
    x: 9.1, y: 0, w: 4.3, h: 7.5, fill: { color: BLUE }, rotate: 0,
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 10.4, y: -1.5, w: 5.2, h: 5.2, fill: { color: CYAN, transparency: 72 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 9.6, y: 4.2, w: 3.4, h: 3.4, fill: { color: WHITE, transparency: 88 },
  });

  s.addText("PROJECT COMPLETION REPORT", {
    x: M, y: 1.55, w: 8.2, h: 0.3, fontFace: HEAD, fontSize: 12, bold: true,
    color: CYAN, charSpacing: 2, margin: 0,
  });
  s.addText("2026 조직건강도\nAI Agent", {
    x: M, y: 2.0, w: 8.2, h: 1.9, fontFace: HEAD, fontSize: 46, bold: true,
    color: WHITE, lineSpacing: 54, margin: 0,
  });
  s.addText(
    "부서장이 스스로 해석하고, 구성원과 대화를 시작하게 하는 진단 리포트",
    { x: M, y: 4.05, w: 8.2, h: 0.4, fontFace: BODY, fontSize: 15, color: "AFC6DE", margin: 0 }
  );

  // 하단 메타
  const metas = [
    ["분석 응답", "37,248건"],
    ["진단 문항", "32문항 · 14영역"],
    ["대상 조직", "6개 부서 · 3개년"],
  ];
  metas.forEach(([k, v], i) => {
    const x = M + i * 2.75;
    s.addText(k, {
      x, y: 5.35, w: 2.5, h: 0.24, fontFace: HEAD, fontSize: 10.5, bold: true,
      color: "8FB2D4", charSpacing: 1, margin: 0,
    });
    s.addText(v, {
      x, y: 5.62, w: 2.5, h: 0.42, fontFace: HEAD, fontSize: 19, bold: true,
      color: WHITE, margin: 0,
    });
  });

  s.addText("포스코그룹 AI활용전문가 과정  ·  프로젝트 과제  ·  2026.08", {
    x: M, y: 6.75, w: 8.2, h: 0.3, fontFace: BODY, fontSize: 11, color: "7E9CBC", margin: 0,
  });
  s.addNotes(
    "조직건강도 설문 결과를 부서장이 스스로 해석하고 구성원과의 대화 주제를 찾도록 돕는 웹 애플리케이션을 설계·구현한 프로젝트입니다."
  );
}

// =====================================================================
// 2. Executive Summary
// =====================================================================
{
  const s = contentSlide("Executive Summary", "평가 도구가 아닌, 대화를 여는 진단 리포트");

  card(s, M, 1.5, W, 1.42, ICE);
  s.addText(
    "설문 결과가 연도별 엑셀로만 존재하고, 부서장은 자기 조직의 숫자를 어떻게 읽어야 할지 모르는 상태였다. " +
      "본 과제는 그 엑셀을 부서장이 혼자서도 해석할 수 있는 웹 리포트로 바꾸되, " +
      "'평가에 쓰이지 않는다'는 원칙을 데이터 처리부터 문장 생성까지 일관되게 관철하는 것을 목표로 했다.",
    { x: M + 0.32, y: 1.68, w: W - 0.64, h: 1.05, fontFace: BODY, fontSize: 13.5, color: INK, lineSpacing: 22, margin: 0 }
  );

  const stats = [
    ["2", "개 사용자 화면", "부서장 리포트 · HR 관리자", BLUE],
    ["5", "단 구성 리포트", "요약→영역→문항→추이→AI", CYAN],
    ["3", "단 AI 라우팅", "규칙 · 데이터근거 LLM · 웹검색", POS],
    ["6", "대 윤리 원칙", "코드로 강제한 가드레일", WARN],
  ];
  const cw = (W - 0.36 * 3) / 4;
  stats.forEach(([num, label, desc, col], i) => {
    const x = M + i * (cw + 0.36);
    card(s, x, 3.16, cw, 1.95);
    s.addText(num, {
      x: x + 0.26, y: 3.34, w: cw - 0.5, h: 0.88, fontFace: HEAD, fontSize: 42,
      bold: true, color: col, margin: 0,
    });
    s.addText(label, {
      x: x + 0.26, y: 4.24, w: cw - 0.5, h: 0.3, fontFace: HEAD, fontSize: 13.5,
      bold: true, color: INK, margin: 0,
    });
    s.addText(desc, {
      x: x + 0.26, y: 4.56, w: cw - 0.5, h: 0.5, fontFace: BODY, fontSize: 10.5,
      color: MUTED, lineSpacing: 15, margin: 0,
    });
  });

  card(s, M, 5.36, W, 1.32, "FFFFFF");
  s.addText("핵심 성과", {
    x: M + 0.32, y: 5.54, w: 2.0, h: 0.3, fontFace: HEAD, fontSize: 12.5, bold: true,
    color: BLUE, margin: 0,
  });
  s.addText(
    [
      { text: "Streamlit 프로토타입으로 개념을 검증한 뒤 FastAPI + SQLite 웹앱으로 전환", options: { bullet: true, breakLine: true } },
      { text: "HR 지침 변경(부서 간 비교 지양)을 해석 로직 전면 재설계로 반영", options: { bullet: true, breakLine: true } },
      { text: "내년 2027년 시트가 추가돼도 코드 수정 없이 동작하도록 연도 구조 일반화", options: { bullet: true } },
    ],
    { x: M + 2.5, y: 5.5, w: W - 2.9, h: 1.0, fontFace: BODY, fontSize: 11.5, color: INK, paraSpaceAfter: 5, margin: 0 }
  );
  s.addNotes("한 장 요약. 무엇을 왜 만들었고, 어떤 원칙을 지켰는지.");
}

// =====================================================================
// 3. 과제 정의
// =====================================================================
{
  const s = contentSlide("Problem Definition", "숫자를 주는 것보다, 오해를 막는 것이 더 어려웠다");

  // 좌: 문제 상황
  card(s, M, 1.5, 5.72, 2.35);
  badge(s, "!", M + 0.3, 1.76, 0.4, NEG);
  s.addText("현재 상황", {
    x: M + 0.82, y: 1.78, w: 3.0, h: 0.34, fontFace: HEAD, fontSize: 15, bold: true, color: INK, margin: 0,
  });
  s.addText(
    [
      { text: "설문 결과가 연도별 엑셀 파일로만 존재", options: { bullet: true, breakLine: true } },
      { text: "부서장은 자기 조직 숫자의 의미를 판단하기 어려움", options: { bullet: true, breakLine: true } },
      { text: "잘못 쓰이면 조직장 평가·문책 도구가 될 위험", options: { bullet: true } },
    ],
    { x: M + 0.34, y: 2.3, w: 5.06, h: 1.4, fontFace: BODY, fontSize: 12.5, color: INK, paraSpaceAfter: 7, margin: 0 }
  );

  // 우: 사용자
  card(s, M + 6.0, 1.5, 6.09, 2.35);
  badge(s, "→", M + 6.3, 1.76, 0.4, BLUE);
  s.addText("설계 방향", {
    x: M + 6.82, y: 1.78, w: 3.0, h: 0.34, fontFace: HEAD, fontSize: 15, bold: true, color: INK, margin: 0,
  });
  s.addText(
    [
      { text: "부서장 — 본인 조직만 조회, 해석과 대화 주제 제공", options: { bullet: true, breakLine: true } },
      { text: "HR 관리자 — Raw Data 관리와 전사 현황 점검", options: { bullet: true, breakLine: true } },
      { text: "AI는 평가자가 아니라 해석자·대화 촉진자로 한정", options: { bullet: true } },
    ],
    { x: M + 6.34, y: 2.3, w: 5.4, h: 1.4, fontFace: BODY, fontSize: 12.5, color: INK, paraSpaceAfter: 7, margin: 0 }
  );

  // 제약 6가지
  s.addText("코드로 강제해야 했던 6가지 제약", {
    x: M, y: 4.12, w: W, h: 0.34, fontFace: HEAD, fontSize: 15, bold: true, color: NAVY, margin: 0,
  });
  const cons = [
    ["점수 미제공", "총점·지수 형태의 수치를 만들지 않는다"],
    ["등급·순위 미제공", "A/B/C 등급이나 부서 순위를 표시하지 않는다"],
    ["개인 원문 미노출", "주관식은 반복 경향만 요약해 보여준다"],
    ["소수 응답 보호", "응답 10명 미만 조직은 결과를 숨긴다"],
    ["평가성 표현 금지", "'문제가 있다', '실패했다' 류 문장을 쓰지 않는다"],
    ["부서 간 비교 지양", "부서장 화면에서 타 부서·전사 평균과 비교하지 않는다"],
  ];
  const ccw = (W - 0.3 * 2) / 3;
  cons.forEach(([t, d], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * (ccw + 0.3);
    const y = 4.58 + row * 1.12;
    card(s, x, y, ccw, 0.98, ICE);
    s.addText(t, {
      x: x + 0.24, y: y + 0.14, w: ccw - 0.48, h: 0.28, fontFace: HEAD, fontSize: 12.5,
      bold: true, color: BLUE, margin: 0,
    });
    s.addText(d, {
      x: x + 0.24, y: y + 0.44, w: ccw - 0.48, h: 0.46, fontFace: BODY, fontSize: 10.5,
      color: MUTED, lineSpacing: 14, margin: 0,
    });
  });
  s.addNotes("이 6가지는 기획 문서(06_guardrails.md)에 정의되어 있으며, 이후 모든 구현 판단의 기준이 되었습니다.");
}

// =====================================================================
// 4. 접근 방식
// =====================================================================
{
  const s = contentSlide("Approach", "원칙을 먼저 고정하고, 화면은 두 번 만들었다");

  const steps = [
    ["01", "원칙과 사전 정의", "해석 사전과 가드레일을 먼저 문서로 확정",
      ["14개 영역별 긍정·중립·부정 해석 문장 사전화", "금지 표현 / 권장 표현 목록 작성", "문항 32개 → 중분류 14 → 대분류 2 매핑"]],
    ["02", "데이터 파이프라인", "엑셀을 분석 가능한 구조로 정규화",
      ["연도별 시트 → long format 변환", "SQLite 5개 테이블 적재 (37,248건)", "업로드 시 동일 파이프라인 재사용"]],
    ["03", "화면과 AI 구현", "프로토타입 검증 후 웹앱으로 전환",
      ["Streamlit으로 구성·문구 빠르게 검증", "FastAPI + SQLite로 재구축", "3단 라우팅 챗봇과 리포트 내보내기"]],
  ];
  const sw = (W - 0.42 * 2) / 3;
  steps.forEach(([no, title, sub, items], i) => {
    const x = M + i * (sw + 0.42);
    card(s, x, 1.6, sw, 4.35);
    badge(s, no, x + 0.3, 1.88, 0.52, i === 2 ? CYAN : BLUE);
    s.addText(title, {
      x: x + 0.3, y: 2.56, w: sw - 0.6, h: 0.34, fontFace: HEAD, fontSize: 16, bold: true,
      color: NAVY, margin: 0,
    });
    s.addText(sub, {
      x: x + 0.3, y: 2.92, w: sw - 0.6, h: 0.5, fontFace: BODY, fontSize: 11.5,
      color: MUTED, lineSpacing: 16, margin: 0,
    });
    s.addText(
      items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
      { x: x + 0.3, y: 3.5, w: sw - 0.6, h: 2.2, fontFace: BODY, fontSize: 11.5, color: INK, paraSpaceAfter: 8, margin: 0 }
    );
    if (i < 2) {
      s.addShape(pres.ShapeType.rightArrow, {
        x: x + sw + 0.08, y: 3.6, w: 0.26, h: 0.26, fill: { color: CYAN },
      });
    }
  });

  card(s, M, 6.18, W, 0.78, ICE);
  s.addText(
    "프로토타입을 버리지 않고 남겨둔 이유 — Streamlit 버전은 문구와 구성 검증에 쓰고, 운영형 요구(세션·업로드·성능)가 확인된 뒤 FastAPI로 옮겼다. 두 버전은 포트가 달라 동시 구동이 가능하다.",
    { x: M + 0.32, y: 6.32, w: W - 0.64, h: 0.5, fontFace: BODY, fontSize: 11.5, color: INK, margin: 0 }
  );
  s.addNotes("원칙 → 데이터 → 화면 순서. 화면을 두 번 만든 것은 낭비가 아니라 검증 단계였습니다.");
}

// =====================================================================
// 5. 아키텍처
// =====================================================================
{
  const s = contentSlide("Architecture", "역할을 나눠 해석 로직을 한 곳에 모았다");

  const layers = [
    ["Presentation", BLUE, [
      ["FastAPI + Jinja2", "서버 렌더링 4개 화면"],
      ["Chart.js (로컬 번들)", "인터넷 없이도 차트 렌더링"],
      ["report.js / admin.js", "필터·정렬·스크롤·챗봇 UI"],
    ]],
    ["Domain Logic", CYAN, [
      ["analytics.py", "SQL 집계 + 부서 내부 비교 해석"],
      ["chat_service.py", "3단 라우팅 + 금지 요청 차단"],
      ["catalog.py", "문항 매핑 · 해석 사전 (공용)"],
    ]],
    ["Data & External", POS, [
      ["SQLite 5 tables", "responses · open_texts · orgs · admins · logs"],
      ["seed.py", "엑셀 → DB 적재 (업로드 시 재사용)"],
      ["OpenAI · Tavily", "근거 기반 답변 · 웹검색 · 대화 요약"],
    ]],
  ];
  let y = 1.56;
  layers.forEach(([name, col, rows]) => {
    card(s, M, y, W, 1.62);
    s.addShape(pres.ShapeType.roundRect, {
      x: M + 0.26, y: y + 0.26, w: 1.72, h: 0.46, rectRadius: 0.09, fill: { color: col },
    });
    s.addText(name, {
      x: M + 0.26, y: y + 0.26, w: 1.72, h: 0.46, align: "center", valign: "middle",
      fontFace: HEAD, fontSize: 11.5, bold: true, color: WHITE, margin: 0,
    });
    const bw = (W - 2.5 - 0.28 * 2) / 3;
    rows.forEach(([t, d], j) => {
      const x = M + 2.22 + j * (bw + 0.28);
      s.addShape(pres.ShapeType.roundRect, {
        x, y: y + 0.2, w: bw, h: 1.2, rectRadius: 0.07, fill: { color: BG }, line: { color: LINE, width: 1 },
      });
      s.addText(t, {
        x: x + 0.2, y: y + 0.36, w: bw - 0.4, h: 0.3, fontFace: HEAD, fontSize: 12,
        bold: true, color: NAVY, margin: 0,
      });
      s.addText(d, {
        x: x + 0.2, y: y + 0.68, w: bw - 0.4, h: 0.62, fontFace: BODY, fontSize: 10,
        color: MUTED, lineSpacing: 14, margin: 0,
      });
    });
    y += 1.78;
  });

  s.addText(
    "해석 사전(catalog.py)과 문항 매핑은 Streamlit·FastAPI 두 버전이 같은 파일을 참조한다 — 문구를 한 곳에서만 고치면 되도록.",
    { x: M, y: 6.92, w: W - 1.1, h: 0.34, fontFace: BODY, fontSize: 11, color: MUTED, italic: true, margin: 0 }
  );
  s.addNotes("3계층 구조. 해석 사전을 공유해 두 프론트엔드가 같은 문장을 내보냅니다.");
}

// =====================================================================
// 6. 핵심 기능 ① 부서장 리포트
// =====================================================================
{
  const s = contentSlide("Feature 01", "부서장 리포트 — 위에서 아래로 읽으면 근거까지 도달");

  s.addImage({ path: path.join(SHOTS, "02_report_hero.png"), x: M, y: 1.52, w: 7.0, h: 4.43, rounding: false });
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.52, w: 7.0, h: 4.43, rectRadius: 0.04, fill: { type: "none" }, line: { color: LINE, width: 1 },
  });

  const secs = [
    ["1", "진단 요약", "긍정·부정 Top3 영역과 주관식 경향, AI Executive Summary"],
    ["2", "카테고리별 결과", "14개 영역을 대분류 기준 좌우 분할로 동시 제시"],
    ["3", "32개 문항 근거", "문항 원문을 제목으로, 중분류 필터·정렬 지원"],
    ["4", "3개년 변화 분석", "긍정/중립/부정을 독립 축으로 확대해 미세 변화까지"],
    ["5", "AI 조직 운영 인사이트", "관찰 신호, 대화 주제, 구성원 질문 예시, 챗봇"],
  ];
  const bx = M + 7.32;
  const bw = W - 7.32;
  secs.forEach(([n, t, d], i) => {
    const y = 1.52 + i * 0.9;
    badge(s, n, bx, y, 0.38);
    s.addText(t, {
      x: bx + 0.52, y: y - 0.02, w: bw - 0.52, h: 0.28, fontFace: HEAD, fontSize: 13,
      bold: true, color: NAVY, margin: 0,
    });
    s.addText(d, {
      x: bx + 0.52, y: y + 0.26, w: bw - 0.52, h: 0.52, fontFace: BODY, fontSize: 10.5,
      color: MUTED, lineSpacing: 14, margin: 0,
    });
  });

  card(s, M, 6.16, W, 0.82, ICE);
  s.addText(
    "화면 어디에도 총점·등급·순위가 없다. 응답 비중(%)과 '어떤 대화를 해볼 수 있는지'만 남긴 것이 이 리포트의 설계 결론이다.",
    { x: M + 0.32, y: 6.34, w: W - 0.64, h: 0.5, fontFace: BODY, fontSize: 12, color: INK, margin: 0 }
  );
  s.addNotes("5단 구성. 요약에서 시작해 문항 근거까지 스크롤 한 번으로 내려갑니다.");
}

// =====================================================================
// 7. 핵심 기능 ② AI 챗봇
// =====================================================================
{
  const s = contentSlide("Feature 02", "AI 챗봇 — 질문의 성격에 따라 세 갈래로 나눈다");

  const routes = [
    ["A", "로컬 규칙 응답", POS, "짧은 키워드 조회",
      "\"가용자원\"처럼 영역명만 물으면 DB 집계와 해석 사전으로 카드를 즉시 생성한다. 외부 호출 없음."],
    ["B", "데이터 근거 LLM", CYAN, "문장형 후속 질문",
      "\"한정된 자원을 어떻게 조율할까?\"는 그 부서의 실제 수치를 컨텍스트로 넘겨 LLM이 질문에 직접 답한다."],
    ["C", "웹검색 기반 답변", WARN, "진단과 무관한 일반 질문",
      "리더십 일반론은 Tavily 검색 결과를 근거로 요약하고 출처 링크를 함께 제시한다."],
  ];
  const rw = (W - 0.36 * 2) / 3;
  routes.forEach(([k, title, col, tag, desc], i) => {
    const x = M + i * (rw + 0.36);
    card(s, x, 1.54, rw, 2.42);
    badge(s, k, x + 0.28, 1.8, 0.44, col);
    s.addText(title, {
      x: x + 0.82, y: 1.82, w: rw - 1.1, h: 0.32, fontFace: HEAD, fontSize: 14.5, bold: true,
      color: NAVY, margin: 0,
    });
    s.addShape(pres.ShapeType.roundRect, {
      x: x + 0.28, y: 2.38, w: rw - 0.56, h: 0.36, rectRadius: 0.16, fill: { color: ICE },
    });
    s.addText(tag, {
      x: x + 0.28, y: 2.38, w: rw - 0.56, h: 0.36, align: "center", valign: "middle",
      fontFace: HEAD, fontSize: 10.5, bold: true, color: BLUE, margin: 0,
    });
    s.addText(desc, {
      x: x + 0.28, y: 2.86, w: rw - 0.56, h: 0.98, fontFace: BODY, fontSize: 11,
      color: INK, lineSpacing: 16, margin: 0,
    });
  });

  // 차단 가드
  card(s, M, 4.16, 5.6, 2.1, "FDEEF0");
  s.addText("추가 장치 — 개인 특정·징계성 요청 차단", {
    x: M + 0.3, y: 4.34, w: 5.0, h: 0.3, fontFace: HEAD, fontSize: 13, bold: true, color: NEG, margin: 0,
  });
  s.addText(
    "\"부정 응답한 직급 찾아서 혼내야겠다\" 같은 요청은 세 갈래 어디로도 보내지 않고 즉시 거절한다. " +
      "데이터가 익명 집계라 특정이 불가능하다는 사실과 함께, 원인 상황을 보는 관점으로 되돌린다.",
    { x: M + 0.3, y: 4.7, w: 5.0, h: 1.3, fontFace: BODY, fontSize: 11, color: INK, lineSpacing: 16, margin: 0 }
  );

  s.addImage({ path: path.join(SHOTS, "06_chatbot.png"), x: M + 5.92, y: 4.16, w: 6.17, h: 2.55 });
  s.addNotes("질문 성격을 먼저 판별해 라우팅합니다. 키워드가 있다고 무조건 카드를 반복하지 않습니다.");
}

// =====================================================================
// 8. 핵심 기능 ③ HR 관리자 화면
// =====================================================================
{
  const s = contentSlide("Feature 03", "HR 관리자 화면 — 비교가 목적인 화면은 따로 두었다");

  s.addImage({ path: path.join(SHOTS, "08_admin_compare.png"), x: M, y: 1.52, w: 7.4, h: 4.69 });
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.52, w: 7.4, h: 4.69, rectRadius: 0.04, fill: { type: "none" }, line: { color: LINE, width: 1 },
  });

  const items = [
    ["Raw Data 업로드", "엑셀을 올리면 검증 후 DB 전체를 교체하고, 실패 시 기존 데이터를 유지한다. 기본 더미 데이터로 되돌리기도 지원."],
    ["부서별 결과 비교", "전사 평균 대비 ±3.0%p를 기준으로 우수/관심 필요를 구분한다. 점수·등급은 여기서도 쓰지 않는다."],
    ["연도별 변화 추이", "부서별 긍정 비중을 한 차트에 겹쳐 전사 흐름을 본다."],
    ["부서장 접근 이력", "로그인·챗봇·다운로드 이력을 기록해 감사 근거를 남긴다."],
  ];
  const ix = M + 7.72;
  const iw = W - 7.72;
  items.forEach(([t, d], i) => {
    const y = 1.52 + i * 1.2;
    badge(s, i + 1, ix, y, 0.38);
    s.addText(t, {
      x: ix + 0.52, y: y - 0.02, w: iw - 0.52, h: 0.28, fontFace: HEAD, fontSize: 13,
      bold: true, color: NAVY, margin: 0,
    });
    s.addText(d, {
      x: ix + 0.52, y: y + 0.28, w: iw - 0.52, h: 0.82, fontFace: BODY, fontSize: 10.5,
      color: MUTED, lineSpacing: 14, margin: 0,
    });
  });

  card(s, M, 6.42, W, 0.62, ICE);
  s.addText(
    "부서 간 비교는 HR의 업무 목적이므로 이 화면에만 남기고, 부서장 리포트에서는 전면 제거했다 — 같은 데이터라도 보는 사람에 따라 허용 범위를 다르게 설계.",
    { x: M + 0.32, y: 6.52, w: W - 0.64, h: 0.42, fontFace: BODY, fontSize: 11.5, color: INK, margin: 0 }
  );
  s.addNotes("HR 화면과 부서장 화면의 비교 허용 범위를 의도적으로 다르게 두었습니다.");
}

// =====================================================================
// 9. 디테일 ① 가드레일 구현
// =====================================================================
{
  const s = contentSlide("Detail 01", "원칙을 문서가 아니라 코드로 강제했다");

  const rows = [
    ["점수·등급·순위 미제공", "어떤 화면에도 총점/등급 필드가 존재하지 않음", "설계 단계에서 스키마에 미포함"],
    ["소수 응답 보호", "응답 10명 미만 조직은 리포트 자체를 차단", "is_suppressed() 게이트"],
    ["개인 응답 원문 미노출", "주관식은 동일 응답 빈도 Top3만 집계 후 표시", "GROUP BY text ORDER BY COUNT"],
    ["평가성 표현 금지", "14개 영역 × 긍정/중립/부정 문장을 사전으로 고정", "catalog.MID_INTERPRETATION"],
    ["개인 특정·징계 요청 차단", "징계 의도 + 특정 의도 동시 감지 시 응답 거부", "chat_service 사전 가드"],
    ["접근 이력 기록", "로그인·챗봇·다운로드를 모두 로깅해 감사 근거 확보", "access_logs 테이블"],
  ];

  s.addText("원칙", { x: M + 0.3, y: 1.56, w: 3.0, h: 0.28, fontFace: HEAD, fontSize: 11, bold: true, color: MUTED, charSpacing: 1, margin: 0 });
  s.addText("구현 방식", { x: M + 3.66, y: 1.56, w: 4.2, h: 0.28, fontFace: HEAD, fontSize: 11, bold: true, color: MUTED, charSpacing: 1, margin: 0 });
  s.addText("근거 위치", { x: M + 8.9, y: 1.56, w: 3.0, h: 0.28, fontFace: HEAD, fontSize: 11, bold: true, color: MUTED, charSpacing: 1, margin: 0 });

  rows.forEach(([a, b, c], i) => {
    const y = 1.94 + i * 0.83;
    card(s, M, y, W, 0.72, i % 2 === 0 ? WHITE : ICE);
    s.addText(a, {
      x: M + 0.3, y: y + 0.2, w: 3.3, h: 0.34, fontFace: HEAD, fontSize: 12, bold: true, color: NAVY, margin: 0,
    });
    s.addText(b, {
      x: M + 3.66, y: y + 0.2, w: 5.1, h: 0.36, fontFace: BODY, fontSize: 11.5, color: INK, margin: 0,
    });
    s.addText(c, {
      x: M + 8.9, y: y + 0.22, w: 3.0, h: 0.32, fontFace: BODY, fontSize: 10, color: MUTED, italic: true, margin: 0,
    });
  });
  s.addNotes("가드레일 6가지가 각각 어디에 구현되어 있는지 대응표입니다.");
}

// =====================================================================
// 10. 디테일 ② 비교 기준 재설계
// =====================================================================
{
  const s = contentSlide("Detail 02", "지침 한 줄이 바뀌자 해석 로직을 통째로 다시 짰다");

  card(s, M, 1.5, W, 0.86, "FFF7E8");
  s.addText(
    "\"부서 간 비교를 지양해야 한다\"  —  프로젝트 중반 HR 부서로부터 전달받은 지침",
    { x: M + 0.34, y: 1.66, w: W - 0.68, h: 0.5, fontFace: HEAD, fontSize: 14, bold: true, color: "8A5A00", margin: 0 }
  );

  // Before
  card(s, M, 2.6, 5.72, 2.2, WHITE);
  s.addShape(pres.ShapeType.roundRect, { x: M + 0.28, y: 2.82, w: 1.1, h: 0.34, rectRadius: 0.16, fill: { color: NEG } });
  s.addText("BEFORE", { x: M + 0.28, y: 2.82, w: 1.1, h: 0.34, align: "center", valign: "middle", fontFace: HEAD, fontSize: 9.5, bold: true, color: WHITE, margin: 0 });
  s.addText("전사 평균과 비교", {
    x: M + 1.52, y: 2.84, w: 3.8, h: 0.3, fontFace: HEAD, fontSize: 14, bold: true, color: INK, margin: 0,
  });
  s.addText(
    "\"전사 평균 대비 긍정 응답 비중이 +12.5%p 높습니다\"\n\n→ 부서장이 자기 부서의 순위를 역산할 수 있고, 사실상 부서 간 비교로 읽힌다.",
    { x: M + 0.3, y: 3.3, w: 5.12, h: 1.34, fontFace: BODY, fontSize: 11.5, color: MUTED, lineSpacing: 17, margin: 0 }
  );

  // After
  card(s, M + 6.0, 2.6, 6.09, 2.2, ICE);
  s.addShape(pres.ShapeType.roundRect, { x: M + 6.28, y: 2.82, w: 1.1, h: 0.34, rectRadius: 0.16, fill: { color: POS } });
  s.addText("AFTER", { x: M + 6.28, y: 2.82, w: 1.1, h: 0.34, align: "center", valign: "middle", fontFace: HEAD, fontSize: 9.5, bold: true, color: WHITE, margin: 0 });
  s.addText("우리 부서 내부에서만 비교", {
    x: M + 7.52, y: 2.84, w: 4.2, h: 0.3, fontFace: HEAD, fontSize: 14, bold: true, color: INK, margin: 0,
  });
  s.addText(
    "\"대분류(회사 지원 수준) 내 다른 영역 평균 대비 -14.9%p 낮습니다\"\n\n→ 비교 대상이 우리 부서 안에 머물러, 다른 부서를 추론할 여지가 없다.",
    { x: M + 6.3, y: 3.3, w: 5.49, h: 1.34, fontFace: BODY, fontSize: 11.5, color: INK, lineSpacing: 17, margin: 0 }
  );

  // fallback 설명
  s.addText("비교 대상이 없을 때를 대비한 3단 폴백", {
    x: M, y: 5.06, w: W, h: 0.32, fontFace: HEAD, fontSize: 14, bold: true, color: NAVY, margin: 0,
  });
  const fb = [
    ["1순위", "같은 중분류 안의 다른 문항 평균", "문항 단위 비교의 기본값"],
    ["2순위", "같은 대분류 안의 다른 문항 평균", "중분류에 문항이 1개뿐인 경우 (예: 리더에 대한 신뢰)"],
    ["3순위", "비교 없이 분포만 서술", "비교 대상이 아예 없을 때"],
  ];
  const fw = (W - 0.3 * 2) / 3;
  fb.forEach(([k, t, d], i) => {
    const x = M + i * (fw + 0.3);
    card(s, x, 5.46, fw, 1.4, WHITE);
    s.addText(k, {
      x: x + 0.26, y: 5.62, w: fw - 0.5, h: 0.26, fontFace: HEAD, fontSize: 10.5, bold: true, color: CYAN, charSpacing: 1, margin: 0,
    });
    s.addText(t, {
      x: x + 0.26, y: 5.9, w: fw - 0.5, h: 0.32, fontFace: HEAD, fontSize: 12.5, bold: true, color: NAVY, margin: 0,
    });
    s.addText(d, {
      x: x + 0.26, y: 6.24, w: fw - 0.5, h: 0.5, fontFace: BODY, fontSize: 10, color: MUTED, lineSpacing: 13, margin: 0,
    });
  });
  s.addNotes("단순히 문구만 바꾼 게 아니라, 비교 대상 산출 함수와 폴백 규칙을 새로 설계했습니다.");
}

// =====================================================================
// 11. 디테일 ③ 시각화 정교화
// =====================================================================
{
  const s = contentSlide("Detail 03", "보기 좋은 화면은 버그 세 개를 잡은 결과였다");

  const bugs = [
    ["막대 시작 위치가 문항마다 달랐다",
      "문항 원문을 차트의 y축 라벨로 쓰다 보니, 글자 길이에 따라 막대 시작점이 밀렸다.",
      "y축 라벨을 없애고 문항을 HTML 제목으로 분리 → 모든 막대가 같은 x에서 시작 (실측 32개 전부 952px 동일)"],
    ["좁은 구간의 수치가 사라졌다",
      "Plotly는 스택 막대에서 글자가 안 들어가면 라벨을 통째로 감춘다. 바깥 배치도 지원하지 않는다.",
      "11% 미만 구간은 막대 오른쪽 고정폭 칸에 주석으로 표시. 웹앱에서는 렌더링 후 실제 폭을 재서 자동 이동"],
    ["한글이 음절 단위로 잘렸다",
      "브라우저는 한글에 CJK 줄바꿈 규칙을 적용해 아무 글자 사이에서나 줄을 바꾼다.",
      "word-break: keep-all로 어절 단위 줄바꿈. 긴 URL 대비 overflow-wrap을 안전망으로 병행"],
  ];
  const bw = (W - 0.36 * 2) / 3;
  bugs.forEach(([t, cause, fix], i) => {
    const x = M + i * (bw + 0.36);
    card(s, x, 1.54, bw, 4.5);
    badge(s, i + 1, x + 0.28, 1.8, 0.42, NEG);
    s.addText(t, {
      x: x + 0.28, y: 2.36, w: bw - 0.56, h: 0.62, fontFace: HEAD, fontSize: 13.5, bold: true,
      color: NAVY, lineSpacing: 19, margin: 0,
    });
    s.addText("원인", {
      x: x + 0.28, y: 3.06, w: bw - 0.56, h: 0.24, fontFace: HEAD, fontSize: 10, bold: true, color: MUTED, charSpacing: 1, margin: 0,
    });
    s.addText(cause, {
      x: x + 0.28, y: 3.32, w: bw - 0.56, h: 0.92, fontFace: BODY, fontSize: 11, color: INK, lineSpacing: 16, margin: 0,
    });
    s.addShape(pres.ShapeType.roundRect, {
      x: x + 0.28, y: 4.32, w: bw - 0.56, h: 1.5, rectRadius: 0.07, fill: { color: ICE },
    });
    s.addText("해결", {
      x: x + 0.46, y: 4.44, w: bw - 0.92, h: 0.24, fontFace: HEAD, fontSize: 10, bold: true, color: BLUE, charSpacing: 1, margin: 0,
    });
    s.addText(fix, {
      x: x + 0.46, y: 4.7, w: bw - 0.92, h: 1.0, fontFace: BODY, fontSize: 10.5, color: INK, lineSpacing: 15, margin: 0,
    });
  });

  card(s, M, 6.22, W, 0.76, "FFFFFF");
  s.addText(
    "세 가지 모두 '기능은 동작하는데 보기 불편한' 문제였다. 브라우저에서 실제 렌더링 폭을 측정해 원인을 특정하고, 수치로 확인한 뒤 종료했다.",
    { x: M + 0.32, y: 6.38, w: W - 0.64, h: 0.46, fontFace: BODY, fontSize: 11.5, color: INK, margin: 0 }
  );
  s.addNotes("실측 기반으로 원인을 찾고 고쳤다는 점이 핵심입니다.");
}

// =====================================================================
// 12. 디테일 ④ 운영 확장성
// =====================================================================
{
  const s = contentSlide("Detail 04", "내년에 코드를 열지 않아도 되게 만들었다");

  // 좌: 연도 확장
  card(s, M, 1.52, 7.4, 2.72);
  badge(s, "Y", M + 0.3, 1.78, 0.44, CYAN);
  s.addText("연도 구조 일반화 — 2027년 대비", {
    x: M + 0.86, y: 1.82, w: 6.2, h: 0.32, fontFace: HEAD, fontSize: 15, bold: true, color: NAVY, margin: 0,
  });
  s.addText(
    "연도가 [\"2024\",\"2025\",\"2026\"]으로 코드에 박혀 있었다. 내년 2027 시트가 추가된 파일을 올리면 조용히 무시될 상황이었다.",
    { x: M + 0.32, y: 2.3, w: 6.8, h: 0.62, fontFace: BODY, fontSize: 11.5, color: MUTED, lineSpacing: 16, margin: 0 }
  );
  s.addText(
    [
      { text: "워크북의 시트 이름에서 4자리 연도를 자동 인식", options: { bullet: true, breakLine: true } },
      { text: "리포트 기준 연도는 DB에 적재된 최신 연도를 매번 조회", options: { bullet: true, breakLine: true } },
      { text: "추이 차트·섹션 제목·다운로드 파일명까지 모두 연동", options: { bullet: true } },
    ],
    { x: M + 0.32, y: 2.98, w: 6.8, h: 1.1, fontFace: BODY, fontSize: 11.5, color: INK, paraSpaceAfter: 6, margin: 0 }
  );

  // 검증 결과
  card(s, M + 7.72, 1.52, W - 7.72, 2.72, ICE);
  s.addText("실증 검증", {
    x: M + 8.0, y: 1.76, w: 3.6, h: 0.3, fontFace: HEAD, fontSize: 13, bold: true, color: BLUE, margin: 0,
  });
  s.addText(
    "2027 시트를 추가한 4개년 파일을 실제로 업로드해, 코드 수정 없이 전 화면이 자동 확장되는 것을 확인",
    { x: M + 8.0, y: 2.1, w: 3.8, h: 0.66, fontFace: BODY, fontSize: 11, color: INK, lineSpacing: 15, margin: 0 }
  );
  const proofs = ["섹션 제목 → 4개년 (2024–2027)", "추이 차트 x축 → 2027까지", "파일명 → ..._2027_리포트.html"];
  s.addText(
    proofs.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < proofs.length - 1 } })),
    { x: M + 8.0, y: 2.84, w: 3.8, h: 1.2, fontFace: BODY, fontSize: 10.5, color: BLUE, paraSpaceAfter: 6, margin: 0 }
  );

  // 하단: 세션 문제
  card(s, M, 4.44, W, 2.5);
  badge(s, "S", M + 0.3, 4.7, 0.44, WARN);
  s.addText("대화 기록이 첫 문답만 남던 문제 — 원인은 쿠키 용량 한계였다", {
    x: M + 0.86, y: 4.74, w: 10.8, h: 0.32, fontFace: HEAD, fontSize: 15, bold: true, color: NAVY, margin: 0,
  });
  const flow = [
    ["증상", "리포트를 내려받으면 대화 기록에 최초 질문 1개만 남아 있음", NEG],
    ["원인", "Starlette 세션은 전체를 서명 쿠키에 담는 방식 — AI 답변 두어 개면 4KB 한계 초과", WARN],
    ["조치", "대화를 chat_messages 테이블로 이전, 쿠키에는 짧은 세션 토큰만 유지", POS],
  ];
  const flw = (W - 0.3 * 2) / 3;
  flow.forEach(([k, d, col], i) => {
    const x = M + i * (flw + 0.3);
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 5.24, w: flw, h: 1.5, rectRadius: 0.07, fill: { color: BG }, line: { color: LINE, width: 1 },
    });
    s.addShape(pres.ShapeType.roundRect, { x: x + 0.24, y: 5.42, w: 0.72, h: 0.3, rectRadius: 0.14, fill: { color: col } });
    s.addText(k, { x: x + 0.24, y: 5.42, w: 0.72, h: 0.3, align: "center", valign: "middle", fontFace: HEAD, fontSize: 9.5, bold: true, color: WHITE, margin: 0 });
    s.addText(d, {
      x: x + 0.24, y: 5.8, w: flw - 0.48, h: 0.86, fontFace: BODY, fontSize: 10.5, color: INK, lineSpacing: 15, margin: 0,
    });
  });
  s.addNotes("겉으로는 UI 버그처럼 보였지만 실제 원인은 프레임워크의 세션 저장 방식이었습니다.");
}

// =====================================================================
// 13. 정량 결과 (차트)
// =====================================================================
{
  const s = contentSlide("Results", "해석이 실제로 갈리는지 수치로 확인했다");

  // 좌: 차트
  card(s, M, 1.52, 6.7, 4.1);
  s.addText("부서별 긍정 응답 비중 (2026)", {
    x: M + 0.32, y: 1.72, w: 6.0, h: 0.32, fontFace: HEAD, fontSize: 13.5, bold: true, color: NAVY, margin: 0,
  });
  s.addChart(
    pres.ChartType.bar,
    [{
      name: "긍정 응답 비중",
      labels: ["철강사업실", "철강설계실", "기술기획실", "플랜트설계실", "건설전략실", "경영혁신실"],
      values: [73.6, 73.5, 59.2, 58.2, 53.0, 52.4],
    }],
    {
      x: M + 0.22, y: 2.12, w: 6.26, h: 3.32,
      barDir: "col",
      chartColors: [BLUE],
      showValue: true, dataLabelPosition: "outEnd",
      dataLabelColor: INK, dataLabelFontSize: 10, dataLabelFontFace: BODY,
      showLegend: false,
      catAxisLabelColor: MUTED, catAxisLabelFontSize: 9.5, catAxisLabelFontFace: BODY,
      valAxisLabelColor: MUTED, valAxisLabelFontSize: 9.5,
      valAxisMaxVal: 90, valAxisMinVal: 0,
      valGridLine: { color: LINE, size: 1 },
      catGridLine: { style: "none" },
    }
  );

  // 우: 개선 지표
  const gains = [
    ["더미 데이터 편차 주입", "\"비슷한 수준\" 문구 비율", "64%", "18%", POS],
    ["대화 기록 저장 방식 전환", "다운로드에 남는 문답 수", "1턴", "전체", POS],
    ["막대 정렬 개선", "문항별 막대 폭 편차", "3종", "1종", POS],
  ];
  const gx = M + 6.94;
  const gw = W - 6.94;
  s.addText("개선 전후 비교", {
    x: gx, y: 1.52, w: gw, h: 0.32, fontFace: HEAD, fontSize: 13.5, bold: true, color: NAVY, margin: 0,
  });
  gains.forEach(([title, metric, before, after, col], i) => {
    const y = 1.96 + i * 1.24;
    card(s, gx, y, gw, 1.06, WHITE);
    s.addText(title, {
      x: gx + 0.26, y: y + 0.14, w: gw - 0.52, h: 0.26, fontFace: HEAD, fontSize: 11.5, bold: true, color: NAVY, margin: 0,
    });
    s.addText(metric, {
      x: gx + 0.26, y: y + 0.4, w: gw - 0.52, h: 0.22, fontFace: BODY, fontSize: 9.5, color: MUTED, margin: 0,
    });
    s.addText(before, {
      x: gx + 0.26, y: y + 0.62, w: 1.3, h: 0.34, fontFace: HEAD, fontSize: 16, bold: true, color: MUTED, margin: 0,
    });
    s.addShape(pres.ShapeType.rightArrow, { x: gx + 1.56, y: y + 0.74, w: 0.26, h: 0.14, fill: { color: MUTED } });
    s.addText(after, {
      x: gx + 1.94, y: y + 0.62, w: 1.6, h: 0.34, fontFace: HEAD, fontSize: 16, bold: true, color: col, margin: 0,
    });
  });

  card(s, M, 5.82, W, 1.12, ICE);
  s.addText(
    "시연 중 \"대부분의 답변이 비슷한 수준이라 단조롭다\"는 피드백을 받고, 조직×중분류마다 목표 편차(±13~17%p)를 부여해 더미 데이터를 재생성했다. " +
      "편차는 대분류 안에서 상쇄되도록 설계해, 부서 전체 평균과 HR 화면의 부서 간 비교 결과는 그대로 유지된다.",
    { x: M + 0.32, y: 5.98, w: W - 0.64, h: 0.82, fontFace: BODY, fontSize: 11.5, color: INK, lineSpacing: 17, margin: 0 }
  );
  s.addNotes("피드백을 받은 뒤 데이터를 다시 만들되, 다른 화면의 결론이 흔들리지 않도록 제약을 걸었습니다.");
}

// =====================================================================
// 14. 기술 스택
// =====================================================================
{
  const s = contentSlide("Tech Stack", "프로토타입에서 운영형 웹앱으로");

  const cols = [
    ["프로토타입", "Streamlit", MUTED, [
      "Python 단일 파일로 화면 구성",
      "Plotly 차트 · st.session_state",
      "엑셀 직접 로드 + 캐시",
      "→ 문구와 화면 구성 검증에 사용",
    ]],
    ["운영형 웹앱", "FastAPI + SQLite", BLUE, [
      "Jinja2 서버 렌더링 · 서명 쿠키 세션",
      "Chart.js 로컬 번들 (오프라인 동작)",
      "SQLite 5개 테이블 · 인덱스 기반 집계",
      "→ 업로드·세션·감사 로그까지 지원",
    ]],
    ["AI 계층", "OpenAI + Tavily", CYAN, [
      "데이터 근거 답변 (진단 컨텍스트 주입)",
      "웹검색 기반 일반 자문 + 출처 표기",
      "대화 요약 서브 에이전트",
      "→ 키가 없으면 규칙 기반으로 자동 폴백",
    ]],
  ];
  const cw2 = (W - 0.36 * 2) / 3;
  cols.forEach(([kicker, name, col, items], i) => {
    const x = M + i * (cw2 + 0.36);
    card(s, x, 1.54, cw2, 3.5);
    s.addText(kicker.toUpperCase(), {
      x: x + 0.3, y: 1.8, w: cw2 - 0.6, h: 0.26, fontFace: HEAD, fontSize: 10, bold: true, color: col, charSpacing: 1.4, margin: 0,
    });
    s.addText(name, {
      x: x + 0.3, y: 2.08, w: cw2 - 0.6, h: 0.4, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY, margin: 0,
    });
    s.addText(
      items.map((t, k) => ({ text: t, options: { bullet: k < items.length - 1, breakLine: k < items.length - 1 } })),
      { x: x + 0.3, y: 2.6, w: cw2 - 0.6, h: 2.2, fontFace: BODY, fontSize: 11, color: INK, paraSpaceAfter: 8, margin: 0 }
    );
  });

  // 하단 수치
  const nums = [
    ["5,033", "라인 (앱 코드)"],
    ["13", "커밋"],
    ["9", "화면·기능 문서"],
    ["37,248", "적재 응답 레코드"],
  ];
  const nw = (W - 0.3 * 3) / 4;
  nums.forEach(([v, k], i) => {
    const x = M + i * (nw + 0.3);
    card(s, x, 5.24, nw, 1.2, ICE);
    s.addText(v, {
      x: x + 0.26, y: 5.42, w: nw - 0.5, h: 0.5, fontFace: HEAD, fontSize: 24, bold: true, color: BLUE, margin: 0,
    });
    s.addText(k, {
      x: x + 0.26, y: 5.94, w: nw - 0.5, h: 0.28, fontFace: BODY, fontSize: 10.5, color: MUTED, margin: 0,
    });
  });
  s.addNotes("두 버전 모두 저장소에 남아 있고, 해석 사전 모듈은 공유합니다.");
}

// =====================================================================
// 15. 한계와 향후 과제
// =====================================================================
{
  const s = contentSlide("Next Steps", "지금은 데모, 운영으로 가려면 남은 것들");

  const now = [
    ["인증", "조직 선택 + 생년월일 6자리", "사내 SSO 연동 및 권한 매핑"],
    ["데이터", "합성 더미 데이터 6개 부서", "실제 설문 결과 연동 및 조직 마스터 동기화"],
    ["보안", "SHA-256 해시 · 로컬 세션", "bcrypt/argon2 · 서버 세션 스토어 · 전송 암호화"],
    ["AI 비용", "질문마다 외부 API 호출", "응답 캐싱 및 호출량 상한 정책"],
    ["운영", "단일 프로세스 로컬 구동", "다중 워커 구성 및 DB 이관(PostgreSQL 등)"],
  ];

  s.addText("현재 (데모)", { x: M + 4.0, y: 1.56, w: 3.6, h: 0.28, fontFace: HEAD, fontSize: 11, bold: true, color: MUTED, charSpacing: 1, margin: 0 });
  s.addText("운영 전환 시 필요한 것", { x: M + 7.9, y: 1.56, w: 4.2, h: 0.28, fontFace: HEAD, fontSize: 11, bold: true, color: CYAN, charSpacing: 1, margin: 0 });

  now.forEach(([area, cur, next], i) => {
    const y = 1.94 + i * 0.94;
    card(s, M, y, W, 0.82, i % 2 === 0 ? WHITE : ICE);
    s.addText(area, {
      x: M + 0.3, y: y + 0.24, w: 3.4, h: 0.34, fontFace: HEAD, fontSize: 13, bold: true, color: NAVY, margin: 0,
    });
    s.addText(cur, {
      x: M + 4.0, y: y + 0.26, w: 3.7, h: 0.34, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0,
    });
    s.addShape(pres.ShapeType.rightArrow, { x: M + 7.62, y: y + 0.36, w: 0.2, h: 0.12, fill: { color: CYAN } });
    s.addText(next, {
      x: M + 7.9, y: y + 0.26, w: 4.2, h: 0.34, fontFace: BODY, fontSize: 11, color: INK, margin: 0,
    });
  });

  card(s, M, 6.62, W, 0.62, "FFF7E8");
  s.addText(
    "본 결과물은 사외 시연용 데모이며, 실제 설문 데이터가 아닌 합성 데이터를 사용했다.",
    { x: M + 0.32, y: 6.72, w: W - 1.5, h: 0.42, fontFace: BODY, fontSize: 11, color: "8A5A00", margin: 0 }
  );
  s.addNotes("데모와 운영의 간극을 솔직하게 정리했습니다.");
}

// =====================================================================
// 16. 클로징
// =====================================================================
{
  pageNo += 1;
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addShape(pres.ShapeType.ellipse, { x: -2.2, y: 3.4, w: 6.6, h: 6.6, fill: { color: BLUE, transparency: 55 } });
  s.addShape(pres.ShapeType.ellipse, { x: 10.2, y: -2.4, w: 5.6, h: 5.6, fill: { color: CYAN, transparency: 78 } });

  s.addText("이 프로젝트가 지킨 한 가지", {
    x: M, y: 2.05, w: 9.5, h: 0.34, fontFace: HEAD, fontSize: 13, bold: true, color: CYAN, charSpacing: 1.4, margin: 0,
  });
  s.addText("\"이 화면이 누군가를\n평가하는 데 쓰이지 않는다\"", {
    x: M, y: 2.5, w: 10.2, h: 1.9, fontFace: HEAD, fontSize: 38, bold: true, color: WHITE, lineSpacing: 50, margin: 0,
  });
  s.addText(
    "기능을 하나 더할지 판단이 설 때마다 이 기준으로 되돌아갔다. 점수를 넣지 않은 것도, 부서 간 비교를 없앤 것도, " +
      "개인을 특정하려는 질문을 거절하는 것도 모두 같은 이유에서 내린 결정이다.",
    { x: M, y: 4.6, w: 9.6, h: 0.9, fontFace: BODY, fontSize: 14, color: "AFC6DE", lineSpacing: 24, margin: 0 }
  );
  s.addText("2026 조직건강도 AI Agent  ·  프로젝트 수행 결과 보고", {
    x: M, y: 6.6, w: 9.6, h: 0.34, fontFace: BODY, fontSize: 11, color: "7E9CBC", margin: 0,
  });
  s.addNotes("설계 원칙 하나로 마무리합니다.");
}

const out = path.join(__dirname, "2026_조직건강도_AI_Agent_수행결과.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("WROTE:", out));
