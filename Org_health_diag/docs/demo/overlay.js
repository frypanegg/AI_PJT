/* 시연 영상용 오버레이 툴킷.
 *
 * Playwright의 add_init_script로 앱 페이지마다 주입된다. 별도 플레이어 페이지를
 * iframe으로 띄우면 file:// ↔ http:// 교차 출처 때문에 내부 제어가 막히므로,
 * 앱 페이지 위에 고정 레이어를 직접 얹는 방식을 쓴다.
 *
 * 페이지 이동(로그인 → 리포트 등) 중에도 간지/자막이 끊기지 않도록 상태를
 * sessionStorage에 두고, 새 문서가 뜨는 즉시 같은 화면을 복원한다.
 */
(() => {
  if (window.__demoInstalled) return;
  window.__demoInstalled = true;

  const SS = {
    get(k, d) { try { const v = sessionStorage.getItem("dm." + k); return v ? JSON.parse(v) : d; } catch { return d; } },
    set(k, v) { try { sessionStorage.setItem("dm." + k, JSON.stringify(v)); } catch {} },
    del(k) { try { sessionStorage.removeItem("dm." + k); } catch {} },
  };

  const CSS = `
  #dm-root, #dm-root * { box-sizing: border-box; margin: 0; padding: 0;
    font-family: "Noto Sans KR","Malgun Gothic",sans-serif; word-break: keep-all; }
  #dm-root { position: fixed; inset: 0; z-index: 2147483600; pointer-events: none; }

  #dm-cover { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    text-align: center; opacity: 0; transition: opacity .8s ease;
    background: linear-gradient(110deg,#002d5a 0%,#004381 42%,#0098d9 82%,#8acfff 100%); }
  #dm-cover.on { opacity: 1; }
  #dm-cover::after { content:""; position:absolute; inset:0;
    background: linear-gradient(118deg,transparent 54%,rgba(255,255,255,.14) 61%,transparent 69%); }
  #dm-cover .in { position: relative; z-index: 2; max-width: 1300px; padding: 0 70px; }

  #dm-k { font-size: 21px; font-weight: 700; letter-spacing: .22em; color: #9ed2f5; margin-bottom: 24px; }
  #dm-n { font-size: 120px; font-weight: 900; line-height: 1; color: rgba(255,255,255,.15); margin-bottom: -22px; }
  /* 제목은 \n 을 줄바꿈으로 살린다 */
  #dm-t { font-size: 76px; font-weight: 900; line-height: 1.18; color: #fff; white-space: pre-line; }
  #dm-t.sm { font-size: 54px; }
  #dm-s { font-size: 26px; color: #cfe4f7; margin-top: 28px; line-height: 1.6; }
  #dm-m { font-size: 19px; color: #8fb8dc; margin-top: 52px; letter-spacing: .05em; }
  .dm-an { opacity: 0; transform: translateY(18px); }
  .dm-an.go { animation: dmRise .85s cubic-bezier(.2,.7,.3,1) forwards; }
  @keyframes dmRise { to { opacity: 1; transform: translateY(0); } }

  #dm-dots { position: absolute; left: 0; right: 0; bottom: 46px; z-index: 3;
    display: flex; gap: 10px; justify-content: center; opacity: 0; transition: opacity .5s; }
  #dm-dots.on { opacity: 1; }
  #dm-dots i { width: 38px; height: 4px; border-radius: 99px; background: rgba(255,255,255,.24); transition: all .4s; }
  #dm-dots i.done { background: rgba(255,255,255,.55); }
  #dm-dots i.cur { background: #fff; width: 64px; }

  #dm-capwrap { position: absolute; left: 0; right: 0; bottom: 0; height: 190px;
    display: flex; align-items: flex-end; justify-content: center; padding-bottom: 44px;
    background: linear-gradient(to top,rgba(2,12,24,.92) 0%,rgba(2,12,24,.74) 46%,rgba(2,12,24,0) 100%);
    opacity: 0; transition: opacity .45s ease; }
  #dm-capwrap.on { opacity: 1; }
  #dm-cap { max-width: 1240px; text-align: center; color: #fff; font-size: 29px; font-weight: 500;
    line-height: 1.5; text-shadow: 0 2px 14px rgba(0,0,0,.7); transition: opacity .3s ease; }
  #dm-cap b { color: #7cd0ff; font-weight: 700; }

  /* 앱 상단바를 가리지 않도록 자막 바로 위(로어서드 위치)에 둔다 */
  #dm-chip { position: absolute; bottom: 208px; left: 46px; display: flex; align-items: center; gap: 12px;
    background: rgba(0,45,90,.92); color: #fff; padding: 11px 22px 11px 14px; border-radius: 999px;
    font-size: 20px; font-weight: 700; box-shadow: 0 10px 30px rgba(0,0,0,.32);
    opacity: 0; transform: translateY(12px); transition: opacity .5s ease, transform .5s ease; }
  #dm-chip.on { opacity: 1; transform: translateY(0); }
  #dm-chip u { width: 30px; height: 30px; border-radius: 9px; background: #0098d9;
    display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 900; text-decoration: none; }

  #dm-cur { position: absolute; width: 30px; height: 30px; left: -120px; top: -120px;
    transition: left .6s cubic-bezier(.3,.7,.3,1), top .6s cubic-bezier(.3,.7,.3,1); }
  #dm-ring { position: absolute; width: 56px; height: 56px; border-radius: 50%; border: 3px solid #0098d9;
    left: -200px; top: -200px; opacity: 0; }
  #dm-ring.pop { animation: dmPop .55s ease-out; }
  @keyframes dmPop { 0% { opacity:.9; transform: scale(.35);} 100% { opacity:0; transform: scale(1.25);} }

  #dm-fade { position: absolute; inset: 0; background: #000; opacity: 0; transition: opacity .55s ease; }
  #dm-fade.on { opacity: 1; }

  /* 페이지 이동 직후 이전 상태를 '복원'할 때는 전환 없이 즉시 그린다.
     그러지 않으면 새 문서에서 커버가 0%부터 다시 페이드인되어,
     그 사이 이동 중인 페이지가 잠깐 노출된다. */
  #dm-root.dm-noanim, #dm-root.dm-noanim * { transition: none !important; animation: none !important; }
  `;

  function build() {
    if (document.getElementById("dm-root")) return;
    const st = document.createElement("style");
    st.textContent = CSS;
    // document_start 시점에는 head가 아직 없을 수 있다
    (document.head || document.documentElement).appendChild(st);

    const root = document.createElement("div");
    root.id = "dm-root";
    root.innerHTML = `
      <div id="dm-cover"><div class="in">
        <div id="dm-k" class="dm-an"></div>
        <div id="dm-n" class="dm-an"></div>
        <div id="dm-t" class="dm-an"></div>
        <div id="dm-s" class="dm-an"></div>
        <div id="dm-m" class="dm-an"></div>
      </div><div id="dm-dots">${"<i></i>".repeat(8)}</div></div>
      <div id="dm-chip"><u id="dm-chipno"></u><span id="dm-chiptxt"></span></div>
      <div id="dm-capwrap"><div id="dm-cap"></div></div>
      <div id="dm-ring"></div>
      <div id="dm-cur"><svg viewBox="0 0 24 24" width="30" height="30">
        <path d="M4 2 L4 20 L9 15.4 L12.2 22 L15.4 20.4 L12.2 14 L19 14 Z"
          fill="#fff" stroke="#0b2740" stroke-width="1.4" stroke-linejoin="round"/></svg></div>
      <div id="dm-fade"></div>`;
    document.documentElement.appendChild(root);
    restore();
  }

  const $ = (id) => document.getElementById(id);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function paintCover(o, animate) {
    $("dm-k").textContent = o.kicker || "";
    $("dm-n").textContent = o.no || "";
    $("dm-t").textContent = o.title || "";
    $("dm-t").className = "dm-an" + (o.titleSm ? " sm" : "");
    $("dm-s").innerHTML = o.sub || "";
    $("dm-m").textContent = o.meta || "";
    $("dm-n").style.display = o.no ? "block" : "none";
    $("dm-s").style.display = o.sub ? "block" : "none";
    $("dm-m").style.display = o.meta ? "block" : "none";

    const dots = $("dm-dots");
    if (o.dots) {
      dots.classList.add("on");
      [...dots.children].forEach((el, i) => {
        el.className = i < o.dots - 1 ? "done" : i === o.dots - 1 ? "cur" : "";
      });
    } else dots.classList.remove("on");

    const ids = ["dm-k", "dm-n", "dm-t", "dm-s", "dm-m"];
    ids.forEach((id) => {
      const e = $(id);
      e.classList.remove("go");
      e.style.opacity = ""; e.style.transform = "";
      void e.offsetWidth;
    });
    if (animate) {
      ids.forEach((id, i) => setTimeout(() => $(id).classList.add("go"), i * 110));
    } else {
      // 복원 경로: 애니메이션 없이 최종 상태를 직접 지정한다.
      ids.forEach((id) => { const e = $(id); e.style.opacity = "1"; e.style.transform = "none"; });
    }
    $("dm-cover").classList.add("on");
  }

  function restore() {
    const root = $("dm-root");
    root.classList.add("dm-noanim");

    const cv = SS.get("cover", null);
    if (cv) paintCover(cv, false);
    const cp = SS.get("chip", null);
    if (cp) { $("dm-chipno").textContent = cp.no; $("dm-chiptxt").textContent = cp.text; $("dm-chip").classList.add("on"); }
    const cap = SS.get("cap", null);
    if (cap) { $("dm-cap").innerHTML = cap; $("dm-capwrap").classList.add("on"); }
    if (SS.get("fade", false)) $("dm-fade").classList.add("on");

    // 두 프레임 뒤 전환을 다시 켠다 (복원분이 화면에 반영된 다음)
    requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove("dm-noanim")));
  }

  window.__demo = {
    async cover(o) {
      build();
      // 간지는 항상 깨끗한 화면에서 시작한다. 칩·자막은 커버보다 뒤에 있어
      // 그냥 두면 간지 위에 겹쳐 보인다.
      SS.del("chip"); $("dm-chip").classList.remove("on");
      SS.del("cap"); $("dm-capwrap").classList.remove("on");
      SS.set("cover", o); paintCover(o, true); await sleep(150);
    },
    async coverOut() { SS.del("cover"); $("dm-cover").classList.remove("on"); await sleep(850); },

    chip(no, text) { build(); SS.set("chip", { no, text }); $("dm-chipno").textContent = no;
      $("dm-chiptxt").textContent = text; $("dm-chip").classList.add("on"); },
    chipOff() { SS.del("chip"); $("dm-chip").classList.remove("on"); },

    async say(html) {
      build(); SS.set("cap", html);
      const w = $("dm-capwrap"), c = $("dm-cap");
      if (!w.classList.contains("on")) { c.innerHTML = html; w.classList.add("on"); await sleep(420); return; }
      c.style.opacity = 0; await sleep(300);
      c.innerHTML = html; c.style.opacity = 1; await sleep(300);
    },
    async sayOff() { SS.del("cap"); $("dm-capwrap").classList.remove("on"); await sleep(450); },

    async move(x, y) { build(); $("dm-cur").style.left = x + "px"; $("dm-cur").style.top = y + "px"; await sleep(640); },
    async ping(x, y) {
      const r = $("dm-ring");
      r.style.left = (x - 13) + "px"; r.style.top = (y - 13) + "px";
      r.classList.remove("pop"); void r.offsetWidth; r.classList.add("pop");
      await sleep(400);
    },
    curOff() { $("dm-cur").style.left = "-120px"; $("dm-cur").style.top = "-120px"; },

    async fadeOut() { build(); SS.set("fade", true); $("dm-fade").classList.add("on"); await sleep(620); },
    async fadeIn() { SS.set("fade", false); $("dm-fade").classList.remove("on"); await sleep(620); },
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
