#!/usr/bin/env python3
"""
gooningCLI - Multi-site hentai content downloader for Termux
"""

import os
import sys
import json
import time
import re
import hashlib
import subprocess
import shutil
import signal
import platform
import traceback
import logging
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, quote_plus

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("[!] 'requests' not installed. Run: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class _NoColor:
        def __getattr__(self, _): return ""
    Fore = _NoColor()
    Style = _NoColor()

# ============================================================
# CONSTANTS
# ============================================================

VERSION = "2.2.0"
AUTHOR = "or4acle"
APP_NAME = "gooningCLI"
CONFIG_DIR = os.path.expanduser("~/.gooningcli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
BOOKMARKS_FILE = os.path.join(CONFIG_DIR, "bookmarks.json")
BLACKLIST_FILE = os.path.join(CONFIG_DIR, "blacklist.json")
DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/gooningcli_downloads")

SPLASH_TEXTS = [
    "Time to do some research...",
    "For educational purposes only.",
    "Scientific exploration begins now.",
    "Opening the sacred archives...",
    "Preparing the sacred texts...",
    "Activating goon mode...",
    "Warning: May cause productivity loss.",
    "Your screen recorder is ready.",
    "Loading important files...",
    "Research in progress...",
    "Premium content loading...",
    "Just for the plot, I swear.",
    "Tax deductible research.",
    "Peer reviewed content.",
    "Academic purposes only.",
    "This is my art degree homework.",
    "I need this for my thesis.",
    "Cultural exploration mode.",
    "Digital anthropology research.",
    "Quality assurance testing.",
    "Content verification in progress.",
    "Downloading... for science.",
    "My lawyer says this is educational.",
    "The research requires more data.",
    "Expanding the archive.",
    "Critical research material incoming.",
    "Loading culture...",
    "Enhancing digital library.",
    "Preserving digital art.",
    "Cultural preservation initiative.",
    "Academic database access granted.",
    "Research mode: ENGAGED.",
    "Downloading pure knowledge.",
    "The things I do for science.",
    "Professional content curator at work.",
    "Advanced research techniques.",
    "Definitely not what it looks like.",
    "FBI open up... just kidding.",
    "This requires a very specific skill set.",
    "Data acquisition in progress.",
    "Research materials loading...",
    "Expanding the collection.",
    "Archival research in progress.",
    "Critical data incoming...",
    "I call this 'field research'.",
    "This is my job now.",
    "Mandatory quality checks.",
    "Vital information ahead.",
    "Trust me, it's for the culture.",
]

BANNER = r"""
 ██████╗  ██████╗  ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗  ██████╗██╗     ██╗
██╔════╝ ██╔═══██╗██╔═══██╗████╗  ██║██║████╗  ██║██╔════╝ ██╔════╝██║     ██║
██║  ███╗██║   ██║██║   ██║██╔██╗ ██║██║██╔██╗ ██║██║  ███╗██║     ██║     ██║
██║   ██║██║   ██║██║   ██║██║╚██╗██║██║██║╚██╗██║██║   ██║██║     ██║     ██║
╚██████╔╝╚██████╔╝╚██████╔╝██║ ╚████║██║██║ ╚████║╚██████╔╝╚██████╗███████╗██║
 ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚══════╝╚═╝
"""

# ============================================================
# SITE DEFINITIONS
# ============================================================

SITES = {
    "1": {"name": "nhentai", "desc": "nhentai.net - Manga/Doujinshi", "type": "manga"},
    "2": {"name": "hanime", "desc": "hanime.tv - Videos", "type": "video"},
    "3": {"name": "hentaihaven", "desc": "hentaihaven.xxx - Videos (yt-dlp)", "type": "video"},
    "4": {"name": "rule34", "desc": "rule34.xxx - Image board (API)", "type": "image"},
    "5": {"name": "gelbooru", "desc": "gelbooru.com - Image board (API)", "type": "image"},
    "6": {"name": "hitomi", "desc": "hitomi.la - Manga/Doujinshi", "type": "manga"},
    "7": {"name": "danbooru", "desc": "danbooru.donmai.us - Image board (no auth)", "type": "image"},
    "8": {"name": "konachan", "desc": "konachan.com - Image board (no auth)", "type": "image"},
    "9": {"name": "nhentai-lolicon", "desc": "nhentai.net - Lolicon tag", "type": "manga"},
    "10": {"name": "nhentai-incest", "desc": "nhentai.net - Incest tag", "type": "manga"},
    "11": {"name": "all", "desc": "All supported sites", "type": "all"},
}

THEMES = {
    "default": {"header": Fore.CYAN, "accent": Fore.MAGENTA, "success": Fore.GREEN,
                "warning": Fore.YELLOW, "error": Fore.RED, "text": Fore.WHITE},
    "fire": {"header": Fore.RED, "accent": Fore.YELLOW, "success": Fore.GREEN,
             "warning": Fore.YELLOW, "error": Fore.RED, "text": Fore.WHITE},
    "ocean": {"header": Fore.BLUE, "accent": Fore.CYAN, "success": Fore.GREEN,
              "warning": Fore.YELLOW, "error": Fore.RED, "text": Fore.WHITE},
    "matrix": {"header": Fore.GREEN, "accent": Fore.GREEN, "success": Fore.GREEN,
               "warning": Fore.YELLOW, "error": Fore.RED, "text": Fore.GREEN},
    "mono": {"header": Fore.WHITE, "accent": Fore.WHITE, "success": Fore.WHITE,
             "warning": Fore.WHITE, "error": Fore.WHITE, "text": Fore.WHITE},
    "pink": {"header": Fore.MAGENTA, "accent": Fore.MAGENTA, "success": Fore.GREEN,
             "warning": Fore.YELLOW, "error": Fore.RED, "text": Fore.WHITE},
}

# ============================================================
# CONFIG / HISTORY / BOOKMARKS / BLACKLIST MANAGEMENT
# ============================================================

class ConfigManager:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.config = self._load(CONFIG_FILE, {
            "theme": "default",
            "download_dir": DEFAULT_DOWNLOAD_DIR,
            "max_workers": 5,
            "proxy": "",
            "rate_limit": 0.5,
            "default_site": "all",
            "nhentai_mirrors": ["nhentai.net"],
            "auto_zip": False,
            "auto_cbz": False,
            "notify": True,
            "debug": False,
        })
        self.history = self._load(HISTORY_FILE, {"downloads": []})
        self.bookmarks = self._load(BOOKMARKS_FILE, {"bookmarks": []})
        self.blacklist = self._load(BLACKLIST_FILE, {"tags": [], "ids": []})

    def _load(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return default

    def save_config(self):
        self._save(CONFIG_FILE, self.config)

    def save_history(self):
        self._save(HISTORY_FILE, self.history)

    def save_bookmarks(self):
        self._save(BOOKMARKS_FILE, self.bookmarks)

    def save_blacklist(self):
        self._save(BLACKLIST_FILE, self.blacklist)

    def _save(self, path: str, data: Any):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_history(self, entry: dict):
        entry["date"] = datetime.now().isoformat()
        self.history["downloads"].append(entry)
        self.save_history()

    def add_bookmark(self, entry: dict):
        entry["date_added"] = datetime.now().isoformat()
        self.bookmarks["bookmarks"].append(entry)
        self.save_bookmarks()

    def remove_bookmark(self, index: int) -> bool:
        if 0 <= index < len(self.bookmarks["bookmarks"]):
            self.bookmarks["bookmarks"].pop(index)
            self.save_bookmarks()
            return True
        return False

    def is_blacklisted(self, tags: list[str] = None, gallery_id: str = None) -> bool:
        if gallery_id and gallery_id in self.blacklist.get("ids", []):
            return True
        if tags:
            bl_tags = set(t.lower() for t in self.blacklist.get("tags", []))
            if any(t.lower() in bl_tags for t in tags):
                return True
        return False


cfg = ConfigManager()

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

THEME = THEMES.get(cfg.config.get("theme", "default"), THEMES["default"])


# ============================================================
# DEBUG LOGGER
# ============================================================

class DLog:
    """Developer mode logger. Outputs to terminal AND logs to file when debug is enabled."""

    LOG_FILE = os.path.join(CONFIG_DIR, "debug.log")

    @staticmethod
    def _write_file(level: str, msg: str):
        if not DLog.is_enabled():
            return
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(DLog.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] [{level}] {msg}\n")
        except Exception:
            pass

    @staticmethod
    def is_enabled() -> bool:
        return cfg.config.get("debug", False)

    @staticmethod
    def log(msg: str):
        if DLog.is_enabled():
            cprint(f"  [DEBUG] {msg}", Fore.BLUE if HAS_COLOR else "")
            DLog._write_file("DEBUG", msg)

    @staticmethod
    def request(method: str, url: str, status: int = 0, elapsed: float = 0, extra: str = ""):
        if DLog.is_enabled():
            status_str = f" -> {status}" if status else ""
            time_str = f" ({elapsed:.1f}ms)" if elapsed else ""
            extra_str = f" | {extra}" if extra else ""
            line = f"  [HTTP] {method} {url}{status_str}{time_str}{extra_str}"
            cprint(line, Fore.BLUE if HAS_COLOR else "")
            DLog._write_file("HTTP", f"{method} {url}{status_str}{time_str}{extra_str}")

    @staticmethod
    def error(msg: str, exc: Exception = None):
        if DLog.is_enabled():
            cprint(f"  [ERROR] {msg}", Fore.RED if HAS_COLOR else "")
            tb_str = ""
            if exc:
                for line in traceback.format_exception(type(exc), exc, exc.__traceback__):
                    for sub in line.strip().split("\n"):
                        cprint(f"    {sub}", Fore.RED if HAS_COLOR else "")
                        tb_str += sub + "\n"
            DLog._write_file("ERROR", f"{msg}\n{tb_str}")

    @staticmethod
    def file(op: str, path: str, size: int = 0):
        if DLog.is_enabled():
            size_str = f" ({size} bytes)" if size else ""
            cprint(f"  [FILE] {op}: {path}{size_str}", Fore.BLUE if HAS_COLOR else "")
            DLog._write_file("FILE", f"{op}: {path}{size_str}")

    @staticmethod
    def info(msg: str):
        if DLog.is_enabled():
            cprint(f"  [INFO] {msg}", Fore.BLUE if HAS_COLOR else "")
            DLog._write_file("INFO", msg)


def cprint(text: str, color: str = ""):
    if HAS_COLOR and color:
        print(f"{color}{text}{Style.RESET_ALL}")
    else:
        print(text)


def show_banner():
    os.system("cls" if os.name == "nt" else "clear")
    cprint(BANNER, THEME["header"])
    cprint(f"  v{VERSION}", THEME["warning"])
    cprint(f"  made by {AUTHOR}", THEME["accent"])
    if cfg.config.get("debug", False):
        cprint("  [DEV MODE]", THEME["error"])
        cprint(f"  Log: {DLog.LOG_FILE}", THEME["text"])
    splash = SPLASH_TEXTS[hash(str(time.time())) % len(SPLASH_TEXTS)]
    cprint(f'  "{splash}"', THEME["text"])
    print()


def input_prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{THEME['success']}> {msg}{suffix}: {Style.RESET_ALL}").strip()
    return val if val else default


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 2.0, description: str = ""):
    last_err = None
    for attempt in range(max_retries):
        start = time.time()
        try:
            result = func()
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", description or "request", elapsed=elapsed)
            return result
        except requests.exceptions.HTTPError as e:
            elapsed = (time.time() - start) * 1000
            status = getattr(e.response, "status_code", 0)
            DLog.error(f"HTTP {status} on {description} (attempt {attempt + 1}/{max_retries}, {elapsed:.0f}ms)", e)
            if status == 429:
                delay = base_delay * (2 ** attempt)
                cprint(f"  [!] Rate limited. Waiting {delay:.0f}s...", THEME["warning"])
                time.sleep(delay)
                last_err = e
                continue
            if 500 <= status < 600:
                delay = base_delay * (2 ** attempt)
                if description:
                    cprint(f"  [!] Server error on {description}. Retry in {delay:.0f}s...", THEME["warning"])
                time.sleep(delay)
                last_err = e
                continue
            raise
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            delay = base_delay * (2 ** attempt)
            DLog.error(f"Connection error on {description} (attempt {attempt + 1}/{max_retries})", e)
            if description:
                cprint(f"  [!] Connection error on {description}. Retry in {delay:.0f}s...", THEME["warning"])
            time.sleep(delay)
            last_err = e
            continue
        except Exception as e:
            DLog.error(f"Unexpected error on {description}", e)
            raise
    if last_err:
        raise last_err


def file_hash(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_termux() -> bool:
    return "TERMUX_VERSION" in os.environ or "com.termux" in os.environ


def send_notification(title: str, message: str):
    if is_termux() and cfg.config.get("notify", True):
        try:
            subprocess.run(
                ["termux-notification", "--title", title, "--content", message],
                timeout=5, capture_output=True
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


def set_wallpaper(filepath: str):
    if is_termux():
        try:
            subprocess.run(["termux-wallpaper", filepath], timeout=10, capture_output=True)
            cprint("[*] Wallpaper set!", THEME["success"])
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    cprint("[!] Wallpaper only works on Termux with termux-api installed.", THEME["warning"])
    return False


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    })
    proxy = cfg.config.get("proxy", "")
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
        DLog.log(f"Proxy configured: {proxy}")

    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# ============================================================
# NHENTAI DOWNLOADER
# ============================================================

class NHentaiDownloader:
    API_BASE = "https://nhentai.net/api/v2"
    IMAGE_SERVERS = [
        "https://i1.nhentai.net",
        "https://i2.nhentai.net",
        "https://i3.nhentai.net",
        "https://i4.nhentai.net",
    ]

    def __init__(self):
        self.session = create_session()
        self.max_workers = cfg.config.get("max_workers", 5)
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str, page: int = 1, sort: str = "") -> dict:
        params: dict[str, Any] = {"query": query, "page": page}
        if sort:
            params["sort"] = sort
        DLog.info(f"nhentai search: query={query}, page={page}, sort={sort}")
        r = retry_with_backoff(
            lambda: self.session.get(f"{self.API_BASE}/search", params=params, timeout=15),
            description=f"search '{query}'"
        )
        r.raise_for_status()
        data = r.json()
        DLog.info(f"nhentai search returned {len(data.get('result', []))} results, total={data.get('total', 0)}")
        return data

    def get_gallery(self, gallery_id: int) -> dict:
        DLog.info(f"nhentai get_gallery: id={gallery_id}")
        r = retry_with_backoff(
            lambda: self.session.get(f"{self.API_BASE}/galleries/{gallery_id}", timeout=15),
            description=f"gallery {gallery_id}"
        )
        r.raise_for_status()
        return r.json()

    def get_random(self) -> dict:
        r = retry_with_backoff(
            lambda: self.session.get(f"{self.API_BASE}/galleries/random", timeout=15),
            description="random gallery"
        )
        r.raise_for_status()
        data = r.json()
        return self.get_gallery(data["id"])

    def get_popular(self) -> list[dict]:
        r = retry_with_backoff(
            lambda: self.session.get(f"{self.API_BASE}/galleries/popular", timeout=15),
            description="popular galleries"
        )
        r.raise_for_status()
        return r.json()

    def get_page_urls(self, gallery: dict) -> list[str]:
        media_id = gallery.get("media_id", "")
        pages = gallery.get("pages", [])
        urls = []
        for i, page in enumerate(pages):
            path = page.get("path", "")
            ext = path.split(".")[-1] if "." in path else "jpg"
            server = self.IMAGE_SERVERS[i % len(self.IMAGE_SERVERS)]
            urls.append(f"{server}/galleries/{media_id}/{i + 1}.{ext}")
        return urls

    def _download_one(self, args: tuple) -> tuple[int, bool]:
        i, url, output_dir = args
        ext = url.split(".")[-1].split("?")[0]
        filepath = os.path.join(output_dir, f"{i + 1:03d}.{ext}")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            DLog.log(f"Skipped (exists): {filepath}")
            return (i, True)
        try:
            DLog.request("GET", url)
            start = time.time()
            r = self.session.get(url, timeout=30)
            elapsed = (time.time() - start) * 1000
            r.raise_for_status()
            content_length = int(r.headers.get("content-length", 0))
            with open(filepath, "wb") as f:
                f.write(r.content)
            actual_size = os.path.getsize(filepath)
            DLog.file("WRITE", filepath, actual_size)
            DLog.request("GET", url, status=r.status_code, elapsed=elapsed,
                        extra=f"size={actual_size}, expected={content_length}")
            if content_length and actual_size != content_length:
                DLog.error(f"Size mismatch: got {actual_size}, expected {content_length} for {url}")
                os.remove(filepath)
                return (i, False)
            return (i, True)
        except Exception as e:
            DLog.error(f"Download failed: {url}", e)
            if os.path.exists(filepath):
                os.remove(filepath)
            return (i, False)

    def download_gallery(self, gallery_id: int, output_dir: str) -> bool:
        gallery = self.get_gallery(gallery_id)
        if not gallery:
            return False

        title = gallery.get("title", {}).get("english") or \
                gallery.get("title", {}).get("pretty") or \
                f"gallery_{gallery_id}"
        title = re.sub(r'[\\/:*?"<>|]', '_', title)[:80]
        tags = [t.get("name", "") for t in gallery.get("tags", [])]

        if cfg.is_blacklisted(tags=tags, gallery_id=str(gallery_id)):
            cprint(f"  [!] Skipped (blacklisted): {title}", THEME["warning"])
            return False

        pages = self.get_page_urls(gallery)
        if not pages:
            cprint(f"  [!] No pages for {gallery_id}", THEME["error"])
            return False

        gallery_dir = os.path.join(output_dir, f"nhentai_{gallery_id}_{title}")
        os.makedirs(gallery_dir, exist_ok=True)

        cprint(f"  [{gallery_id}] {title} ({len(pages)} pages)", THEME["accent"])
        time.sleep(self.rate_limit)

        tasks = [(i, url, gallery_dir) for i, url in enumerate(pages)]
        success = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_one, t): t for t in tasks}
            for future in as_completed(futures):
                _, ok = future.result()
                if ok:
                    success += 1

        cprint(f"  -> {success}/{len(pages)} pages downloaded", THEME["success"])

        cfg.add_history({
            "id": str(gallery_id),
            "site": "nhentai",
            "title": title,
            "tags": tags,
            "path": gallery_dir,
            "type": "manga",
            "pages": len(pages),
        })

        if cfg.config.get("auto_zip"):
            _zip_folder(gallery_dir)
        if cfg.config.get("auto_cbz"):
            _cbz_folder(gallery_dir)

        return True

    def search_and_download(self, query: str, count: int, output_dir: str, sort: str = ""):
        cprint(f"\n  [nhentai] Searching for '{query}'...", THEME["header"])
        try:
            result = self.search(query, sort=sort)
        except Exception as e:
            cprint(f"  [!] Search failed: {e}", THEME["error"])
            return

        galleries = result.get("result", [])
        total = result.get("total", 0)
        cprint(f"  Found {total} results, downloading up to {count}", THEME["success"])

        downloaded = 0
        for gallery in galleries:
            if downloaded >= count:
                break
            gid = gallery.get("id")
            if gid and self.download_gallery(gid, output_dir):
                downloaded += 1

        cprint(f"\n  [nhentai] Downloaded {downloaded} galleries", THEME["success"])

    def show_info(self, gallery_id: int):
        gallery = self.get_gallery(gallery_id)
        if not gallery:
            cprint(f"  [!] Gallery {gallery_id} not found", THEME["error"])
            return

        title = gallery.get("title", {}).get("english") or \
                gallery.get("title", {}).get("pretty") or "Unknown"
        tags = [t.get("name", "") for t in gallery.get("tags", [])]
        artist = next((t["name"] for t in gallery.get("tags", []) if t.get("type") == "artist"), "Unknown")
        language = next((t["name"] for t in gallery.get("tags", []) if t.get("type") == "language"), "Unknown")

        print()
        cprint(f"  Title:    {title}", THEME["text"])
        cprint(f"  ID:       {gallery_id}", THEME["text"])
        cprint(f"  Pages:    {gallery.get('num_pages', '?')}", THEME["text"])
        cprint(f"  Favorites:{gallery.get('num_favorites', '?')}", THEME["text"])
        cprint(f"  Artist:   {artist}", THEME["text"])
        cprint(f"  Language: {language}", THEME["text"])
        cprint(f"  Tags:     {', '.join(tags[:15])}", THEME["text"])
        print()


