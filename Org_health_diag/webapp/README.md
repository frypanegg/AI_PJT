# 조직건강도 진단 웹앱 (FastAPI + SQLite)

Streamlit 데모를 로컬 구동형 웹앱으로 전환한 버전. 화면 구성과 해석 로직은 동일하고,
데이터 저장소가 엑셀 직접 읽기에서 **SQLite**로, 프레임워크가 **FastAPI + Jinja2**로 바뀌었다.

## 실행

```bash
cd Org_health_diag/webapp
pip install -r requirements.txt
python seed.py                    # 최초 1회: 엑셀 → SQLite 적재
uvicorn main:app --port 8000
```

접속: <http://localhost:8000>

`seed.py`를 건너뛰어도 앱 기동 시 DB가 비어 있으면 자동으로 적재한다.

## 계정

| 구분 | 접속 | 계정 |
| --- | --- | --- |
| 부서장 | `/` | 조직 선택 + 생년월일 6자리 (`DEMO_GUIDE.md` 참조) |
| 관리자 | `/admin/login` | `sum` / `sum1420` |

개인화 링크: `http://localhost:8000/?org=ss` (org 코드는 `DEMO_GUIDE.md`)

## 구조

```
webapp/
├── main.py           FastAPI 라우팅 · 세션 인증 · API
├── db.py             SQLite 스키마/커넥션
├── seed.py           엑셀 → SQLite 적재 (업로드 시에도 재사용)
├── analytics.py      SQL 집계 + 부서 내부 비교 해석
├── chat_service.py   챗봇 라우팅 (로컬 규칙 → 웹검색 위임)
├── templates/        login · admin_login · report · admin
├── static/           style.css · report.js · admin.js · vendor/chart.umd.min.js
└── org_health.db     SQLite (자동 생성, git 제외)
```

`catalog.py` · `insights_questions.py` · `web_advisor.py` · `report_export.py` 는
`../streamlit_app/` 의 모듈을 그대로 재사용한다 (해석 사전을 한 곳에서 관리하기 위함).

## DB 스키마

| 테이블 | 내용 |
| --- | --- |
| `orgs` | 회사·부서·조직장·인증코드·대상인원 |
| `admins` | 관리자 계정 (SHA-256 해시) |
| `responses` | 객관식 응답 long format (1행 = 1인 1문항) |
| `open_texts` | 주관식 응답 |
| `access_logs` | 로그인·챗봇·다운로드 접근 이력 |

## 주요 엔드포인트

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | `/` | 부서장 로그인 (`?org=` 로 사전 선택) |
| POST | `/login` | 조직 + 생년월일 인증 |
| GET | `/report` | 부서장 리포트 (5개 섹션) |
| GET | `/admin/login`, `/admin` | 관리자 로그인 · 대시보드 |
| POST | `/api/chat` | 챗봇 질의 (JSON) |
| GET | `/api/report/download` | 리포트 HTML 다운로드 |
| POST | `/admin/upload` | Raw Data 엑셀 업로드 |
| POST | `/admin/reset-data` | 기본 더미 데이터로 되돌리기 |
| GET | `/healthz` | 헬스체크 |

## 환경 변수

상위 폴더 `.env`를 자동으로 읽는다.

| 키 | 용도 | 없을 때 |
| --- | --- | --- |
| `OPENAI_API_KEY` | 챗봇 웹검색 답변 생성 | 웹검색 기능만 비활성, 나머지는 정상 |
| `TAVILY_API_KEY` | 웹 검색 | 동일 |
| `SESSION_SECRET` | 세션 서명 키 (선택) | 최초 실행 시 자동 생성해 `.session_secret`에 보관 |

## Streamlit 버전과의 차이

- 데이터: 엑셀 직접 읽기 → SQLite (인덱스 기반 집계)
- 업로드: 파일 교체 → DB 테이블 교체 (트랜잭션)
- 접근 로그: CSV → `access_logs` 테이블
- 차트: Plotly → Chart.js (로컬 vendor, 오프라인 동작)
- 세션: `st.session_state` → 서명 쿠키 세션

두 버전은 포트가 달라 동시에 띄울 수 있다 (Streamlit 8502 / FastAPI 8000).
