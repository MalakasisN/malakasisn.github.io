"""NM_editor: edit content.json through a browser UI, preview the site, publish to GitHub Pages.

Run:  python3 admin/app.py   (or double-click NM_editor.app; the UI opens at http://127.0.0.1:8787)
"""
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

ROOT = build.ROOT
ADMIN_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FILE = os.path.join(ADMIN_DIR, "ui.html")
PENDING_FILE = os.path.join(ADMIN_DIR, ".pending-uploads.json")
PORT = int(os.environ.get("PORT", "8787"))
MAX_IMAGE_PX = 1600
JPEG_QUALITY = "normal"
PHOTO_PX = 400
SITE_FILES = ["content.json", "style.css", "script.js", "favicon.svg", "og-image.jpg", ".nojekyll", "README.md",
              "admin/app.py", "admin/build.py", "admin/ui.html", "admin/.gitignore",
              "NM_editor.app/Contents/Info.plist", "NM_editor.app/Contents/MacOS/NM_editor", "NM_editor.app/Contents/Resources/NM_editor.icns"] + list(build.RENDERERS)


# ── helpers ──────────────────────────────────────────────────────

def run_git(*args, check=True, timeout=120):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{p.stderr.strip() or p.stdout.strip()}")
    return p.stdout


def safe_rel_path(rel):
    rel = unquote(rel).replace("\\", "/").lstrip("/")
    full = os.path.normpath(os.path.join(ROOT, rel))
    if not full.startswith(ROOT + os.sep) and full != ROOT:
        raise ValueError("path outside site folder")
    if "/.git/" in full + "/" or full.startswith(os.path.join(ROOT, ".git")):
        raise ValueError("path not allowed")
    return full, os.path.relpath(full, ROOT).replace(os.sep, "/")


def sanitize_name(name):
    name = os.path.basename(name)
    name = re.sub(r"[^\w\-. ]+", "", name).strip() or "file"
    return name


def unique_path(full):
    if not os.path.exists(full):
        return full
    stem, ext = os.path.splitext(full)
    n = 2
    while os.path.exists(f"{stem}_{n}{ext}"):
        n += 1
    return f"{stem}_{n}{ext}"


def load_pending():
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE) as f:
            return json.load(f)
    return []


def save_pending(items):
    with open(PENDING_FILE, "w") as f:
        json.dump(items, f, indent=2)


def remember_upload(rel):
    items = load_pending()
    if rel not in items:
        items.append(rel)
    save_pending(items)


def referenced_assets(content):
    """All relative file paths referenced from content.json (images, pdf, ...)."""
    found = set()

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and re.search(r"\.(jpe?g|png|webp|gif|svg|pdf)$", v, re.I) and "://" not in v:
            if os.path.exists(os.path.join(ROOT, v)):
                found.add(v)

    walk(content)
    return sorted(found)


def tracked_files():
    return set(run_git("ls-files").split("\n")) - {""}


def git_status():
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD").strip()
    last = run_git("log", "-1", "--format=%h %s (%cr)").strip()
    porcelain = run_git("status", "--porcelain", "--untracked-files=all")
    changed, untracked = [], []
    for line in porcelain.split("\n"):
        if not line:
            continue
        code, path = line[:2], line[3:].strip().strip('"')
        if code == "??":
            untracked.append(path)
        else:
            changed.append(path)
    content = build.load_content()
    publishable = set(SITE_FILES) | set(referenced_assets(content)) | set(load_pending())
    publishable = {p for p in publishable if os.path.exists(os.path.join(ROOT, p))}
    to_publish = sorted(
        [p for p in changed if not p.endswith(".DS_Store")]
        + [p for p in untracked if p in publishable and not p.endswith(".DS_Store")]
    )
    ahead = ""
    try:
        ahead = run_git("rev-list", "--count", "@{u}..HEAD").strip()
    except RuntimeError:
        pass
    return {"branch": branch, "last_commit": last, "to_publish": to_publish, "unpushed": ahead,
            "remote": run_git("remote", "get-url", "origin", check=False).strip()}