# ============================================================
# HANIME DOWNLOADER
# ============================================================

class HanimeDownloader:
    BASE_URL = "https://hanime.tv"

    def __init__(self):
        self.session = create_session()
        self.session.headers["Referer"] = self.BASE_URL
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str) -> list[dict]:
        results = []
        DLog.info(f"hanime search: query={query}")
        for endpoint in ["/api/v2/search", "/api/v1/search", "/search", "/search/query"]:
            try:
                DLog.request("GET", f"{self.BASE_URL}{endpoint}?q={query}")
                start = time.time()
                r = self.session.get(f"{self.BASE_URL}{endpoint}", params={"q": query}, timeout=15)
                elapsed = (time.time() - start) * 1000
                DLog.request("GET", f"{self.BASE_URL}{endpoint}", status=r.status_code, elapsed=elapsed)
                if r.status_code in (404, 500, 502, 503):
                    DLog.info(f"hanime endpoint {endpoint} returned {r.status_code}, trying next")
                    continue
                r.raise_for_status()
                try:
                    data = r.json()
                    for item in data.get("results", data.get("data", data.get("videos", [])))[:20]:
                        slug = item.get("slug", item.get("id", ""))
                        title = item.get("name", item.get("title", slug))
                        if slug:
                            results.append({"slug": slug, "title": title})
                except (json.JSONDecodeError, ValueError):
                    if BeautifulSoup:
                        soup = BeautifulSoup(r.text, "html.parser")
                        for a in soup.select("a[href*='/watch/']"):
                            href = a.get("href", "")
                            slug = href.rstrip("/").split("/")[-1]
                            title = a.get_text(strip=True) or slug
                            if slug and title and len(title) > 1:
                                results.append({"slug": slug, "title": title})
                if results:
                    return results[:20]
            except Exception as e:
                DLog.info(f"hanime endpoint {endpoint} failed: {e}")
                continue
        return results

    def get_video_url(self, slug: str) -> Optional[str]:
        url = f"{self.BASE_URL}/watch/{slug}"
        DLog.info(f"hanime get_video_url: slug={slug}, url={url}")
        try:
            start = time.time()
            r = self.session.get(url, timeout=15)
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", url, status=r.status_code, elapsed=elapsed)
            r.raise_for_status()
            if BeautifulSoup:
                soup = BeautifulSoup(r.text, "html.parser")
                for script in soup.find_all("script"):
                    text = script.string or ""
                    for pattern in [
                        r'"video_url"\s*:\s*"([^"]+)"',
                        r'"file"\s*:\s*"([^"]+\.mp4[^"]*)"',
                        r'videoUrl\s*=\s*["\']([^"\']+)',
                    ]:
                        match = re.search(pattern, text)
                        if match:
                            vid_url = match.group(1).replace("\\u0026", "&")
                            DLog.info(f"hanime found video URL (bs4): {vid_url[:80]}...")
                            return vid_url
            html = r.text
            for pattern in [
                r'"video_url"\s*:\s*"([^"]+)"',
                r'"file"\s*:\s*"([^"]+\.mp4[^"]*)"',
                r'source\s+src="([^"]+\.mp4[^"]*)"',
            ]:
                match = re.search(pattern, html)
                if match:
                    vid_url = match.group(1).replace("\\u0026", "&")
                    DLog.info(f"hanime found video URL (regex): {vid_url[:80]}...")
                    return vid_url
            DLog.error(f"hanime: no video URL pattern matched for {slug}")
        except Exception as e:
            DLog.error(f"hanime get_video_url failed: {slug}", e)
            cprint(f"  [!] Error fetching {slug}: {e}", THEME["error"])
        return None

    def download_video(self, slug: str, output_dir: str) -> bool:
        video_url = self.get_video_url(slug)
        if not video_url:
            cprint(f"  [!] No video URL for {slug}", THEME["error"])
            return False

        filepath = os.path.join(output_dir, f"hanime_{slug}.mp4")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            cprint(f"  [~] Already exists: {slug}", THEME["warning"])
            return True

        cprint(f"  Downloading: {slug}", THEME["accent"])
        DLog.request("GET", video_url, extra="stream=True")
        try:
            start = time.time()
            r = self.session.get(video_url, timeout=120, stream=True)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            DLog.info(f"hanime video response: status={r.status_code}, content-length={total}")
            downloaded = 0

            with open(filepath, "wb") as f:
                if tqdm and total:
                    with tqdm(total=total, unit="B", unit_scale=True, desc=slug[:30]) as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            pbar.update(len(chunk))
                else:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = (downloaded / total) * 100
                            sys.stdout.write(f"\r    [{pct:.1f}%] {downloaded}/{total}")
                            sys.stdout.flush()
            print()

            if total and os.path.getsize(filepath) != total:
                os.remove(filepath)
                cprint(f"  [!] Incomplete download, retrying...", THEME["warning"])
                return self.download_video(slug, output_dir)

            cfg.add_history({
                "id": slug,
                "site": "hanime",
                "title": slug,
                "path": filepath,
                "type": "video",
                "size": os.path.getsize(filepath),
            })
            return True
        except Exception as e:
            cprint(f"\n  [!] Download error: {e}", THEME["error"])
            if os.path.exists(filepath):
                os.remove(filepath)
            return False

    def search_and_download(self, query: str, count: int, output_dir: str):
        cprint(f"\n  [hanime] Searching for '{query}'...", THEME["header"])
        results = self.search(query)
        if not results:
            cprint("  [!] No results found", THEME["error"])
            return

        cprint(f"  Found {len(results)} results", THEME["success"])
        for i, item in enumerate(results[:count]):
            cprint(f"    {i + 1}. {item['title'][:60]}", THEME["text"])

        downloaded = 0
        for item in results:
            if downloaded >= count:
                break
            time.sleep(self.rate_limit)
            if self.download_video(item["slug"], output_dir):
                downloaded += 1

        cprint(f"\n  [hanime] Downloaded {downloaded} videos", THEME["success"])


