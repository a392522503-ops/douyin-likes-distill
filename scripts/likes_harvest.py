# -*- coding: utf-8 -*-
"""likes_harvest.py — 抖音「喜欢」列表批量抓取（接管已登录 CDP Chrome）
用法：
  python likes_harvest.py collect   # 阶段1：滚动收集全部视频ID
  python likes_harvest.py detail    # 阶段2：逐条抓详情（断点续传）
"""
import json, time, os, sys, random, urllib.request
import websocket

sys.stdout.reconfigure(encoding="utf-8")
CDP = "http://127.0.0.1:9222"
OUT = r"C:\Users\Administrator\YuedaContent\tools\_out"
LIST_F = os.path.join(OUT, "likes_list.json")
FAIL_F = os.path.join(OUT, "likes_failed.json")
os.makedirs(OUT, exist_ok=True)
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

LIST_JS = """
(function(){
  const ids = new Set();
  document.querySelectorAll('a[href*="/video/"]').forEach(a=>{
    const m = a.href.match(/video\\/(\\d{15,20})/);
    if(m) ids.add(m[1]);
  });
  return JSON.stringify({count: ids.size, ids: [...ids], url: location.href,
    needLogin: !!document.querySelector('[data-e2e="login-button"]') || location.href.includes('passport') || document.body.innerText.includes('扫码登录')});
})()
"""

GRAB = """
(function(){
  const pick = (s)=>{const e=document.querySelector(s);return e?e.innerText.trim():"";};
  return JSON.stringify({
    url: location.href,
    pageTitle: document.title,
    desc: pick('[data-e2e="video-desc"]') || pick('.video-info-detail .title') || "",
    author: pick('[data-e2e="video-author-name"]') || pick('.author-name') || "",
    stats: pick('[data-e2e="video-player-digg"]') || "",
    body: document.body.innerText.slice(0, 2500)
  });
})()
"""

def cdp_pages():
    return json.loads(op.open(CDP + "/json", timeout=5).read().decode())

def get_ws():
    pages = [p for p in cdp_pages() if p.get("type") == "page" and "douyin" in (p.get("url") or "")]
    if not pages:
        pages = [p for p in cdp_pages() if p.get("type") == "page"]
    assert pages, "无可用 douyin tab"
    return pages[0]["webSocketDebuggerUrl"], pages[0]

def cdp_eval(ws, expr, timeout=25):
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                        "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}}))
    t0 = time.time()
    while time.time() - t0 < timeout:
        msg = json.loads(ws.recv())
        if msg.get("id") == 1:
            r = msg.get("result", {})
            if "exceptionDetails" in r:
                return {"error": str(r["exceptionDetails"])[:300]}
            return r.get("result", {}).get("value")
    return {"error": "timeout"}

def check_block(ws):
    st = cdp_eval(ws, "JSON.stringify({t:document.title, c:document.body.innerText.includes('验证'), url:location.href})")
    st = json.loads(st) if isinstance(st, str) else (st or {})
    if "验证" in st.get("t", "") or st.get("c"):
        open(os.path.join(OUT, "likes_BLOCKED.flag"), "w").write(st.get("url", ""))
        print("!! 风控验证码拦截，已写 flag，请人工过验证后重跑", flush=True)
        return True
    return False

def _ws_connect(url, timeout=60):
    """CDP WebSocket 连接：先试 suppress_origin（免 --remote-allow-origins），失败再带 origin"""
    try:
        return websocket.create_connection(url, timeout=timeout, suppress_origin=True)
    except Exception:
        return websocket.create_connection(url, timeout=timeout, origin="http://127.0.0.1:9222")

def phase_collect():
    ws_url, page = get_ws()
    print("接管 tab:", page.get("url", "")[:60], flush=True)
    ws = _ws_connect(ws_url)
    cdp_eval(ws, "location.href='https://www.douyin.com/user/self?showTab=like'; 'ok'", timeout=15)
    time.sleep(6)
    all_ids, stale = set(), 0
    for i in range(60):  # 最多60轮滚动
        r = cdp_eval(ws, LIST_JS)
        r = json.loads(r) if isinstance(r, str) else (r or {})
        if r.get("needLogin"):
            print("!! 未登录或登录态失效，请重新扫码", flush=True); ws.close(); sys.exit(2)
        if check_block(ws): ws.close(); sys.exit(3)
        new = set(r.get("ids", [])) - all_ids
        all_ids |= new
        print("scroll %d: +%d = %d 条 (url=%s)" % (i, len(new), len(all_ids), r.get("url", "")[:50]), flush=True)
        if new:
            stale = 0
            cdp_eval(ws, "window.scrollTo(0, document.body.scrollHeight); 'ok'")
            time.sleep(random.uniform(2.5, 4.0))
        else:
            stale += 1
            cdp_eval(ws, "window.scrollTo(0, document.body.scrollHeight); 'ok'")
            time.sleep(2)
            if stale >= 4:
                print("连续 4 轮无新增，判定到底", flush=True)
                break
    ws.close()
    ids = sorted(all_ids)
    json.dump({"total": len(ids), "ids": ids, "harvest_time": time.strftime("%Y-%m-%d %H:%M:%S")},
              open(LIST_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("COLLECT DONE: %d 条 -> likes_list.json" % len(ids), flush=True)

def phase_detail():
    data = json.load(open(LIST_F, encoding="utf-8"))
    ids = data["ids"]
    failed = []
    done = 0
    ws_url, page = get_ws()
    ws = _ws_connect(ws_url)
    for n, vid in enumerate(ids, 1):
        out = os.path.join(OUT, "likes_detail_%s.json" % vid)
        if os.path.exists(out):
            done += 1
            continue
        try:
            cdp_eval(ws, "location.href='https://www.douyin.com/?modal_id=%s'; 'ok'" % vid, timeout=15)
            got = None
            for attempt in range(2):
                if attempt > 0:
                    cdp_eval(ws, "location.href='https://www.douyin.com/?modal_id=%s'; 'ok'" % vid, timeout=15)
                    time.sleep(6)
                for i in range(8):
                    time.sleep(4)
                    st = cdp_eval(ws, "JSON.stringify({t:document.title, d:!!document.querySelector('[data-e2e=\"video-desc\"]'), v:document.body.innerText.indexOf('%s')>=0})" % vid[:10])
                    st = json.loads(st) if isinstance(st, str) else (st or {})
                    if check_block(ws): ws.close(); sys.exit(3)
                    if st.get("d") or st.get("v"):
                        time.sleep(3)
                        got = True
                        break
                if got:
                    break
            raw = cdp_eval(ws, GRAB, timeout=25)
            rec = json.loads(raw) if isinstance(raw, str) else (raw or {})
            rec["modal_id"] = vid
            json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            done += 1
            print("[%d/%d] %s desc=%d" % (n, len(ids), vid, len(rec.get("desc", ""))), flush=True)
        except Exception as e:
            failed.append({"id": vid, "err": str(e)[:200]})
            print("[%d/%d] %s FAIL %s" % (n, len(ids), vid, str(e)[:80]), flush=True)
        time.sleep(random.uniform(4.0, 6.0))
    ws.close()
    if failed:
        json.dump(failed, open(FAIL_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DETAIL DONE: %d/%d 成功, %d 失败" % (done, len(ids), len(failed)), flush=True)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "collect"
    if mode == "collect":
        phase_collect()
    elif mode == "detail":
        phase_detail()
    else:
        print("用法: likes_harvest.py collect|detail")
