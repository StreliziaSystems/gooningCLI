# gooningCLI

```
 ██████╗  ██████╗  ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗  ██████╗██╗     ██╗
██╔════╝ ██╔═══██╗██╔═══██╗████╗  ██║██║████╗  ██║██╔════╝ ██╔════╝██║     ██║
██║  ███╗██║   ██║██║   ██║██╔██╗ ██║██║██╔██╗ ██║██║  ███╗██║     ██║     ██║
██║   ██║██║   ██║██║   ██║██║╚██╗██║██║██║╚██╗██║██║   ██║██║     ██║     ██║
╚██████╔╝╚██████╔╝╚██████╔╝██║ ╚████║██║██║ ╚████║╚██████╔╝╚██████╗███████╗██║
 ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚══════╝╚═╝
```

**v3.1.0** | made by **or4acle**

> *For educational purposes only.*

A multi-site hentai content downloader CLI built for Termux. Download manga, doujinshi, images, and videos from multiple sites with a single tool.

---

## Disclaimer & Liability Notice

This project, **gooningCLI**, was created strictly for **educational and learning purposes** by its developer. It serves as a practical exercise in Python programming, API integration, and web scraping.

**StreliziaSystems** and its owner, **or4acle**, are NOT responsible for any media, data, or material downloaded, accessed, or stored using this software. The tool merely acts as an automated client; what you choose to search for and download is entirely your own responsibility as the end-user.

While we have put genuine effort into implementing **Safety Filters** (Blocklists) to prevent the fetching of sensitive, illegal, or disturbing content, no system is completely bulletproof. We acknowledge that loopholes and bypasses can be discovered and abused by malicious users. We strongly condemn the download of prohibited materials, but as this is an open-source tool executed locally on your machine, we cannot monitor, control, or be held liable for how it is ultimately used.

**By using this software, you agree to take full responsibility for your actions.**

---

## Supported Sites

| Site | Type | Method | Auth Required |
|------|------|--------|---------------|
| nhentai.net | Manga/Doujinshi | API v2 | No |
| hanime.tv | Videos | Scraping | No |
| hentaihaven.xxx | Videos | yt-dlp | No |
| rule34.xxx | Images | API (posts.json) | Yes (API key) |
| gelbooru.com | Images | API (JSON) | Yes (API key) |
| hitomi.la | Manga/Doujinshi | HTML scraping | No |
| **danbooru.donmai.us** | **Images** | **API (JSON)** | **No** |
| **konachan.com** | **Images** | **API (JSON)** | **No** |
| nhentai (tags) | Manga | API v2 (specific tags) | No |

---

## Features

### Core
- **Multi-site support** - 8 sites + tag-specific nhentai queries
- **Concurrent downloads** - ThreadPoolExecutor for fast parallel image downloading
- **Resilient networking** - Exponential backoff, retry on failure, rate limiting
- **File validation** - Checks file size against Content-Length, retries incomplete downloads
- **Smart server rotation** - Distributes requests across multiple image servers

### Content Management
- **Download history** - Track everything you've downloaded
- **Bookmarks** - Save content to download later
- **Blacklist** - Filter out unwanted tags or specific gallery IDs
- **Statistics** - View your download stats, top tags, storage usage
- **Deduplication** - Find and remove duplicate files by hash
- **Organize** - Sort download folders by site, date, or type
- **Clean** - Remove empty folders, old downloads, or small files

### Export & Viewing
- **Export** - Export galleries as JSON metadata, CBZ (comic archive), or ZIP
- **Batch mode** - Download from a text file with multiple search terms
- **Slideshow** - View downloaded images in terminal (ASCII art) or open them
- **Wallpaper** - Set downloaded images as Android wallpaper via Termux API

### Configuration
- **Themes** - 6 built-in color themes (default, fire, ocean, matrix, mono, pink)
- **Proxy support** - SOCKS5/HTTP proxy configuration
- **Notifications** - Android notifications when downloads complete
- **CLI arguments** - Use interactively or script with command-line args

### Developer Mode
- **Verbose logging** - Full HTTP request/response details with timing
- **Error tracebacks** - Complete stack traces on failures
- **File I/O logging** - See every file write with sizes
- **API debugging** - Response summaries and search parameters
- **Enable via** menu option [18] or `--debug` CLI flag

---

## Installation (Termux)

```bash
# Clone the repo
git clone https://github.com/StreliziaSystems/gooningCLI.git
cd gooningCLI

# Run setup
bash setup.sh

# Or install manually
pip install requests tqdm colorama beautifulsoup4
pip install yt-dlp  # Optional: for hentaihaven video downloads
pkg install termux-api  # Optional: for notifications & wallpaper
```

---

## Usage

### Interactive Mode

```bash
python gooningcli.py
```

Opens a menu with all commands. Just enter the number.

### Command Line Mode

```bash
# Search and download
python gooningcli.py search "futa" -n 10 -s nhentai

# Download random gallery
python gooningcli.py random

# View gallery info
python gooningcli.py info 12345

# Developer mode
python gooningcli.py --debug search "futa" -n 5

# View history/stats
python gooningcli.py history
python gooningcli.py stats
```

### Available Commands