# ============================================================
# HENTAIHAVEN DOWNLOADER (with yt-dlp)
# ============================================================

class HentaiHavenDownloader:
    BASE_URL = "https://hentaihaven.xxx"

    def __init__(self):
        self.session = create_session()
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str) -> list[dict]:
        results = []
        DLog.info(f"hentaihaven search: query={query}")
        try:
            for params in [
                {"s": query, "post_type": "wp-manga"},
                {"s": query},
            ]:
                DLog.request("GET", f"{self.BASE_URL}?s={query}")
                start = time.time()
                r = self.session.get(self.BASE_URL, params=params, timeout=15)
                elapsed = (time.time() - start) * 1000
                DLog.request("GET", self.BASE_URL, status=r.status_code, elapsed=elapsed)
                r.raise_for_status()
                if BeautifulSoup:
                    soup = BeautifulSoup(r.text, "html.parser")
                    for a in soup.select("a[href]"):
                        href = a.get("href", "")
                        title = a.get_text(strip=True)
                        if not title or len(title) < 3:
                            continue
                        if "hentaihaven" in href and "/series/" in href:
                            slug = href.rstrip("/").split("/")[-1] or href.rstrip("/").split("/")[-2]
                            results.append({"slug": slug, "title": title, "url": href})
                        elif "hentaihaven" in href and href.rstrip("/").count("/") >= 3:
                            slug = href.rstrip("/").split("/")[-2] if href.endswith("/") else href.rstrip("/").split("/")[-1]
                            if slug and slug not in ("www", "http:", "https:"):
                                results.append({"slug": slug, "title": title, "url": href})
                seen = set()
                unique = []
                for r_item in results:
                    key = r_item.get("slug", r_item.get("url"))
                    if key not in seen:
                        seen.add(key)
                        unique.append(r_item)
                results = unique
                if results:
                    break
            DLog.info(f"hentaihaven found {len(results)} results")
        except Exception as e:
            DLog.error("hentaihaven search failed", e)
            cprint(f"  [!] Search error: {e}", THEME["error"])
        return results[:20]

    def _has_ytdlp(self) -> bool:
        found = shutil.which("yt-dlp") is not None
        DLog.info(f"hentaihaven yt-dlp available: {found}")
        return found

    def search_and_download(self, query: str, count: int, output_dir: str):
        cprint(f"\n  [hentaihaven] Searching for '{query}'...", THEME["header"])
        results = self.search(query)
        if not results:
            cprint("  [!] No results or site unavailable", THEME["error"])
            return

        cprint(f"  Found {len(results)} results:", THEME["success"])
        for i, item in enumerate(results[:count]):
            cprint(f"    {i + 1}. {item['title'][:60]}", THEME["text"])

        if not self._has_ytdlp():
            cprint("\n  [!] yt-dlp not found. Install it:", THEME["warning"])
            cprint("    pip install yt-dlp", THEME["text"])
            cprint("  or:", THEME["text"])
            cprint("    pkg install yt-dlp", THEME["text"])
            return

        downloaded = 0
        for item in results[:count]:
            time.sleep(self.rate_limit)
            url = item.get("url", f"{self.BASE_URL}/{item['slug']}/")
            cprint(f"  Downloading: {item['title'][:50]}", THEME["accent"])
            DLog.info(f"yt-dlp URL: {url}")
            try:
                result = subprocess.run(
                    ["yt-dlp", "-o", f"{output_dir}/%(title)s.%(ext)s", "--no-warnings", url],
                    capture_output=True, text=True, timeout=300
                )
                DLog.log(f"yt-dlp exit code: {result.returncode}")
                if result.stdout:
                    DLog.log(f"yt-dlp stdout: {result.stdout[:200]}")
                if result.stderr:
                    DLog.log(f"yt-dlp stderr: {result.stderr[:200]}")
                if result.returncode == 0:
                    downloaded += 1
                    cfg.add_history({
                        "id": item["slug"],
                        "site": "hentaihaven",
                        "title": item["title"],
                        "path": output_dir,
                        "type": "video",
                    })
                else:
                    cprint(f"    [!] yt-dlp error: {result.stderr[:100]}", THEME["error"])
            except subprocess.TimeoutExpired:
                DLog.error(f"yt-dlp timed out for {url}")
                cprint(f"    [!] Download timed out", THEME["error"])
            except FileNotFoundError:
                cprint("  [!] yt-dlp not found. Install: pip install yt-dlp", THEME["error"])
                return

        cprint(f"\n  [hentaihaven] Downloaded {downloaded} videos", THEME["success"])


# ============================================================
# NHENTAI TAG DOWNLOADER (for specific tags)
# ============================================================

