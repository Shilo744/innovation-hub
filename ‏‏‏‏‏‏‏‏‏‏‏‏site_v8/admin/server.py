"""
RISE.HUB local content admin server.

Everything is LOCAL-FIRST:
  * Serves the site itself (so you can preview every page).
  * Serves the admin UI at /admin/.
  * Every edit in the admin is written straight to the data files on disk
    (data/events.json, data/news.json) — no internet needed.
  * Uploaded images are saved to assets/content/... on disk immediately.
  * Only the "publish" button touches git (add + commit + push).

Run:  py admin/server.py   (or double-click start-admin.bat)
Stdlib only — no pip installs.
"""
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8765

DATA_FILES = {
    "events": os.path.join("data", "events.json"),
    "news": os.path.join("data", "news.json"),
}
UPLOAD_ROOT = os.path.join("assets", "content")
ALLOWED_IMG = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}


# ---------- helpers ----------

def read_json(rel):
    path = os.path.join(ROOT, rel)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        return {"_error": str(e)}


def write_json_atomic(rel, obj):
    """Write UTF-8 (no BOM), atomic via temp file + replace."""
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def git(*args):
    """Run a git command in the site root, return (ok, output)."""
    try:
        p = subprocess.run(
            ["git"] + list(args),
            cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode == 0, out.strip()
    except FileNotFoundError:
        return False, "git not found — install git or publish manually"
    except subprocess.TimeoutExpired:
        return False, "git timed out (network?)"


def git_state():
    ok, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if not ok:
        return {"ok": False, "error": branch}
    _, remote = git("remote", "get-url", "origin")
    # scope to the site folder only — the repo root may sit a level above
    _, status = git("status", "--porcelain", "--", ".")
    dirty = [l[3:] for l in status.splitlines() if l.strip()]
    ahead = 0
    ok_a, out_a = git("rev-list", "--count", "@{u}..HEAD")
    if ok_a:
        try:
            ahead = int(out_a.strip() or "0")
        except ValueError:
            ahead = 0
    return {
        "ok": True,
        "branch": branch,
        "remote": remote if remote and "fatal" not in remote else "",
        "dirty": dirty,
        "ahead": ahead,
    }


def slugify_filename(name):
    base, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext not in ALLOWED_IMG:
        ext = ".jpg"
    base = re.sub(r"[^a-z0-9\-]+", "-", base.lower()).strip("-") or "image"
    stamp = format(int(time.time() * 1000) % 0xFFFFFF, "x")
    return f"{base}-{stamp}{ext}"


# ---------- request handler ----------

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):  # quieter console
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("[api] %s\n" % (args[0],))

    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def end_headers(self):
        # never cache data files or the admin while editing locally
        if self.path.startswith(("/data/", "/api/", "/admin")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # -- routing --

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/state":
            data = {k: read_json(v) for k, v in DATA_FILES.items()}
            return self._send_json({"data": data, "git": git_state()})
        if parsed.path == "/admin":
            self.send_response(301)
            self.send_header("Location", "/admin/")
            self.end_headers()
            return
        return super().do_GET()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        m = re.fullmatch(r"/api/data/(\w+)", parsed.path)
        if m and m.group(1) in DATA_FILES:
            try:
                obj = json.loads(self._read_body().decode("utf-8"))
            except Exception as e:
                return self._send_json({"ok": False, "error": "bad json: %s" % e}, 400)
            write_json_atomic(DATA_FILES[m.group(1)], obj)
            return self._send_json({"ok": True, "saved": DATA_FILES[m.group(1)]})
        return self._send_json({"ok": False, "error": "unknown endpoint"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/upload":
            name = (qs.get("name") or ["image.jpg"])[0]
            sub = re.sub(r"[^a-z0-9\-]+", "", (qs.get("dir") or ["events"])[0].lower()) or "events"
            body = self._read_body()
            if not body:
                return self._send_json({"ok": False, "error": "empty upload"}, 400)
            if len(body) > 15 * 1024 * 1024:
                return self._send_json({"ok": False, "error": "image too large (15MB max)"}, 400)
            fname = slugify_filename(name)
            rel_dir = os.path.join(UPLOAD_ROOT, sub)
            os.makedirs(os.path.join(ROOT, rel_dir), exist_ok=True)
            rel_path = os.path.join(rel_dir, fname).replace("\\", "/")
            with open(os.path.join(ROOT, rel_path), "wb") as f:
                f.write(body)
            return self._send_json({"ok": True, "path": rel_path})

        if parsed.path == "/api/publish":
            try:
                payload = json.loads(self._read_body().decode("utf-8") or "{}")
            except Exception:
                payload = {}
            msg = (payload.get("message") or "").strip() or \
                  "Content update via local admin"
            log = []

            # add ONLY the site folder — never sibling folders in the same repo
            ok, out = git("add", "-A", "--", ".")
            log.append("$ git add -A -- .\n" + out)
            if not ok:
                return self._send_json({"ok": False, "log": "\n\n".join(log)})

            ok_diff, _ = git("diff", "--cached", "--quiet")
            state = git_state()
            if ok_diff and state.get("ahead", 0) == 0:
                log.append("Nothing new to publish — the site is already up to date.")
                return self._send_json({"ok": True, "nothing": True, "log": "\n\n".join(log)})

            if not ok_diff:
                ok, out = git("commit", "-m", msg)
                log.append("$ git commit\n" + out)
                if not ok:
                    return self._send_json({"ok": False, "log": "\n\n".join(log)})

            ok, out = git("push")
            if not ok and "no upstream" in out.lower():
                ok, out = git("push", "-u", "origin", git_state().get("branch", "main"))
            log.append("$ git push\n" + out)
            return self._send_json({"ok": ok, "log": "\n\n".join(log)})

        return self._send_json({"ok": False, "error": "unknown endpoint"}, 404)


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    port = PORT
    for _ in range(10):
        try:
            srv = ThreadingServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    else:
        print("No free port found.")
        return

    url = f"http://localhost:{port}/admin/"
    print("=" * 58)
    print("  RISE.HUB — Local Content Admin")
    print(f"  Editing:   {ROOT}")
    print(f"  Admin UI:  {url}")
    print(f"  Site view: http://localhost:{port}/")
    print("  Every change is saved to your computer immediately.")
    print("  'Publish' pushes to GitHub only when YOU choose.")
    print("  Keep this window open while editing. Ctrl+C to stop.")
    print("=" * 58)
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