| Command | Description |
|---------|-------------|
| `search` | Search and download content |
| `random` | Download a random gallery |
| `info` | Show gallery details |
| `history` | View download history |
| `stats` | Show download statistics |
| `bookmarks` | View bookmarks |
| `bookmark add` | Add a bookmark |
| `bookmark remove` | Remove a bookmark |
| `blacklist` | View/manage blacklist |
| `blacklist tag <tag>` | Blacklist a tag |
| `blacklist id <id>` | Blacklist a gallery ID |
| `dedup` | Find and remove duplicates |
| `organize` | Organize folders by site/date/type |
| `clean` | Clean old/empty/small downloads |
| `export` | Export as JSON/CBZ/ZIP |
| `batch` | Download from a text file |
| `slideshow` | View downloaded images |
| `wallpaper` | Set image as wallpaper (Termux) |
| `config` | View/set configuration |
| `theme` | Change color theme |
| `proxy` | Set proxy URL |
| `devmode` | Toggle developer mode |
| `update` | Update via git pull |
| `shell` | Run shell command |
| `help` | Show help |

---

## Configuration

Config is stored in `~/.gooningcli/config.json`:

```json
{
  "theme": "default",
  "download_dir": "~/gooningcli_downloads",
  "max_workers": 5,
  "proxy": "",
  "rate_limit": 0.5,
  "auto_zip": false,
  "auto_cbz": false,
  "notify": true,
  "debug": false
}
```

### Options

| Key | Default | Description |
|-----|---------|-------------|
| `theme` | `default` | Color theme (default/fire/ocean/matrix/mono/pink) |
| `download_dir` | `~/gooningcli_downloads` | Where to save downloads |
| `max_workers` | `5` | Concurrent download threads |
| `proxy` | `""` | HTTP/SOCKS5 proxy URL |
| `rate_limit` | `0.5` | Delay between requests (seconds) |
| `default_site` | `all` | Default site for search (nhentai/gelbooru/danbooru/konachan/all) |
| `nhentai_mirrors` | `["nhentai.net"]` | nhentai mirrors to try in order |
| `auto_zip` | `false` | Auto-zip manga galleries after download |
| `auto_cbz` | `false` | Auto-create CBZ archives after download |
| `notify` | `true` | Android notifications (Termux only) |
| `debug` | `false` | Developer mode (verbose logging) |

---

## Developer Mode

Enable dev mode to get detailed debugging output:

```bash
# Via CLI flag
python gooningcli.py --debug search "futa" -n 5

# Via menu
# Option [18] -> Toggle on/off

# What it shows:
#   [HTTP] GET https://nhentai.net/api/v2/search?query=futa -> 200 (145ms)
#   [FILE] WRITE: /path/to/001.jpg (52847 bytes)
#   [ERROR] HTTP 429 on search (attempt 2/3, 4000ms)
#     Traceback (most recent call last):
#       File "gooningcli.py", line 318, in retry_with_backoff
#         ...
```

---

## Batch Mode

Create a text file with one search term per line:

```txt
# my_downloads.txt
# Lines starting with # are ignored
futa
big boobs
sole female
ahegao
```

Then run:

```bash
python gooningcli.py batch
```

---

## File Structure

```
gooningCLI/
  gooningcli.py      # Main script
  requirements.txt   # Python dependencies
  setup.sh          # Termux setup script
  README.md         # This file
```

### Data Files (auto-created)

```
~/.gooningcli/
  config.json       # Configuration
  history.json      # Download history
  bookmarks.json    # Saved bookmarks
  blacklist.json    # Blacklisted tags/IDs
```

---

## Requirements

- Python 3.8+
- Termux (recommended) or any Linux/macOS/Windows terminal
- Internet connection

### Python Packages

| Package | Required | Purpose |
|---------|----------|---------|
| requests | Yes | HTTP client |
| beautifulsoup4 | Yes | HTML parsing |
| tqdm | No | Progress bars |
| colorama | No | Terminal colors |
| yt-dlp | No | Video downloads (hentaihaven) |

### System Packages (Termux)

| Package | Required | Purpose |
|---------|----------|---------|
| python | Yes | Runtime |
| termux-api | No | Notifications, wallpaper |
| git | No | Auto-update feature |

---

## How It Works

1. **Search** - Queries the site's API or scrapes search results
2. **Filter** - Checks results against your blacklist
3. **Download** - Fetches content with concurrent workers and retry logic
4. **Validate** - Verifies file integrity via Content-Length
5. **Save** - Stores files and logs to history
6. **Notify** - Sends Android notification on completion (Termux)

---

## For Developers

The code is organized into modular classes:

- `ConfigManager` - Handles all config, history, bookmarks, blacklist
- `DLog` - Developer mode logger (only outputs when debug is enabled)
- `NHentaiDownloader` - nhentai API v2 client with concurrent image download
- `HanimeDownloader` - hanime.tv scraper
- `HentaiHavenDownloader` - hentaihaven with yt-dlp integration
- `Rule34Downloader` - rule34.xxx API client
- `GelbooruDownloader` - gelbooru.com API client
- `HitomiDownloader` - hitomi.la scraper
- `NHentaiTagDownloader` - nhentai specific tag queries

Each downloader implements `search_and_download(query, count, output_dir)`.

### Extending

To add a new site, create a class with:

```python
class MySiteDownloader:
    def search(self, query: str) -> list[dict]:
        # Return [{"slug": "...", "title": "..."}]
        ...

    def search_and_download(self, query: str, count: int, output_dir: str):
        ...
```

Then add it to `_download_from_site()` and `SITES`.

---

Happy gooning, ya freaks! :D