class NHentaiTagDownloader(NHentaiDownloader):
    def __init__(self, tag_slug: str, tag_name: str):
        super().__init__()
        self.tag_slug = tag_slug
        self.tag_name = tag_name

    def search_and_download(self, query: str, count: int, output_dir: str, sort: str = ""):
        cprint(f"\n  [nhentai:{self.tag_name}] Looking up tag...", THEME["header"])
        try:
            r = self.session.get(f"{self.API_BASE}/tags/tag/{self.tag_slug}", timeout=15)
            if r.status_code == 404:
                cprint(f"  [!] Tag '{self.tag_name}' not found on nhentai (404). Skipping.", THEME["warning"])
                DLog.info(f"nhentai tag '{self.tag_slug}' returned 404")
                return
            r.raise_for_status()
            tag_info = r.json()
        except Exception as e:
            cprint(f"  [!] Tag lookup failed: {e}", THEME["error"])
            return

        tag_id = tag_info.get("id")
        if not tag_id:
            cprint(f"  [!] Tag '{self.tag_name}' not found", THEME["error"])
            return

        cprint(f"  Tag: {tag_info.get('name', self.tag_name)} ({tag_info.get('count', 0)} galleries)", THEME["success"])

        try:
            params: dict[str, Any] = {"tag_id": tag_id, "page": 1}
            if sort:
                params["sort"] = sort
            r = self.session.get(f"{self.API_BASE}/galleries/tagged", params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            cprint(f"  [!] Search failed: {e}", THEME["error"])
            return

        galleries = data.get("result", [])
        if query:
            galleries = [g for g in galleries if query.lower() in
                        (g.get("title", "") + " " + str(g.get("tag_ids", []))).lower()]

        downloaded = 0
        for gallery in galleries:
            if downloaded >= count:
                break
            gid = gallery.get("id")
            if gid and self.download_gallery(gid, output_dir):
                downloaded += 1

        cprint(f"\n  [nhentai:{self.tag_name}] Downloaded {downloaded} galleries", THEME["success"])


# ============================================================
# RULE34 DOWNLOADER (API)
# ============================================================

class Rule34Downloader:
    API_BASE = "https://rule34.xxx/index.php"

    def __init__(self):
        self.session = create_session()
        self.max_workers = cfg.config.get("max_workers", 5)
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str, limit: int = 100, pid: int = 1) -> list[dict]:
        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "json": 1,
            "limit": min(limit, 100),
            "pid": pid,
            "tags": query,
        }
        DLog.info(f"rule34 search: query={query}, limit={limit}, page={pid}")
        try:
            start = time.time()
            r = self.session.get(self.API_BASE, params=params, timeout=15)
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", self.API_BASE, status=r.status_code, elapsed=elapsed)
            r.raise_for_status()
            text = r.text.strip()
            if not text or text == "null" or text == '""':
                DLog.info("rule34: empty response")
                return []
            data = r.json()
            if isinstance(data, str):
                data = json.loads(data)
            if isinstance(data, list):
                posts = data
            elif isinstance(data, dict):
                posts = data.get("post", [])
            elif data is None:
                posts = []
            else:
                posts = []
            DLog.info(f"rule34 returned {len(posts)} posts")
            return posts if isinstance(posts, list) else []
        except json.JSONDecodeError as e:
            DLog.error(f"rule34: JSON decode error (response: {r.text[:200]})", e)
            return []
        except Exception as e:
            DLog.error("rule34 search failed", e)
            return []

    def _download_one(self, args: tuple) -> tuple[int, bool]:
        i, post, output_dir = args
        file_url = post.get("file_url", "")
        if not file_url:
            return (i, False)

        post_id = post.get("id", i)
        ext = file_url.split(".")[-1].split("?")[0]
        filepath = os.path.join(output_dir, f"rule34_{post_id}.{ext}")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            DLog.log(f"Skipped (exists): {filepath}")
            return (i, True)

        try:
            DLog.request("GET", file_url)
            start = time.time()
            r = self.session.get(file_url, timeout=30)
            elapsed = (time.time() - start) * 1000
            r.raise_for_status()
            content_length = int(r.headers.get("content-length", 0))
            with open(filepath, "wb") as f:
                f.write(r.content)
            actual_size = os.path.getsize(filepath)
            DLog.file("WRITE", filepath, actual_size)
            DLog.request("GET", file_url, status=r.status_code, elapsed=elapsed)
            if content_length and actual_size != content_length:
                DLog.error(f"Size mismatch for {file_url}")
                os.remove(filepath)
                return (i, False)
            return (i, True)
        except Exception as e:
            DLog.error(f"rule34 download failed: {file_url}", e)
            if os.path.exists(filepath):
                os.remove(filepath)
            return (i, False)

    def search_and_download(self, query: str, count: int, output_dir: str):
        cprint(f"\n  [rule34] Searching for '{query}'...", THEME["header"])
        posts = self.search(query, limit=count)
        if not posts:
            cprint("  [!] No results found", THEME["error"])
            return

        posts = posts[:count]
        tags_set = set()
        for p in posts:
            for t in p.get("tags", "").split():
                if t:
                    tags_set.add(t)

        if cfg.is_blacklisted(tags=list(tags_set)):
            cprint("  [!] Results match blacklisted tags", THEME["warning"])
            return

        cprint(f"  Found {len(posts)} posts, downloading...", THEME["success"])

        site_dir = os.path.join(output_dir, f"rule34_{query.replace(' ', '_')}")
        os.makedirs(site_dir, exist_ok=True)

        tasks = [(i, p, site_dir) for i, p in enumerate(posts)]
        success = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_one, t): t for t in tasks}
            for future in as_completed(futures):
                _, ok = future.result()
                if ok:
                    success += 1

        cprint(f"  -> {success}/{len(posts)} images downloaded", THEME["success"])

        for p in posts:
            cfg.add_history({
                "id": str(p.get("id", "")),
                "site": "rule34",
                "title": f"rule34 #{p.get('id', '?')}",
                "tags": p.get("tags", "").split(),
                "path": site_dir,
                "type": "image",
                "size": os.path.getsize(os.path.join(site_dir, f"rule34_{p.get('id')}.{p.get('file_url', '').split('.')[-1].split('?')[0]}"))
                if os.path.exists(os.path.join(site_dir, f"rule34_{p.get('id')}.{p.get('file_url', '').split('.')[-1].split('?')[0]}")) else 0,
            })


# ============================================================
# GELBOORU DOWNLOADER (API)
# ============================================================

class GelbooruDownloader:
    API_BASE = "https://gelbooru.com/index.php"

    def __init__(self):
        self.session = create_session()
        self.max_workers = cfg.config.get("max_workers", 5)
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str, limit: int = 20, pid: int = 1) -> list[dict]:
        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "json": 1,
            "limit": min(limit, 100),
            "pid": pid,
            "tags": query,
        }
        DLog.info(f"gelbooru search: query={query}, limit={limit}, page={pid}")
        try:
            start = time.time()
            r = self.session.get(self.API_BASE, params=params, timeout=15)
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", self.API_BASE, status=r.status_code, elapsed=elapsed)
            if r.status_code == 401:
                DLog.error("gelbooru: 401 Unauthorized - API may require auth key")
                cprint("  [!] gelbooru: API requires authentication. Skipping.", THEME["warning"])
                return []
            if r.status_code == 403:
                DLog.error("gelbooru: 403 Forbidden - IP may be blocked")
                cprint("  [!] gelbooru: Access forbidden. Skipping.", THEME["warning"])
                return []
            r.raise_for_status()
            text = r.text.strip()
            if not text or text == "null":
                return []
            data = r.json()
            if isinstance(data, dict):
                posts = data.get("post", [])
            elif isinstance(data, list):
                posts = data
            else:
                posts = []
            DLog.info(f"gelbooru returned {len(posts)} posts")
            return posts if isinstance(posts, list) else []
        except json.JSONDecodeError as e:
            DLog.error("gelbooru: JSON decode error", e)
            return []
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 0)
            DLog.error(f"gelbooru: HTTP {status} error", e)
            if status in (401, 403):
                cprint(f"  [!] gelbooru: HTTP {status} - API key may be required", THEME["warning"])
            return []
        except Exception as e:
            DLog.error("gelbooru search failed", e)
            return []

    def _download_one(self, args: tuple) -> tuple[int, bool]:
        i, post, output_dir = args
        file_url = post.get("file_url", "")
        if not file_url:
            return (i, False)

        post_id = post.get("id", i)
        ext = file_url.split(".")[-1].split("?")[0]
        filepath = os.path.join(output_dir, f"gelbooru_{post_id}.{ext}")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return (i, True)

        try:
            DLog.request("GET", file_url)
            start = time.time()
            r = self.session.get(file_url, timeout=30)
            elapsed = (time.time() - start) * 1000
            r.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(r.content)
            DLog.file("WRITE", filepath, os.path.getsize(filepath))
            DLog.request("GET", file_url, status=r.status_code, elapsed=elapsed)
            return (i, True)
        except Exception as e:
            DLog.error(f"gelbooru download failed: {file_url}", e)
            if os.path.exists(filepath):
                os.remove(filepath)
            return (i, False)

    def search_and_download(self, query: str, count: int, output_dir: str):
        cprint(f"\n  [gelbooru] Searching for '{query}'...", THEME["header"])
        posts = self.search(query, limit=count)
        if not posts:
            cprint("  [!] No results found", THEME["error"])
            return

        posts = posts[:count]
        all_tags = set()
        for p in posts:
            for t in p.get("tags", "").split():
                if t:
                    all_tags.add(t)

        if cfg.is_blacklisted(tags=list(all_tags)):
            cprint("  [!] Results match blacklisted tags", THEME["warning"])
            return

        cprint(f"  Found {len(posts)} posts, downloading...", THEME["success"])

        site_dir = os.path.join(output_dir, f"gelbooru_{query.replace(' ', '_')}")
        os.makedirs(site_dir, exist_ok=True)

        tasks = [(i, p, site_dir) for i, p in enumerate(posts)]
        success = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_one, t): t for t in tasks}
            for future in as_completed(futures):
                _, ok = future.result()
                if ok:
                    success += 1

        cprint(f"  -> {success}/{len(posts)} images downloaded", THEME["success"])

        for p in posts:
            cfg.add_history({
                "id": str(p.get("id", "")),
                "site": "gelbooru",
                "title": f"gelbooru #{p.get('id', '?')}",
                "tags": p.get("tags", "").split(),
                "path": site_dir,
                "type": "image",
            })


# ============================================================
# DANBOORU DOWNLOADER (no auth required for read)
# ============================================================

class DanbooruDownloader:
    API_BASE = "https://danbooru.donmai.us"

    def __init__(self):
        self.session = create_session()
        self.session.headers["User-Agent"] = "gooningCLI/2.1 (https://github.com/StreliziaSystems/gooningCLI)"
        self.max_workers = cfg.config.get("max_workers", 5)
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str, limit: int = 20, page: int = 1) -> list[dict]:
        params = {
            "tags": query,
            "limit": min(limit, 200),
            "page": page,
        }
        DLog.info(f"danbooru search: query={query}, limit={limit}, page={page}")
        try:
            start = time.time()
            r = self.session.get(f"{self.API_BASE}/posts.json", params=params, timeout=15)
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", f"{self.API_BASE}/posts.json", status=r.status_code, elapsed=elapsed)
            r.raise_for_status()
            data = r.json()
            posts = data if isinstance(data, list) else []
            DLog.info(f"danbooru returned {len(posts)} posts")
            return posts
        except json.JSONDecodeError as e:
            DLog.error("danbooru: JSON decode error", e)
            return []
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 0)
            DLog.error(f"danbooru: HTTP {status} error", e)
            cprint(f"  [!] danbooru: HTTP {status}", THEME["warning"])
            return []
        except Exception as e:
            DLog.error("danbooru search failed", e)
            return []

    def _download_one(self, args: tuple) -> tuple[int, bool]:
        i, post, output_dir = args
        file_url = post.get("file_url") or post.get("large_file_url") or ""
        if not file_url:
            return (i, False)

        post_id = post.get("id", i)
        ext = file_url.split(".")[-1].split("?")[0] or "jpg"
        filepath = os.path.join(output_dir, f"danbooru_{post_id}.{ext}")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return (i, True)

        try:
            DLog.request("GET", file_url)
            start = time.time()
            r = self.session.get(file_url, timeout=30)
            elapsed = (time.time() - start) * 1000
            r.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(r.content)
            DLog.file("WRITE", filepath, os.path.getsize(filepath))
            DLog.request("GET", file_url, status=r.status_code, elapsed=elapsed)
            return (i, True)
        except Exception as e:
            DLog.error(f"danbooru download failed: {file_url}", e)
            if os.path.exists(filepath):
                os.remove(filepath)
            return (i, False)

    def search_and_download(self, query: str, count: int, output_dir: str):
        cprint(f"\n  [danbooru] Searching for '{query}'...", THEME["header"])
        posts = self.search(query, limit=count)
        if not posts:
            cprint("  [!] No results found", THEME["error"])
            return

        posts = posts[:count]
        all_tags = set()
        for p in posts:
            for t in p.get("tag_string", "").split():
                if t:
                    all_tags.add(t)

        if cfg.is_blacklisted(tags=list(all_tags)):
            cprint("  [!] Results match blacklisted tags", THEME["warning"])
            return

        cprint(f"  Found {len(posts)} posts, downloading...", THEME["success"])

        site_dir = os.path.join(output_dir, f"danbooru_{query.replace(' ', '_')}")
        os.makedirs(site_dir, exist_ok=True)

        tasks = [(i, p, site_dir) for i, p in enumerate(posts)]
        success = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_one, t): t for t in tasks}
            for future in as_completed(futures):
                _, ok = future.result()
                if ok:
                    success += 1

        cprint(f"  -> {success}/{len(posts)} images downloaded", THEME["success"])

        for p in posts:
            cfg.add_history({
                "id": str(p.get("id", "")),
                "site": "danbooru",
                "title": f"danbooru #{p.get('id', '?')}",
                "tags": p.get("tag_string", "").split(),
                "path": site_dir,
                "type": "image",
            })


# ============================================================
# KONACHAN DOWNLOADER (no auth required)
# ============================================================

