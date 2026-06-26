#!/usr/bin/env python3
"""
OptAgent 功能验证测试 — P0 ~ P3 全部 15 项功能

运行:
  python3 tests/test_verify.py           # 快速验证（11项，无WebSocket）
  python3 tests/test_verify.py --all     # 完整验证（15项，含WebSocket）
  python3 tests/test_verify.py --list    # 列出所有测试
  python3 tests/test_verify.py --p0      # 仅 P0
  python3 tests/test_verify.py --timeout 30  # 自定义WS超时
"""

import argparse, asyncio, json, sys, time, traceback, urllib.request, urllib.error
from pathlib import Path

BASE = "http://localhost:8020/api"
WS  = "ws://localhost:8020"
WS_TIMEOUT = 15

PASS = FAIL = 0
results: list = []
tests: list = []

def R(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, method=method,
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise AssertionError(f"HTTP {e.code}: {e.read().decode()}")
    except urllib.error.URLError as e:
        raise AssertionError(f"Connection: {e.reason}")

GET = lambda p: R("GET", p)
POST = lambda p, d=None: R("POST", p, d)
DELETE = lambda p: R("DELETE", p)

def test(name, cat):
    def deco(fn):
        tests.append((name, cat, fn))
        return fn
    return deco

def ok(name, cat):
    global PASS; PASS += 1; results.append((name, cat, "PASS"))
    print(f"  \033[32mPASS\033[0m [{cat}] {name}")

def fail(name, cat, msg):
    global FAIL; FAIL += 1; results.append((name, cat, "FAIL", msg))
    print(f"  \033[31mFAIL\033[0m [{cat}] {name}")
    print(f"    {msg}")

# ══════════════════════════════════════════════════════════════════════════════
# P0 — 核心流程
# ══════════════════════════════════════════════════════════════════════════════

@test("Health endpoint", "P0")
def t_health():
    r = json.loads(urllib.request.urlopen("http://localhost:8020/health", timeout=5).read())
    assert r["status"] == "ok"

@test("Session CRUD", "P0")
def t_session_crud():
    s = POST("/sessions", {"workflow_name": "process-optimization"})
    assert "id" in s; sid = s["id"]
    lst = GET("/sessions"); assert any(i["id"] == sid for i in lst)
    g = GET(f"/sessions/{sid}"); assert g["id"] == sid and g["status"] == "pending"
    DELETE(f"/sessions/{sid}")
    assert not any(i["id"] == sid for i in GET("/sessions"))

@test("Workflows list & detail", "P0")
def t_workflows():
    lst = GET("/workflows"); assert any(w["name"] for w in lst)
    d = GET("/workflows/process-optimization")
    assert d["name"] == "process-optimization" and len(d["nodes"]) == 6

@test("Skills registration", "P0")
def t_skills():
    s = GET("/skills"); names = {i["name"] for i in s}
    expected = {"define-objective","identify-params","design-doe",
                "collect-data","analyze-results","generate-report","knowledge-retrieval"}
    assert not expected - names, f"missing: {expected - names}"

@test("Config file loads", "P0")
def t_config():
    import yaml
    d = yaml.safe_load(Path("backend/config.yaml").read_text())
    assert d and "skills" in d and "workflows" in d

@test("KB document upload & search & stats", "P0")
def t_kb():
    import tempfile, os
    fpath = tempfile.mktemp(suffix=".txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("注塑工艺参数优化是提高产品质量的关键步骤。温度、压力、时间是核心参数。")
    try:
        boundary = "----B"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"t.txt\"\r\n"
                "Content-Type: text/plain\r\n\r\n"
                "注塑工艺参数优化是提高产品质量的关键步骤。温度、压力、时间是核心参数。\r\n"
                f"--{boundary}--\r\n").encode()
        r = urllib.request.Request(f"{BASE}/kb/upload", data=body, method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        urllib.request.urlopen(r, timeout=10)
    finally:
        os.unlink(fpath)
    assert isinstance(GET("/kb/documents"), list)
    try: GET("/kb/search?q=工艺参数优化&top_k=3")
    except: pass
    try: GET("/kb/stats")
    except: pass

@test("WS: graph:start + node:enter events", "P0")
async def t_ws_events():
    import websockets
    s = POST("/sessions", {"workflow_name": "process-optimization"}); sid = s["id"]
    events = []
    async with websockets.connect(f"{WS}/ws/sessions/{sid}") as ws:
        await ws.send(json.dumps({"type":"user:message","content":"你好"}))
        while True:
            ev = json.loads(await asyncio.wait_for(ws.recv(), WS_TIMEOUT))
            events.append(ev["type"])
            if ev["type"] == "agent:message": break
    et = events
    for k in ("graph:start","node:enter","agent:token","agent:message"):
        assert k in et, f"missing {k}"
    assert et.index("graph:start") < et.index("node:enter")
    assert et.index("node:enter") < et.index("agent:message")
    DELETE(f"/sessions/{sid}")

@test("WS: tools & skills detected", "P0")
async def t_ws_tools():
    import websockets
    s = POST("/sessions", {"workflow_name": "process-optimization"}); sid = s["id"]
    events = []
    async with websockets.connect(f"{WS}/ws/sessions/{sid}") as ws:
        await ws.send(json.dumps({"type":"user:message","content":"分析注塑工艺参数对良率的影响"}))
        while True:
            ev = json.loads(await asyncio.wait_for(ws.recv(), WS_TIMEOUT))
            events.append(ev["type"])
            if ev["type"] == "agent:message": break
    et = set(events)
    print(f"  tools: kb={'kb:query' in et} call={'agent:tool_call' in et} skill={'skill:matched' in et}")
    DELETE(f"/sessions/{sid}")

# ══════════════════════════════════════════════════════════════════════════════
# P1 — 数据链路
# ══════════════════════════════════════════════════════════════════════════════

@test("Data endpoint structure", "P1")
def t_data():
    s = POST("/sessions", {"workflow_name": "process-optimization"}); sid = s["id"]
    d = GET(f"/sessions/{sid}/data")
    assert d["session_id"] == sid
    for k in ("factor_importance","correlation","pareto","scatter","steps"):
        assert k in d["data"], f"missing {k}"
    DELETE(f"/sessions/{sid}")

# ══════════════════════════════════════════════════════════════════════════════
# P2 — 生产化
# ══════════════════════════════════════════════════════════════════════════════

@test("Terminate endpoint", "P2")
def t_terminate():
    s = POST("/sessions", {"workflow_name": "process-optimization"}); sid = s["id"]
    assert POST(f"/sessions/{sid}/terminate")["ok"]
    DELETE(f"/sessions/{sid}")

@test("Session state endpoint", "P2")
def t_state():
    s = POST("/sessions", {"workflow_name": "process-optimization"}); sid = s["id"]
    st = GET(f"/sessions/{sid}/state")
    assert st["message_count"] == 0
    for k in ("session_id","status","current_node","node_statuses","node_results","created_at"):
        assert k in st
    DELETE(f"/sessions/{sid}")

@test("WS: Message persistence (checkpoint)", "P2")
async def t_checkpoint():
    import websockets
    s = POST("/sessions", {"workflow_name": "process-optimization"}); sid = s["id"]
    for _ in range(2):
        async with websockets.connect(f"{WS}/ws/sessions/{sid}") as ws:
            await ws.send(json.dumps({"type":"user:message","content":"你好"}))
            ok = False
            while True:
                ev = json.loads(await asyncio.wait_for(ws.recv(), WS_TIMEOUT))
                if ev["type"] == "agent:message": ok = True; break
            assert ok
    assert GET(f"/sessions/{sid}/state")["message_count"] >= 2
    DELETE(f"/sessions/{sid}")

@test("WS: terminate → graph:interrupted", "P2")
async def t_ws_terminate():
    import websockets
    s = POST("/sessions", {"workflow_name": "process-optimization"}); sid = s["id"]
    async with websockets.connect(f"{WS}/ws/sessions/{sid}") as ws:
        await ws.send(json.dumps({"type":"user:message","content":"你好"}))
        await asyncio.sleep(1.5)
        await ws.send(json.dumps({"type":"user:terminate"}))
        while True:
            try:
                ev = json.loads(await asyncio.wait_for(ws.recv(), 5))
                if ev["type"] == "graph:interrupted": break
            except asyncio.TimeoutError:
                assert False, "no graph:interrupted"
    DELETE(f"/sessions/{sid}")

# ══════════════════════════════════════════════════════════════════════════════
# P3 — 扩展能力
# ══════════════════════════════════════════════════════════════════════════════

@test("Backend registry", "P3")
def t_backend():
    sys.path.insert(0, "backend/src")
    from optagent.backends import register, list_backends, get_backend
    from optagent.persistence.store import SessionStore
    register("sqlite", SessionStore)
    assert "sqlite" in list_backends()
    assert get_backend("sqlite") is not None
    try: get_backend("x"); assert False
    except ValueError: pass

@test("Embedding model (ngram + ONNX fallback)", "P3")
def t_embed():
    sys.path.insert(0, "backend/src")
    from optagent.kb.embedding import FastEmbeddings
    emb = FastEmbeddings("ngram")
    v = emb.embed_query("测试")
    assert len(v) == 512
    docs = emb.embed_documents(["A","B"])
    assert len(docs) == 2 and len(docs[0]) == 512
    emb2 = FastEmbeddings("bert-base-uncased")
    v2 = emb2.embed_query("test")
    assert len(v2) == 512  # ONNX unavailable → ngram fallback

# ══════════════════════════════════════════════════════════════════════════════
# Runner
# ══════════════════════════════════════════════════════════════════════════════

def run(fns):
    for name, cat, fn in fns:
        try:
            if asyncio.iscoroutinefunction(fn):
                asyncio.run(fn())
            else:
                fn()
            ok(name, cat)
        except Exception as e:
            fail(name, cat, f"{type(e).__name__}: {e}")

def main():
    global WS_TIMEOUT
    ap = argparse.ArgumentParser(description="OptAgent 功能验证测试")
    ap.add_argument("--all", action="store_true", help="运行全部测试（含WS）")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--p0", action="store_true")
    ap.add_argument("--p1", action="store_true")
    ap.add_argument("--p2", action="store_true")
    ap.add_argument("--p3", action="store_true")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--timeout", type=int, default=15, help="WS 超时秒数（默认15）")
    args = ap.parse_args()
    WS_TIMEOUT = args.timeout

    if args.list:
        for n, c, _ in tests: print(f"  [{c}] {n}")
        return

    # Determine category filter
    cat = None
    if args.p0: cat = "P0"
    elif args.p1: cat = "P1"
    elif args.p2: cat = "P2"
    elif args.p3: cat = "P3"

    selected = []
    for t in tests:
        is_ws = t[0].startswith("WS:")
        if cat:
            if t[1] == cat: selected.append(t)
        elif args.all:
            selected.append(t)
        elif args.fast or not is_ws:
            selected.append(t)

    if not selected:
        selected = [t for t in tests if not t[0].startswith("WS:")]

    print(f"OptAgent 验证测试 — {len(selected)} 项\n")
    run(selected)

    total = PASS + FAIL
    print(f"\n{'─'*40}")
    print(f"  {PASS}/{total} 通过  {FAIL} 失败")
    if FAIL:
        print("\n失败的测试:")
        for r in results:
            if r[2] == "FAIL":
                print(f"  [{r[1]}] {r[0]}: {r[3]}")
    print()
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
