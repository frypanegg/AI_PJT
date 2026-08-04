# -*- coding: utf-8 -*-
"""2026 조직건강도 진단 — FastAPI 웹앱.

로컬 구동용. Streamlit 데모와 동일한 화면·해석 로직을 FastAPI + SQLite로 옮긴 것.

실행:  uvicorn main:app --port 8000     (webapp 디렉터리에서)
"""

import os
import secrets
import sys
import tempfile
import urllib.parse

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "streamlit_app"))

import report_export  # noqa: E402

import analytics  # noqa: E402
import chat_service  # noqa: E402
import db  # noqa: E402
import seed  # noqa: E402

BASE_DIR = os.path.dirname(__file__)
SECRET_FILE = os.path.join(BASE_DIR, ".session_secret")


def get_session_secret() -> str:
    """세션 서명 키. .env에 없으므로 최초 실행 시 생성해 로컬 파일에 보관한다."""
    env_secret = os.environ.get("SESSION_SECRET")
    if env_secret:
        return env_secret
    if os.path.exists(SECRET_FILE):
        return open(SECRET_FILE, encoding="utf-8").read().strip()
    generated = secrets.token_urlsafe(48)
    with open(SECRET_FILE, "w", encoding="utf-8") as f:
        f.write(generated)
    return generated


app = FastAPI(title="2026 조직건강도 진단")
app.add_middleware(SessionMiddleware, secret_key=get_session_secret(), https_only=False)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.on_event("startup")
def startup():
    """DB가 비어 있으면 기본 더미 데이터로 부트스트랩한다."""
    if not db.db_exists():
        seed.bootstrap()


# ---------------------------------------------------------------------------
# 인증 헬퍼
# ---------------------------------------------------------------------------

def current_org_key(request: Request) -> str | None:
    return request.session.get("org_key")


def is_admin(request: Request) -> bool:
    return bool(request.session.get("is_admin"))


def require_org(request: Request) -> str:
    org_key = current_org_key(request)
    if not org_key:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return org_key


def require_admin(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=401, detail="관리자 로그인이 필요합니다.")


# ---------------------------------------------------------------------------
# 화면
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request, org: str = ""):
    if is_admin(request):
        return RedirectResponse("/admin", status_code=303)
    if current_org_key(request):
        return RedirectResponse("/report", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"orgs": analytics.list_orgs(), "preselect": org, "error": None},
    )


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, org_key: str = Form(...), birth_code: str = Form(...)):
    code = birth_code.strip()
    if len(code) != 6 or not code.isdigit():
        error = "생년월일 6자리 숫자를 정확히 입력해 주세요."
    elif analytics.verify_org_login(org_key, code):
        org = analytics.get_org(org_key)
        request.session["org_key"] = org_key
        analytics.log_access(org_key, org["org"], "login_success")
        return RedirectResponse("/report", status_code=303)
    else:
        org = analytics.get_org(org_key)
        analytics.log_access(org_key, org["org"] if org else None, "login_failed")
        error = "조직 또는 생년월일 정보가 일치하지 않습니다."

    return templates.TemplateResponse(
        request,
        "login.html",
        {"orgs": analytics.list_orgs(), "preselect": org_key, "error": error},
        status_code=400,
    )


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    if is_admin(request):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(request, "admin_login.html", {"error": None})


@app.post("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request, admin_id: str = Form(...), password: str = Form(...)):
    if analytics.verify_admin(admin_id, password):
        request.session["is_admin"] = True
        analytics.log_access(None, None, "admin_login_success")
        return RedirectResponse("/admin", status_code=303)
    analytics.log_access(None, None, "admin_login_failed")
    return templates.TemplateResponse(
        request,
        "admin_login.html",
        {"error": "ID 또는 비밀번호가 일치하지 않습니다."},
        status_code=400,
    )


@app.get("/logout")
def logout(request: Request):
    org_key = current_org_key(request)
    if org_key:
        org = analytics.get_org(org_key)
        analytics.log_access(org_key, org["org"] if org else None, "logout")
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/report", response_class=HTMLResponse)
def report_page(request: Request):
    org_key = current_org_key(request)
    if not org_key:
        return RedirectResponse("/", status_code=303)
    payload = analytics.report_payload(org_key)
    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "p": payload,
            "web_tool": chat_service.web_tool_available(),
            "disclaimer": chat_service.DISCLAIMER,
            "welcome": chat_service.WELCOME.format(org=payload.get("org", "")),
        },
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "a": analytics.admin_payload(),
            "data_source": request.session.pop("upload_result", None),
        },
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def api_chat(request: Request):
    org_key = require_org(request)
    body = await request.json()
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    result = chat_service.respond(message, org_key)
    org = analytics.get_org(org_key)
    analytics.log_access(org_key, org["org"], "chat_message")
    return JSONResponse(result)


@app.get("/api/report/download")
def api_download(request: Request):
    org_key = require_org(request)
    payload = analytics.report_payload(org_key)
    if payload.get("suppressed"):
        raise HTTPException(status_code=403, detail="소수 응답 보호로 다운로드할 수 없습니다.")

    import pandas as pd

    history = request.session.get("chat_history", [])
    html = report_export.build_report_html(
        org=payload["org"],
        company=payload["company"],
        overall=payload["overall"],
        top_pos_df=pd.DataFrame(payload["top_pos"]),
        top_neg_df=pd.DataFrame(payload["top_neg"]),
        executive_summary=payload["executive_summary"],
        chat_history=[(m["role"], m["text"]) for m in history],
        year=payload["year"],
    )
    analytics.log_access(org_key, payload["org"], "report_download")
    filename = f"{payload['org']}_{payload['year']}_조직건강도_리포트.html"
    return Response(
        content=html.encode("utf-8"),
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename*=UTF-8''"
            + urllib.parse.quote(filename)
        },
    )


@app.post("/api/chat/history")
async def api_save_history(request: Request):
    require_org(request)
    body = await request.json()
    request.session["chat_history"] = body.get("history", [])[-40:]
    return JSONResponse({"ok": True})


@app.post("/admin/upload")
async def admin_upload(request: Request, file: UploadFile = File(...)):
    require_admin(request)
    if not file.filename.lower().endswith(".xlsx"):
        request.session["upload_result"] = {"ok": False, "msg": "xlsx 파일만 업로드할 수 있습니다."}
        return RedirectResponse("/admin", status_code=303)

    content = await file.read()
    tmp_path = os.path.join(tempfile.gettempdir(), "org_health_upload.xlsx")
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        stats = seed.load_workbook(tmp_path, replace=True)
        request.session["upload_result"] = {
            "ok": True,
            "msg": (
                f"'{file.filename}' 적용 완료 — 연도 {', '.join(stats['years'])}, "
                f"응답 {stats['responses']}건, 주관식 {stats['open_texts']}건, "
                f"{stats['latest_year']}년 조직 {stats['orgs_latest_year']}개"
            ),
        }
        analytics.log_access(None, None, "raw_data_upload")
    except Exception as exc:
        request.session["upload_result"] = {
            "ok": False,
            "msg": f"적용하지 못했습니다: {exc}",
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/reset-data")
def admin_reset(request: Request):
    require_admin(request)
    stats = seed.load_workbook(seed.DEFAULT_EXCEL, replace=True)
    request.session["upload_result"] = {
        "ok": True,
        "msg": f"기본 더미 데이터로 되돌렸습니다 — 응답 {stats['responses']}건",
    }
    return RedirectResponse("/admin", status_code=303)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "db": os.path.basename(db.DB_PATH)}