class KonachanDownloader:
    API_BASE = "https://konachan.com"

    def __init__(self):
        self.session = create_session()
        self.session.headers["User-Agent"] = "gooningCLI/2.1 (https://github.com/StreliziaSystems/gooningCLI)"
        self.max_workers = cfg.config.get("max_workers", 5)
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str, limit: int = 20, page: int = 1) -> list[dict]:
        params = {
            "tags": query,
            "limit": min(limit, 200),
            "page": page,
        }
        DLog.info(f"konachan search: query={query}, limit={limit}, page={page}")
        try:
            start = time.time()
            r = self.session.get(f"{self.API_BASE}/post.json", params=params, timeout=15)
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", f"{self.API_BASE}/post.json", status=r.status_code, elapsed=elapsed)
            r.raise_for_status()
            data = r.json()
            posts = data if isinstance(data, list) else []
            DLog.info(f"konachan returned {len(posts)} posts")
            return posts
        except json.JSONDecodeError as e:
            DLog.error("konachan: JSON decode error", e)
            return []
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 0)
            DLog.error(f"konachan: HTTP {status} error", e)
            cprint(f"  [!] konachan: HTTP {status}", THEME["warning"])
            return []
        except Exception as e:
            DLog.error("konachan search failed", e)
            return []

    def _download_one(self, args: tuple) -> tuple[int, bool]:
        i, post, output_dir = args
        file_url = post.get("file_url") or ""
        if not file_url:
            return (i, False)

        post_id = post.get("id", i)
        ext = file_url.split(".")[-1].split("?")[0] or "jpg"
        filepath = os.path.join(output_dir, f"konachan_{post_id}.{ext}")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return (i, True)

        try:
            DLog.request("GET", file_url)
            start = time.time()
            r = self.session.get(file_url, timeout=30)
            elapsed = (time.time() - start) * 1000
            r.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(r.content)
            DLog.file("WRITE", filepath, os.path.getsize(filepath))
            DLog.request("GET", file_url, status=r.status_code, elapsed=elapsed)
            return (i, True)
        except Exception as e:
            DLog.error(f"konachan download failed: {file_url}", e)
            if os.path.exists(filepath):
                os.remove(filepath)
            return (i, False)

    def search_and_download(self, query: str, count: int, output_dir: str):
        cprint(f"\n  [konachan] Searching for '{query}'...", THEME["header"])
        posts = self.search(query, limit=count)
        if not posts:
            cprint("  [!] No results found", THEME["error"])
            return

        posts = posts[:count]
        all_tags = set()
        for p in posts:
            for t in p.get("tags", "").split():
                if t:
                    all_tags.add(t)

        if cfg.is_blacklisted(tags=list(all_tags)):
            cprint("  [!] Results match blacklisted tags", THEME["warning"])
            return

        cprint(f"  Found {len(posts)} posts, downloading...", THEME["success"])

        site_dir = os.path.join(output_dir, f"konachan_{query.replace(' ', '_')}")
        os.makedirs(site_dir, exist_ok=True)

        tasks = [(i, p, site_dir) for i, p in enumerate(posts)]
        success = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_one, t): t for t in tasks}
            for future in as_completed(futures):
                _, ok = future.result()
                if ok:
                    success += 1

        cprint(f"  -> {success}/{len(posts)} images downloaded", THEME["success"])

        for p in posts:
            cfg.add_history({
                "id": str(p.get("id", "")),
                "site": "konachan",
                "title": f"konachan #{p.get('id', '?')}",
                "tags": p.get("tags", "").split(),
                "path": site_dir,
                "type": "image",
            })


# ============================================================
# HITOMI DOWNLOADER
# ============================================================

class HitomiDownloader:
    BASE_URL = "https://hitomi.la"

    def __init__(self):
        self.session = create_session()
        self.max_workers = cfg.config.get("max_workers", 5)
        self.rate_limit = cfg.config.get("rate_limit", 0.5)

    def search(self, query: str) -> list[dict]:
        DLog.info(f"hitomi search: query={query}")
        try:
            start = time.time()
            r = self.session.get(
                f"{self.BASE_URL}/search",
                params={"q": query},
                timeout=15
            )
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", f"{self.BASE_URL}/search", status=r.status_code, elapsed=elapsed)
            r.raise_for_status()

            results = []
            if BeautifulSoup:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.select("a"):
                    href = a.get("href", "")
                    if "/galleries/" in href and href != "#":
                        title = a.get_text(strip=True)
                        gid_match = re.search(r'/galleries/(\d+)', href)
                        if gid_match and title and len(title) > 1:
                            full_url = urljoin(self.BASE_URL, href)
                            results.append({
                                "id": gid_match.group(1),
                                "title": title,
                                "url": full_url,
                            })

            if not results:
                DLog.info("hitomi: no results from HTML, trying embedded data...")
                script_match = re.search(r'var\s+g\s*=\s*(\[.*?\]);', r.text)
                if script_match:
                    try:
                        gallery_data = json.loads(script_match.group(1))
                        for item in gallery_data[:20]:
                            if isinstance(item, dict):
                                results.append({
                                    "id": str(item.get("id", "")),
                                    "title": item.get("title", ""),
                                    "url": f"{self.BASE_URL}/galleries/{item.get('id', '')}.html",
                                })
                    except json.JSONDecodeError:
                        pass

            DLog.info(f"hitomi found {len(results)} results")
            if not results:
                cprint("  [!] hitomi.la uses JavaScript rendering. Results may be limited.", THEME["warning"])
            return results[:20]
        except Exception as e:
            DLog.error("hitomi search failed", e)
            return []

    def get_image_urls(self, gallery_id: str) -> list[str]:
        DLog.info(f"hitomi get_images: id={gallery_id}")
        try:
            url = f"{self.BASE_URL}/galleries/{gallery_id}.html"
            DLog.request("GET", url)
            start = time.time()
            r = self.session.get(url, timeout=15)
            elapsed = (time.time() - start) * 1000
            DLog.request("GET", url, status=r.status_code, elapsed=elapsed)
            r.raise_for_status()

            urls = []
            if BeautifulSoup:
                soup = BeautifulSoup(r.text, "html.parser")
                for img in soup.select("img"):
                    src = img.get("src", "") or img.get("data-src", "")
                    if not src:
                        continue
                    if any(x in src for x in ["//tn.hitomi.la/smalltn", "//bigimage"]):
                        if src.startswith("//"):
                            src = "https:" + src
                        elif not src.startswith("http"):
                            src = urljoin(self.BASE_URL, src)
                        urls.append(src)

                if not urls:
                    for a in soup.select("a[href*='//bigimage']"):
                        href = a.get("href", "")
                        if href.startswith("//"):
                            href = "https:" + href
                        urls.append(href)

            DLog.info(f"hitomi found {len(urls)} images")
            return urls
        except Exception as e:
            DLog.error(f"hitomi get_images failed for {gallery_id}", e)
            return []

    def _download_one(self, args: tuple) -> tuple[int, bool]:
        i, url, output_dir = args
        ext = url.split(".")[-1].split("?")[0]
        filepath = os.path.join(output_dir, f"{i + 1:03d}.{ext}")

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return (i, True)

        try:
            DLog.request("GET", url)
            start = time.time()
            r = self.session.get(url, timeout=30)
            elapsed = (time.time() - start) * 1000
            r.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(r.content)
            DLog.file("WRITE", filepath, os.path.getsize(filepath))
            return (i, True)
        except Exception as e:
            DLog.error(f"hitomi download failed: {url}", e)
            if os.path.exists(filepath):
                os.remove(filepath)
            return (i, False)

    def search_and_download(self, query: str, count: int, output_dir: str):
        cprint(f"\n  [hitomi] Searching for '{query}'...", THEME["header"])
        results = self.search(query)
        if not results:
            cprint("  [!] No results found", THEME["error"])
            return

        cprint(f"  Found {len(results)} galleries:", THEME["success"])
        for i, item in enumerate(results[:count]):
            cprint(f"    {i + 1}. {item['title'][:60]}", THEME["text"])

        downloaded = 0
        for item in results[:count]:
            if downloaded >= count:
                break
            time.sleep(self.rate_limit)
            gallery_id = item["id"]
            title = re.sub(r'[\\/:*?"<>|]', '_', item["title"])[:80]
            images = self.get_image_urls(gallery_id)

            if not images:
                cprint(f"  [!] No images for {gallery_id}", THEME["warning"])
                continue

            gallery_dir = os.path.join(output_dir, f"hitomi_{gallery_id}_{title}")
            os.makedirs(gallery_dir, exist_ok=True)

            cprint(f"  [{gallery_id}] {title} ({len(images)} pages)", THEME["accent"])
            tasks = [(i, url, gallery_dir) for i, url in enumerate(images)]
            success = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._download_one, t): t for t in tasks}
                for future in as_completed(futures):
                    _, ok = future.result()
                    if ok:
                        success += 1

            cprint(f"    -> {success}/{len(images)} pages", THEME["success"])
            if success > 0:
                downloaded += 1
                cfg.add_history({
                    "id": gallery_id,
                    "site": "hitomi",
                    "title": item["title"],
                    "path": gallery_dir,
                    "type": "manga",
                    "pages": len(images),
                })

        cprint(f"\n  [hitomi] Downloaded {downloaded} galleries", THEME["success"])


# ============================================================
# CLI COMMANDS
# ============================================================

def cmd_search():
    show_banner()
    query = input_prompt("Search query")
    if not query:
        cprint("  [!] Query required", THEME["error"])
        return

    count_str = input_prompt("How many to download", "5")
    try:
        count = max(1, min(100, int(count_str)))
    except ValueError:
        count = 5

    output_dir = input_prompt("Download directory", cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR))
    os.makedirs(output_dir, exist_ok=True)

    sort = input_prompt("Sort by (none/recent/popular-today/popular/popular-week/popular-month)", "none")
    if sort == "none":
        sort = ""

    selected = select_sites()
    start = time.time()

    for site_key in selected:
        site = SITES[site_key]
        _download_from_site(site["name"], query, count, output_dir, sort)

    elapsed = time.time() - start
    print()
    cprint("=" * 50, THEME["header"])
    cprint(f"  Done! Took {elapsed:.1f}s", THEME["success"])
    cprint(f"  Saved to: {output_dir}", THEME["success"])
    cprint("=" * 50, THEME["header"])
    send_notification("gooningCLI", f"Download complete! {elapsed:.1f}s")


def cmd_random():
    show_banner()
    cprint("  Fetching random gallery from nhentai...", THEME["header"])
    dl = NHentaiDownloader()
    output_dir = input_prompt("Download directory", cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR))
    os.makedirs(output_dir, exist_ok=True)
    try:
        gallery = dl.get_random()
        if gallery:
            gid = gallery.get("id")
            if gid:
                dl.download_gallery(gid, output_dir)
            else:
                cprint("  [!] Random gallery has no ID", THEME["error"])
        else:
            cprint("  [!] Failed to get random gallery", THEME["error"])
    except Exception as e:
        cprint(f"  [!] Error: {e}", THEME["error"])


def cmd_info():
    show_banner()
    site_id = input_prompt("Site (nhentai)")
    gallery_id_str = input_prompt("Gallery/Video ID")
    if not gallery_id_str:
        cprint("  [!] ID required", THEME["error"])
        return

    if site_id in ("nhentai", "1", ""):
        try:
            dl = NHentaiDownloader()
            dl.show_info(int(gallery_id_str))
        except ValueError:
            cprint("  [!] Invalid ID", THEME["error"])
    else:
        cprint("  [!] Info only available for nhentai", THEME["warning"])