def sips(*args):
    p = subprocess.run(["sips", *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout


def image_size(path):
    out = sips("-g", "pixelWidth", "-g", "pixelHeight", path)
    w = int(re.search(r"pixelWidth: (\d+)", out).group(1))
    h = int(re.search(r"pixelHeight: (\d+)", out).group(1))
    return w, h


def optimize_image(src, dest, max_px=MAX_IMAGE_PX):
    """Resize to fit max_px and recompress. HEIC/TIFF/BMP become JPEG. Returns final dest path."""
    ext = os.path.splitext(dest)[1].lower()
    if ext in (".heic", ".heif", ".tif", ".tiff", ".bmp"):
        dest = os.path.splitext(dest)[0] + ".jpg"
        ext = ".jpg"
    args = ["-Z", str(max_px)]
    if ext in (".jpg", ".jpeg"):
        args += ["-s", "format", "jpeg", "-s", "formatOptions", JPEG_QUALITY]
    elif ext == ".png":
        args += ["-s", "format", "png"]
    sips(*args, src, "--out", dest)
    return dest


def make_profile_photo(src, jpg_rel, webp_rel):
    jpg = os.path.join(ROOT, jpg_rel)
    w, h = image_size(src)
    side = min(w, h)
    sips("-c", str(side), str(side), "-s", "format", "jpeg", src, "--out", jpg)
    sips("-Z", str(PHOTO_PX), "-s", "format", "jpeg", "-s", "formatOptions", "90", jpg, "--out", jpg)
    cwebp = shutil.which("cwebp")
    webp = os.path.join(ROOT, webp_rel) if webp_rel else None
    if webp and cwebp:
        subprocess.run([cwebp, "-quiet", "-q", "85", jpg, "-o", webp], check=True, capture_output=True)
    elif webp and os.path.exists(webp):
        os.remove(webp)
    return os.path.exists(webp) if webp else False


# ── HTTP handler ─────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if "/preview/" not in (fmt % args):
            super().log_message(fmt, *args)

    def send_json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, full, content_type=None):
        if not os.path.isfile(full):
            self.send_error(404)
            return
        ctype = content_type or mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        try:
            if path in ("/", "/index.html"):
                self.send_file(UI_FILE, "text/html")
            elif path == "/api/content":
                self.send_file(build.CONTENT_FILE, "application/json")
            elif path == "/api/status":
                self.send_json(git_status())
            elif path == "/api/files":
                folder = parse_qs(url.query).get("folder", [""])[0]
                full, _ = safe_rel_path(folder)
                names = sorted(n for n in os.listdir(full) if not n.startswith(".")) if os.path.isdir(full) else []
                self.send_json({"files": names})
            elif path.startswith("/preview/"):
                rel = path[len("/preview/"):] or "index.html"
                full, _ = safe_rel_path(rel)
                if os.path.isdir(full):
                    full = os.path.join(full, "index.html")
                self.send_file(full)
            else:
                self.send_error(404)
        except (ValueError, RuntimeError) as e:
            self.send_json({"error": str(e)}, 400)

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if path == "/api/content":
                content = json.loads(self.read_body().decode("utf-8"))
                with open(build.CONTENT_FILE, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                written = build.build(content)
                self.send_json({"ok": True, "written": written, "status": git_status()})

            elif path == "/api/upload":
                body = self.read_body()
                folder_full, folder_rel = safe_rel_path(q.get("folder", "uploads"))
                os.makedirs(folder_full, exist_ok=True)
                name = sanitize_name(q.get("name", "file"))
                dest = unique_path(os.path.join(folder_full, name))
                tmp = dest + ".upload"
                with open(tmp, "wb") as f:
                    f.write(body)
                is_image = re.search(r"\.(jpe?g|png|heic|heif|tif|tiff|bmp|webp|gif)$", name, re.I)
                if is_image and q.get("optimize", "1") == "1" and not name.lower().endswith((".webp", ".gif", ".svg")):
                    try:
                        dest = optimize_image(tmp, dest)
                        os.remove(tmp)
                    except RuntimeError:
                        os.replace(tmp, dest)
                else:
                    os.replace(tmp, dest)
                rel = os.path.relpath(dest, ROOT).replace(os.sep, "/")
                remember_upload(rel)
                self.send_json({"ok": True, "path": rel, "size": os.path.getsize(dest)})

            elif path == "/api/photo":
                body = self.read_body()
                content = build.load_content()
                site = content["site"]
                tmp = os.path.join(ADMIN_DIR, ".photo-upload" + os.path.splitext(sanitize_name(q.get("name", "p.jpg")))[1])
                with open(tmp, "wb") as f:
                    f.write(body)
                try:
                    has_webp = make_profile_photo(tmp, site["photo"], site.get("photo_webp"))
                finally:
                    os.remove(tmp)
                self.send_json({"ok": True, "path": site["photo"], "webp": has_webp})

            elif path == "/api/file":
                body = self.read_body()
                full, rel = safe_rel_path(q["path"])
                with open(full, "wb") as f:
                    f.write(body)
                remember_upload(rel)
                self.send_json({"ok": True, "path": rel, "size": len(body)})

            elif path == "/api/publish":
                req = json.loads(self.read_body().decode("utf-8") or "{}")
                message = (req.get("message") or "Update site content").strip()
                content = build.load_content()
                build.build(content)
                status = git_status()
                if not status["to_publish"] and not status["unpushed"]:
                    self.send_json({"ok": False, "error": "Nothing to publish."})
                    return
                result = {"ok": True, "committed": False}
                if status["to_publish"]:
                    run_git("add", "--", *status["to_publish"])
                    run_git("commit", "-m", message)
                    result["committed"] = True
                    result["commit"] = run_git("log", "-1", "--format=%h %s").strip()
                push = subprocess.run(["git", "push", "origin", status["branch"]], cwd=ROOT, capture_output=True, text=True, timeout=180)
                result["pushed"] = push.returncode == 0
                result["push_output"] = (push.stderr + push.stdout).strip()
                save_pending([])
                result["status"] = git_status()
                result["site_url"] = content["site"]["base_url"]
                self.send_json(result)

            elif path == "/api/quit":
                self.send_json({"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()

            elif path == "/api/discard":
                tracked = tracked_files()
                status = git_status()
                revert = [p for p in status["to_publish"] if p in tracked]
                if revert:
                    run_git("checkout", "--", *revert)
                removed = []
                for rel in load_pending():
                    full = os.path.join(ROOT, rel)
                    if rel not in tracked and os.path.exists(full):
                        os.remove(full)
                        removed.append(rel)
                save_pending([])
                build.build()
                self.send_json({"ok": True, "reverted": revert, "removed": removed, "status": git_status()})

            else:
                self.send_error(404)
        except (ValueError, RuntimeError, KeyError, json.JSONDecodeError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            self.send_json({"ok": False, "error": str(e)}, 400)


def main():
    os.chdir(ROOT)
    url = f"http://127.0.0.1:{PORT}/"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"NM_editor is already running at {url}")
        if "--no-browser" not in sys.argv:
            webbrowser.open(url)
        return
    print(f"NM_editor running at {url}  (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