def cmd_history():
    show_banner()
    downloads = cfg.history.get("downloads", [])
    if not downloads:
        cprint("  No download history.", THEME["text"])
        return

    cprint(f"\n  Download History ({len(downloads)} items):", THEME["header"])
    print(f"  {'#':<5} {'Site':<12} {'Title':<40} {'Date':<20}")
    print("  " + "-" * 77)
    for i, entry in enumerate(downloads[-50:]):
        title = entry.get("title", "?")[:38]
        site = entry.get("site", "?")[:10]
        date = entry.get("date", "?")[:16]
        print(f"  {i + 1:<5} {site:<12} {title:<40} {date:<20}")
    print()


def cmd_stats():
    show_banner()
    downloads = cfg.history.get("downloads", [])
    if not downloads:
        cprint("  No data yet.", THEME["text"])
        return

    sites = {}
    types = {}
    total_size = 0
    all_tags = {}

    for entry in downloads:
        site = entry.get("site", "unknown")
        sites[site] = sites.get(site, 0) + 1
        t = entry.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
        total_size += entry.get("size", 0)
        for tag in entry.get("tags", []):
            all_tags[tag] = all_tags.get(tag, 0) + 1

    print()
    cprint("  === Statistics ===", THEME["header"])
    cprint(f"  Total downloads: {len(downloads)}", THEME["text"])
    cprint(f"  Total size: {total_size / (1024 * 1024):.1f} MB", THEME["text"])

    cprint("\n  By site:", THEME["accent"])
    for site, count in sorted(sites.items(), key=lambda x: -x[1]):
        cprint(f"    {site:<15} {count}", THEME["text"])

    cprint("\n  By type:", THEME["accent"])
    for t, count in sorted(types.items(), key=lambda x: -x[1]):
        cprint(f"    {t:<15} {count}", THEME["text"])

    if all_tags:
        cprint("\n  Top tags:", THEME["accent"])
        for tag, count in sorted(all_tags.items(), key=lambda x: -x[1])[:15]:
            cprint(f"    {tag:<20} {count}", THEME["text"])
    print()


def cmd_bookmarks():
    show_banner()
    bookmarks = cfg.bookmarks.get("bookmarks", [])
    if not bookmarks:
        cprint("  No bookmarks yet.", THEME["text"])
        cprint("  Use 'bookmark add <id> <site> <title>' to add.", THEME["text"])
        return

    cprint(f"\n  Bookmarks ({len(bookmarks)}):", THEME["header"])
    for i, bm in enumerate(bookmarks):
        cprint(f"    [{i}] {bm.get('site', '?')} - {bm.get('title', '?')[:50]} ({bm.get('date_added', '?')[:10]})", THEME["text"])
    print()


def cmd_bookmark_add():
    show_banner()
    site = input_prompt("Site (nhentai/hanime)")
    gid = input_prompt("Gallery/Video ID")
    title = input_prompt("Title (optional)")
    note = input_prompt("Note (optional)")

    if not site or not gid:
        cprint("  [!] Site and ID required", THEME["error"])
        return

    cfg.add_bookmark({"id": gid, "site": site, "title": title, "note": note})
    cprint(f"  [+] Bookmarked {gid}", THEME["success"])


def cmd_bookmark_remove():
    show_banner()
    bookmarks = cfg.bookmarks.get("bookmarks", [])
    if not bookmarks:
        cprint("  No bookmarks.", THEME["text"])
        return

    for i, bm in enumerate(bookmarks):
        cprint(f"    [{i}] {bm.get('site', '?')} - {bm.get('title', '?')[:50]}", THEME["text"])

    idx_str = input_prompt("Index to remove")
    try:
        idx = int(idx_str)
        if cfg.remove_bookmark(idx):
            cprint("  [+] Removed!", THEME["success"])
        else:
            cprint("  [!] Invalid index", THEME["error"])
    except ValueError:
        cprint("  [!] Invalid number", THEME["error"])


def cmd_blacklist():
    show_banner()
    bl = cfg.blacklist
    cprint(f"\n  Blacklisted tags: {', '.join(bl.get('tags', [])) or '(none)'}", THEME["text"])
    cprint(f"  Blacklisted IDs:  {', '.join(bl.get('ids', [])) or '(none)'}", THEME["text"])
    print()
    cprint("  Commands:", THEME["accent"])
    cprint("    tag <name>    - Blacklist a tag", THEME["text"])
    cprint("    id <id>       - Blacklist an ID", THEME["text"])
    cprint("    remove tag <name> - Remove tag", THEME["text"])
    cprint("    remove id <id>    - Remove ID", THEME["text"])
    print()


def cmd_blacklist_manage(args: list[str]):
    if len(args) < 2:
        cmd_blacklist()
        return

    action = args[0]
    target = args[1]

    if action == "tag":
        if target not in cfg.blacklist["tags"]:
            cfg.blacklist["tags"].append(target)
            cfg.save_blacklist()
            cprint(f"  [+] Blacklisted tag: {target}", THEME["success"])
        else:
            cprint(f"  [~] Already blacklisted", THEME["warning"])
    elif action == "id":
        if target not in cfg.blacklist["ids"]:
            cfg.blacklist["ids"].append(target)
            cfg.save_blacklist()
            cprint(f"  [+] Blacklisted ID: {target}", THEME["success"])
        else:
            cprint(f"  [~] Already blacklisted", THEME["warning"])
    elif action == "remove":
        if len(args) >= 3 and args[1] == "tag":
            if args[2] in cfg.blacklist["tags"]:
                cfg.blacklist["tags"].remove(args[2])
                cfg.save_blacklist()
                cprint(f"  [+] Removed tag: {args[2]}", THEME["success"])
        elif len(args) >= 3 and args[1] == "id":
            if args[2] in cfg.blacklist["ids"]:
                cfg.blacklist["ids"].remove(args[2])
                cfg.save_blacklist()
                cprint(f"  [+] Removed ID: {args[2]}", THEME["success"])


def cmd_dedup():
    show_banner()
    cprint("  Scanning for duplicates...", THEME["header"])

    download_dir = cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR)
    if not os.path.exists(download_dir):
        cprint("  [!] Download directory not found", THEME["error"])
        return

    hashes: dict[str, list[str]] = {}
    for root, _, files in os.walk(download_dir):
        for f in files:
            filepath = os.path.join(root, f)
            try:
                h = file_hash(filepath)
                hashes.setdefault(h, []).append(filepath)
            except Exception:
                continue

    dupes = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    if not dupes:
        cprint("  No duplicates found!", THEME["success"])
        return

    total_dupes = sum(len(paths) - 1 for paths in dupes.values())
    cprint(f"  Found {len(dupes)} duplicate groups ({total_dupes} extra files):", THEME["warning"])

    for h, paths in dupes.items():
        size = os.path.getsize(paths[0]) if os.path.exists(paths[0]) else 0
        cprint(f"\n    Hash: {h[:8]}... ({size} bytes)", THEME["text"])
        for p in paths:
            cprint(f"      {p}", THEME["text"])

    confirm = input_prompt("\n  Remove duplicates? (y/n)", "n")
    if confirm.lower() == "y":
        removed = 0
        for h, paths in dupes.items():
            for p in paths[1:]:
                try:
                    os.remove(p)
                    removed += 1
                except Exception:
                    pass
        cprint(f"  [+] Removed {removed} duplicate files", THEME["success"])
    else:
        cprint("  Cancelled.", THEME["text"])


def cmd_organize():
    show_banner()
    cprint("  Organize downloads by:", THEME["header"])
    cprint("    1. Site", THEME["text"])
    cprint("    2. Date", THEME["text"])
    cprint("    3. Type (manga/video)", THEME["text"])

    choice = input_prompt("Choice", "1")
    download_dir = cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR)

    if not os.path.exists(download_dir):
        cprint("  [!] Download directory not found", THEME["error"])
        return

    moved = 0
    for entry in os.listdir(download_dir):
        full = os.path.join(download_dir, entry)
        if not os.path.isdir(full):
            continue

        if choice == "1":
            site = entry.split("_")[0] if "_" in entry else "other"
            dest = os.path.join(download_dir, site, entry)
        elif choice == "2":
            try:
                mtime = os.path.getmtime(full)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m")
            except Exception:
                date_str = "unknown"
            dest = os.path.join(download_dir, date_str, entry)
        elif choice == "3":
            vtype = "video" if any(x in entry.lower() for x in ["hanime", "hentaihaven"]) else "manga"
            dest = os.path.join(download_dir, vtype, entry)
        else:
            return

        if dest != full:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(full, dest)
            moved += 1

    cprint(f"  [+] Organized {moved} folders", THEME["success"])


def cmd_clean():
    show_banner()
    cprint("  Clean downloads:", THEME["header"])
    cprint("    1. Remove empty folders", THEME["text"])
    cprint("    2. Remove by age (days)", THEME["text"])
    cprint("    3. Remove folders smaller than X KB", THEME["text"])

    choice = input_prompt("Choice", "1")
    download_dir = cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR)

    if not os.path.exists(download_dir):
        cprint("  [!] Download directory not found", THEME["error"])
        return

    removed = 0

    if choice == "1":
        for root, dirs, files in os.walk(download_dir, topdown=False):
            if not dirs and not files and root != download_dir:
                try:
                    os.rmdir(root)
                    removed += 1
                except Exception:
                    pass
        cprint(f"  [+] Removed {removed} empty folders", THEME["success"])

    elif choice == "2":
        days_str = input_prompt("Days old", "30")
        try:
            days = int(days_str)
        except ValueError:
            days = 30
        cutoff = time.time() - (days * 86400)
        for entry in os.listdir(download_dir):
            full = os.path.join(download_dir, entry)
            if os.path.isdir(full) and os.path.getmtime(full) < cutoff:
                shutil.rmtree(full, ignore_errors=True)
                removed += 1
        cprint(f"  [+] Removed {removed} folders older than {days} days", THEME["success"])

    elif choice == "3":
        size_str = input_prompt("Minimum size in KB", "100")
        try:
            min_size = int(size_str) * 1024
        except ValueError:
            min_size = 100 * 1024
        for entry in os.listdir(download_dir):
            full = os.path.join(download_dir, entry)
            if os.path.isdir(full):
                total = sum(
                    os.path.getsize(os.path.join(r, f))
                    for r, _, fs in os.walk(full) for f in fs
                )
                if total < min_size:
                    shutil.rmtree(full, ignore_errors=True)
                    removed += 1
        cprint(f"  [+] Removed {removed} small folders", THEME["success"])


def cmd_export():
    show_banner()
    gid = input_prompt("Gallery ID to export")
    if not gid:
        return

    dl = NHentaiDownloader()
    try:
        gallery = dl.get_gallery(int(gid))
    except ValueError:
        cprint("  [!] Invalid ID", THEME["error"])
        return
    except Exception as e:
        cprint(f"  [!] Error: {e}", THEME["error"])
        return

    if not gallery:
        cprint("  [!] Gallery not found", THEME["error"])
        return

    title = gallery.get("title", {}).get("english") or f"gallery_{gid}"
    title = re.sub(r'[\\/:*?"<>|]', '_', title)[:80]

    fmt = input_prompt("Format (json/cbz/zip)", "json")
    output_dir = cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR)
    os.makedirs(output_dir, exist_ok=True)

    if fmt == "json":
        out_path = os.path.join(output_dir, f"nhentai_{gid}_{title}.json")
        tags = [t.get("name", "") for t in gallery.get("tags", [])]
        data = {
            "id": gallery.get("id"),
            "title": gallery.get("title"),
            "tags": tags,
            "num_pages": gallery.get("num_pages"),
            "num_favorites": gallery.get("num_favorites"),
            "pages": dl.get_page_urls(gallery),
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        cprint(f"  [+] Exported: {out_path}", THEME["success"])

    elif fmt in ("cbz", "zip"):
        pages = dl.get_page_urls(gallery)
        if not pages:
            cprint("  [!] No pages", THEME["error"])
            return

        cprint(f"  Downloading {len(pages)} pages for archive...", THEME["text"])
        tmp_dir = os.path.join(output_dir, f"_tmp_{gid}")
        os.makedirs(tmp_dir, exist_ok=True)

        tasks = [(i, url, tmp_dir) for i, url in enumerate(pages)]
        with ThreadPoolExecutor(max_workers=dl.max_workers) as executor:
            list(executor.map(dl._download_one, tasks))

        ext = "cbz" if fmt == "cbz" else "zip"
        out_path = os.path.join(output_dir, f"nhentai_{gid}_{title}.{ext}")
        import zipfile
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in sorted(os.listdir(tmp_dir)):
                fpath = os.path.join(tmp_dir, fname)
                zf.write(fpath, fname)

        shutil.rmtree(tmp_dir, ignore_errors=True)
        cprint(f"  [+] Archive created: {out_path}", THEME["success"])


def cmd_batch():
    show_banner()
    filepath = input_prompt("Path to .txt file (one query per line)")
    if not filepath or not os.path.exists(filepath):
        cprint("  [!] File not found", THEME["error"])
        return

    with open(filepath, "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    count_str = input_prompt("Items per query", "3")
    try:
        count = max(1, int(count_str))
    except ValueError:
        count = 3

    output_dir = input_prompt("Download directory", cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR))
    os.makedirs(output_dir, exist_ok=True)

    selected = select_sites()
    cprint(f"\n  Processing {len(queries)} queries...", THEME["header"])

    for i, query in enumerate(queries):
        cprint(f"\n  [{i + 1}/{len(queries)}] '{query}'", THEME["accent"])
        for site_key in selected:
            site = SITES[site_key]
            _download_from_site(site["name"], query, count, output_dir)

    cprint("\n  Batch complete!", THEME["success"])


def cmd_slideshow():
    show_banner()
    download_dir = cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR)
    if not os.path.exists(download_dir):
        cprint("  [!] Download directory not found", THEME["error"])
        return

    folders = [d for d in os.listdir(download_dir)
               if os.path.isdir(os.path.join(download_dir, d))]
    if not folders:
        cprint("  [!] No downloaded galleries found", THEME["error"])
        return

    cprint("  Available galleries:", THEME["header"])
    for i, f in enumerate(folders[:20]):
        cprint(f"    [{i}] {f}", THEME["text"])

    choice = input_prompt("Gallery index to view")
    try:
        idx = int(choice)
        folder = os.path.join(download_dir, folders[idx])
    except (ValueError, IndexError):
        cprint("  [!] Invalid selection", THEME["error"])
        return

    images = sorted([f for f in os.listdir(folder)
                     if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))])
    if not images:
        cprint("  [!] No images in this gallery", THEME["error"])
        return

    cprint(f"\n  Viewing: {folders[idx]} ({len(images)} images)", THEME["accent"])
    cprint("  Press Ctrl+C to stop\n", THEME["text"])

    for img_name in images:
        img_path = os.path.join(folder, img_name)
        try:
            if is_termux():
                subprocess.run(["termux-open", img_path], timeout=5, capture_output=True)
                time.sleep(2)
            else:
                from PIL import Image
                img = Image.open(img_path)
                img.thumbnail((80, 40))
                pixels = img.load()
                chars = " .:-=+*#%@"
                for y in range(img.height):
                    line = ""
                    for x in range(img.width):
                        r, g, b = pixels[x, y][:3]
                        brightness = (r + g + b) / 3
                        idx = min(int(brightness / 255 * (len(chars) - 1)), len(chars) - 1)
                        line += chars[idx]
                    print(line)
                print()
                time.sleep(0.5)
        except KeyboardInterrupt:
            break
        except ImportError:
            cprint(f"  [i] {img_path}", THEME["text"])
        except Exception:
            cprint(f"  [!] Cannot display {img_name}", THEME["error"])


def cmd_wallpaper():
    show_banner()
    download_dir = cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR)
    if not os.path.exists(download_dir):
        cprint("  [!] Download directory not found", THEME["error"])
        return

    folders = [d for d in os.listdir(download_dir)
               if os.path.isdir(os.path.join(download_dir, d))]
    if not folders:
        cprint("  [!] No galleries found", THEME["error"])
        return

    cprint("  Available galleries:", THEME["header"])
    for i, f in enumerate(folders[:20]):
        cprint(f"    [{i}] {f}", THEME["text"])

    choice = input_prompt("Gallery index")
    try:
        idx = int(choice)
        folder = os.path.join(download_dir, folders[idx])
    except (ValueError, IndexError):
        cprint("  [!] Invalid selection", THEME["error"])
        return

    images = sorted([f for f in os.listdir(folder)
                     if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    if not images:
        cprint("  [!] No compatible images", THEME["error"])
        return

    img_path = os.path.join(folder, images[0])
    set_wallpaper(img_path)


def cmd_config():
    show_banner()
    cprint("  Configuration:", THEME["header"])
    for key, val in cfg.config.items():
        cprint(f"    {key:<20} = {val}", THEME["text"])
    print()
    cprint("  Use 'config set <key> <value>' to change.", THEME["text"])


def cmd_config_set(args: list[str]):
    global THEME
    if len(args) < 2:
        cmd_config()
        return

    key, value = args[0], " ".join(args[1:])
    if key in cfg.config:
        if key == "theme":
            if value not in THEMES:
                cprint(f"  [!] Unknown theme: {value}", THEME["error"])
                cprint(f"  Available: {', '.join(THEMES.keys())}", THEME["text"])
                return
        old_type = type(cfg.config[key])
        try:
            if old_type == bool:
                cfg.config[key] = value.lower() in ("true", "1", "yes")
            elif old_type == int:
                cfg.config[key] = int(value)
            elif old_type == float:
                cfg.config[key] = float(value)
            else:
                cfg.config[key] = value
        except (ValueError, TypeError):
            cprint(f"  [!] Invalid value for {key}", THEME["error"])
            return
        cfg.save_config()
        cprint(f"  [+] {key} = {cfg.config[key]}", THEME["success"])

        if key == "theme":
            THEME = THEMES.get(value, THEMES["default"])
    else:
        cprint(f"  [!] Unknown key: {key}", THEME["error"])


def cmd_theme():
    global THEME
    show_banner()
    cprint("  Available themes:", THEME["header"])
    for name in THEMES:
        marker = " *" if name == cfg.config.get("theme") else ""
        cprint(f"    {name}{marker}", THEME["text"])

    name = input_prompt("\n  Theme name")
    if name in THEMES:
        cfg.config["theme"] = name
        cfg.save_config()
        THEME = THEMES[name]
        cprint(f"  [+] Theme set to '{name}'", THEME["success"])
    else:
        cprint("  [!] Unknown theme", THEME["error"])


def cmd_proxy():
    show_banner()
    current = cfg.config.get("proxy", "")
    cprint(f"  Current proxy: {current or '(none)'}", THEME["text"])

    proxy = input_prompt("Proxy URL (empty to remove)")
    cfg.config["proxy"] = proxy
    cfg.save_config()
    if proxy:
        cprint(f"  [+] Proxy set: {proxy}", THEME["success"])
    else:
        cprint("  [+] Proxy removed", THEME["success"])


def cmd_update():
    show_banner()
    cprint("  Checking for updates...", THEME["header"])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(script_dir, ".git")):
        cprint("  [!] Not a git repository. Clone from GitHub first.", THEME["error"])
        return

    try:
        result = subprocess.run(
            ["git", "-C", script_dir, "pull"],
            capture_output=True, text=True, timeout=30
        )
        print(result.stdout)
        if result.returncode == 0:
            cprint("  [+] Updated!", THEME["success"])
        else:
            cprint(f"  [!] Error: {result.stderr}", THEME["error"])
    except FileNotFoundError:
        cprint("  [!] git not found", THEME["error"])


def cmd_shell(args: list[str]):
    if not cfg.config.get("debug", False):
        cprint("  [!] Shell requires Developer Mode to be enabled.", THEME["error"])
        cprint("  Enable it via [18] Developer Mode or --debug flag.", THEME["text"])
        return
    if not args:
        cprint("  Usage: shell <command>", THEME["text"])
        return
    cprint(f"  [!] Running: {' '.join(args)}", THEME["warning"])
    try:
        result = subprocess.run(args, capture_output=False, timeout=30)
    except FileNotFoundError:
        cprint(f"  [!] Command not found: {args[0]}", THEME["error"])
    except subprocess.TimeoutExpired:
        cprint("  [!] Command timed out", THEME["error"])


def cmd_debug_toggle():
    show_banner()
    current = cfg.config.get("debug", False)
    cprint(f"  Developer Mode: {'ON' if current else 'OFF'}", THEME["header"])

    if current:
        cprint("  Dev mode shows:", THEME["text"])
        cprint("    - Full HTTP request/response details", THEME["text"])
        cprint("    - File I/O operations with sizes", THEME["text"])
        cprint("    - Full tracebacks on errors", THEME["text"])
        cprint("    - API response summaries", THEME["text"])
        cprint("    - Download timing information", THEME["text"])
        print()

    choice = input_prompt("  Toggle dev mode? (on/off)", "on" if not current else "off")
    new_val = choice.lower() in ("on", "true", "1", "yes")
    cfg.config["debug"] = new_val
    cfg.save_config()
    cprint(f"\n  [+] Developer Mode: {'ON' if new_val else 'OFF'}", THEME["success"])

    if new_val:
        cprint("  Warning: Dev mode prints sensitive info (URLs, file paths, etc.)", THEME["warning"])
        cprint("  Use for debugging only, not in shared environments.", THEME["warning"])


def cmd_help():
    show_banner()
    cprint("  === gooningCLI Help ===\n", THEME["header"])

    commands = [
        ("search", "Search and download content"),
        ("random", "Download random gallery"),
        ("info", "Show gallery details"),
        ("history", "View download history"),
        ("stats", "Show download statistics"),
        ("bookmarks", "View bookmarks"),
        ("bookmark add", "Add a bookmark"),
        ("bookmark remove", "Remove a bookmark"),
        ("blacklist", "View/manage blacklist"),
        ("blacklist tag <tag>", "Blacklist a tag"),
        ("blacklist id <id>", "Blacklist an ID"),
        ("dedup", "Find and remove duplicates"),
        ("organize", "Organize download folders"),
        ("clean", "Clean old/empty/small downloads"),
        ("export", "Export gallery as JSON/CBZ/ZIP"),
        ("batch", "Download from text file"),
        ("slideshow", "View downloaded images"),
        ("wallpaper", "Set image as wallpaper (Termux)"),
        ("config", "View configuration"),
        ("config set", "Change a config value"),
        ("theme", "Change CLI theme"),
        ("proxy", "Set proxy"),
        ("devmode", "Toggle developer mode (verbose logging)"),
        ("update", "Update via git pull"),
        ("shell *", "Run shell command (dev mode only)"),
        ("help", "Show this help"),
    ]

    for cmd, desc in commands:
        cprint(f"    {cmd:<20} {desc}", THEME["text"])
    print()
    cprint("    * shell requires Developer Mode enabled", THEME["warning"])
    print()

    cprint("  Supported sites:", THEME["accent"])
    cprint("    nhentai.net          Manga/Doujinshi (API)", THEME["text"])
    cprint("    hanime.tv            Videos", THEME["text"])
    cprint("    hentaihaven.xxx      Videos (yt-dlp)", THEME["text"])
    cprint("    rule34.xxx           Image board (API)", THEME["text"])
    cprint("    gelbooru.com         Image board (API)", THEME["text"])
    cprint("    hitomi.la            Manga/Doujinshi", THEME["text"])
    cprint("    danbooru.donmai.us   Image board (no auth)", THEME["text"])
    cprint("    konachan.com         Image board (no auth)", THEME["text"])
    print()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def select_sites() -> list[str]:
    print(f"\n{THEME['header']}Available sites:{Style.RESET_ALL}")
    for key, site in SITES.items():
        print(f"  {THEME['warning']}{key}{Style.RESET_ALL} - {site['desc']}")

    choice = input_prompt("\nSelect site (number)", "11")
    if choice == "11":
        return [k for k in SITES if SITES[k]["type"] != "all"]
    if choice in SITES:
        return [choice]
    cprint("  [!] Invalid, using all sites", THEME["warning"])
    return [k for k in SITES if SITES[k]["type"] != "all"]


def _download_from_site(name: str, query: str, count: int, output_dir: str, sort: str = ""):
    DLog.info(f"_download_from_site: site={name}, query={query}, count={count}")
    try:
        if name == "nhentai":
            NHentaiDownloader().search_and_download(query, count, output_dir, sort)
        elif name == "hanime":
            HanimeDownloader().search_and_download(query, count, output_dir)
        elif name == "hentaihaven":
            HentaiHavenDownloader().search_and_download(query, count, output_dir)
        elif name == "rule34":
            Rule34Downloader().search_and_download(query, count, output_dir)
        elif name == "gelbooru":
            GelbooruDownloader().search_and_download(query, count, output_dir)
        elif name == "danbooru":
            DanbooruDownloader().search_and_download(query, count, output_dir)
        elif name == "konachan":
            KonachanDownloader().search_and_download(query, count, output_dir)
        elif name == "hitomi":
            HitomiDownloader().search_and_download(query, count, output_dir)
        elif name == "nhentai-lolicon":
            NHentaiTagDownloader("lolicon", "lolicon").search_and_download(query, count, output_dir, sort)
        elif name == "nhentai-incest":
            NHentaiTagDownloader("incest", "incest").search_and_download(query, count, output_dir, sort)
        else:
            cprint(f"  [!] Unknown site: {name}", THEME["error"])
    except Exception as e:
        DLog.error(f"Error on site {name}", e)
        cprint(f"  [!] Error on {name}: {e}", THEME["error"])


def _zip_folder(folder_path: str):
    zip_path = folder_path.rstrip(os.sep) + ".zip"
    if os.path.exists(zip_path):
        return
    import zipfile
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for f in files:
                fpath = os.path.join(root, f)
                arcname = os.path.relpath(fpath, os.path.dirname(folder_path))
                zf.write(fpath, arcname)
    cprint(f"  [+] Zipped: {zip_path}", THEME["success"])


def _cbz_folder(folder_path: str):
    cbz_path = folder_path.rstrip(os.sep) + ".cbz"
    if os.path.exists(cbz_path):
        return
    import zipfile
    with zipfile.ZipFile(cbz_path, "w", zipfile.ZIP_STORED) as zf:
        for root, _, files in os.walk(folder_path):
            for f in sorted(files):
                fpath = os.path.join(root, f)
                arcname = os.path.relpath(fpath, os.path.dirname(folder_path))
                zf.write(fpath, arcname)
    cprint(f"  [+] CBZ: {cbz_path}", THEME["success"])

# ============================================================
# MAIN CLI
# ============================================================

def interactive_loop():
    show_banner()

    while True:
        try:
            debug_status = f" [DEV MODE: ON]" if cfg.config.get("debug", False) else ""
            cprint(f"  === Main Menu ==={debug_status}\n", THEME["header"])
            cprint("    [1]  Search & Download", THEME["text"])
            cprint("    [2]  Random Gallery", THEME["text"])
            cprint("    [3]  Gallery Info", THEME["text"])
            cprint("    [4]  Download History", THEME["text"])
            cprint("    [5]  Statistics", THEME["text"])
            cprint("    [6]  Bookmarks", THEME["text"])
            cprint("    [7]  Blacklist", THEME["text"])
            cprint("    [8]  Dedup", THEME["text"])
            cprint("    [9]  Organize", THEME["text"])
            cprint("    [10] Clean", THEME["text"])
            cprint("    [11] Export", THEME["text"])
            cprint("    [12] Batch Download", THEME["text"])
            cprint("    [13] Slideshow", THEME["text"])
            cprint("    [14] Wallpaper", THEME["text"])
            cprint("    [15] Config", THEME["text"])
            cprint("    [16] Theme", THEME["text"])
            cprint("    [17] Proxy", THEME["text"])
            cprint("    [18] Developer Mode", THEME["text"])
            cprint("    [19] Update", THEME["text"])
            cprint("    [20] Shell", THEME["text"])
            cprint("    [21] Help", THEME["text"])
            cprint("    [0]  Exit\n", THEME["text"])

            choice = input_prompt("Select option", "1")

            if choice == "1":
                cmd_search()
            elif choice == "2":
                cmd_random()
            elif choice == "3":
                cmd_info()
            elif choice == "4":
                cmd_history()
            elif choice == "5":
                cmd_stats()
            elif choice == "6":
                sub = input_prompt("  [list/add/remove]", "list")
                if sub == "add":
                    cmd_bookmark_add()
                elif sub == "remove":
                    cmd_bookmark_remove()
                else:
                    cmd_bookmarks()
            elif choice == "7":
                sub = input_prompt("  [list/tag/id/remove_tag/remove_id]", "list")
                if sub == "tag":
                    tag = input_prompt("Tag to blacklist")
                    cmd_blacklist_manage(["tag", tag])
                elif sub == "id":
                    gid = input_prompt("ID to blacklist")
                    cmd_blacklist_manage(["id", gid])
                elif sub == "remove_tag":
                    tag = input_prompt("Tag to remove")
                    cmd_blacklist_manage(["remove", "tag", tag])
                elif sub == "remove_id":
                    gid = input_prompt("ID to remove")
                    cmd_blacklist_manage(["remove", "id", gid])
                else:
                    cmd_blacklist()
            elif choice == "8":
                cmd_dedup()
            elif choice == "9":
                cmd_organize()
            elif choice == "10":
                cmd_clean()
            elif choice == "11":
                cmd_export()
            elif choice == "12":
                cmd_batch()
            elif choice == "13":
                cmd_slideshow()
            elif choice == "14":
                cmd_wallpaper()
            elif choice == "15":
                sub = input_prompt("  [view/set]", "view")
                if sub == "set":
                    key = input_prompt("Key")
                    val = input_prompt("Value")
                    cmd_config_set([key, val])
                else:
                    cmd_config()
            elif choice == "16":
                cmd_theme()
            elif choice == "17":
                cmd_proxy()
            elif choice == "18":
                cmd_debug_toggle()
            elif choice == "19":
                cmd_update()
            elif choice == "20":
                cmdstr = input_prompt("Shell command")
                if cmdstr:
                    cmd_shell(cmdstr.split())
            elif choice == "21":
                cmd_help()
            elif choice == "0":
                cprint("\n  Goodbye!", THEME["accent"])
                break
            else:
                cprint("  [!] Invalid option", THEME["error"])
                time.sleep(1)

        except KeyboardInterrupt:
            print()
            cprint("\n  Goodbye!", THEME["accent"])
            break


def cli_main():
    import argparse
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{VERSION} - Multi-site hentai downloader")
    parser.add_argument("command", nargs="?", default=None,
                       help="Command to run (search, random, info, history, stats, etc.)")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--site", "-s", default="all", help="Site to use")
    parser.add_argument("--count", "-n", type=int, default=5, help="Number of items")
    parser.add_argument("--dir", "-d", default=None, help="Download directory")
    parser.add_argument("--sort", default="", help="Sort order")
    parser.add_argument("--version", "-v", action="store_true", help="Show version")
    parser.add_argument("--debug", action="store_true", help="Enable developer mode (verbose logging)")

    parsed = parser.parse_args()

    if parsed.version:
        print(f"{APP_NAME} v{VERSION}")
        return

    if parsed.debug:
        cfg.config["debug"] = True
        cfg.save_config()
        DLog.log("Developer mode enabled via CLI flag")

    if not parsed.command:
        interactive_loop()
        return

    show_banner()
    output_dir = parsed.dir or cfg.config.get("download_dir", DEFAULT_DOWNLOAD_DIR)
    os.makedirs(output_dir, exist_ok=True)

    cmd = parsed.command.lower()

    if cmd == "search":
        query = parsed.args[0] if parsed.args else input_prompt("Search query")
        if query:
            sites = [parsed.site] if parsed.site != "all" else [k for k in SITES if SITES[k]["type"] != "all"]
            for site_key in sites:
                if site_key in SITES:
                    _download_from_site(SITES[site_key]["name"], query, parsed.count, output_dir, parsed.sort)
    elif cmd == "random":
        dl = NHentaiDownloader()
        gallery = dl.get_random()
        if gallery:
            dl.download_gallery(gallery["id"], output_dir)
    elif cmd == "info":
        gid = parsed.args[0] if parsed.args else input_prompt("Gallery ID")
        if gid:
            NHentaiDownloader().show_info(int(gid))
    elif cmd == "history":
        cmd_history()
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "bookmarks":
        cmd_bookmarks()
    elif cmd == "dedup":
        cmd_dedup()
    elif cmd == "organize":
        cmd_organize()
    elif cmd == "clean":
        cmd_clean()
    elif cmd == "export":
        cmd_export()
    elif cmd == "batch":
        cmd_batch()
    elif cmd == "config":
        cmd_config()
    elif cmd == "theme":
        cmd_theme()
    elif cmd == "proxy":
        cmd_proxy()
    elif cmd == "update":
        cmd_update()
    elif cmd == "help":
        cmd_help()
    else:
        cprint(f"  [!] Unknown command: {cmd}", THEME["error"])
        cprint("  Run with no args for interactive mode, or 'help' for commands.", THEME["text"])


if __name__ == "__main__":
    try:
        cli_main()
    except KeyboardInterrupt:
        print()
        cprint("  Goodbye!", THEME["accent"])
    except Exception as e:
        if cfg.config.get("debug", False):
            cprint("\n  [FATAL ERROR]", THEME["error"])
            traceback.print_exc()
        else:
            cprint(f"\n  [!] Fatal error: {e}", THEME["error"])
            cprint("  Run with --debug for full traceback.", THEME["warning"])
        sys.exit(1)
