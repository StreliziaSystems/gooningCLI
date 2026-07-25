# gooningCLI

```
 ██████╗  ██████╗  ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗  ██████╗██╗     ██╗
██╔════╝ ██╔═══██╗██╔═══██╗████╗  ██║██║████╗  ██║██╔════╝ ██╔════╝██║     ██║
██║  ███╗██║   ██║██║   ██║██╔██╗ ██║██║██╔██╗ ██║██║  ███╗██║     ██║     ██║
██║   ██║██║   ██║██║   ██║██║╚██╗██║██║██║╚██╗██║██║   ██║██║     ██║     ██║
╚██████╔╝╚██████╔╝╚██████╔╝██║ ╚████║██║██║ ╚████║╚██████╔╝╚██████╗███████╗██║
 ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚══════╝╚═╝
```

**v2.0.0** | made by **or4acle**

> *For educational purposes only.*

A multi-site hentai content downloader CLI built for Termux. Download manga, doujinshi, and videos from multiple sites with a single tool.

---

## Supported Sites

| Site | Type | Method |
|------|------|--------|
| nhentai.net | Manga/Doujinshi | API v2 |
| hanime.tv | Videos | Scraping |
| hentaihaven.xxx | Videos | yt-dlp |
| nhentai (specific tags) | Manga | API v2 |

---

## Features

- **Multi-site support** - Download from nhentai, hanime, hentaihaven
- **Concurrent downloads** - ThreadPoolExecutor for fast parallel image downloading
- **Resilient networking** - Exponential backoff, retry on failure, rate limiting
- **File validation** - Checks file size against Content-Length, retries incomplete downloads
- **Smart server rotation** - Distributes requests across multiple nhentai image servers
- **Download history** - Track everything you've downloaded
- **Bookmarks** - Save content to download later
- **Blacklist** - Filter out unwanted tags or specific gallery IDs
- **Statistics** - View your download stats, top tags, storage usage
- **Deduplication** - Find and remove duplicate files by hash
- **Organize** - Sort download folders by site, date, or type
- **Clean** - Remove empty folders, old downloads, or small files
- **Export** - Export galleries as JSON metadata, CBZ (comic archive), or ZIP
- **Batch mode** - Download from a text file with multiple search terms
- **Slideshow** - View downloaded images in terminal (ASCII art) or open them
- **Wallpaper** - Set downloaded images as Android wallpaper via Termux API
- **Notifications** - Android notifications when downloads complete
- **Themes** - 6 built-in color themes (default, fire, ocean, matrix, mono, pink)
- **Proxy support** - SOCKS5/HTTP proxy configuration
- **CLI arguments** - Use interactively or script with command-line args

---

## Installation (Termux)

```bash
# Clone the repo
git clone https://github.com/or4acle/gooningCLI.git
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

Opens a menu with all 20 commands. Just enter the number.

### Command Line Mode

```bash
# Search and download
python gooningcli.py search "futa" -n 10 -s nhentai

# Download random gallery
python gooningcli.py random

# View gallery info
python gooningcli.py info 12345

# View history
python gooningcli.py history

# View stats
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
  "notify": true
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
| `auto_zip` | `false` | Auto-zip manga galleries after download |
| `auto_cbz` | `false` | Auto-create CBZ archives after download |
| `notify` | `true` | Android notifications (Termux only) |

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
# Or point directly:
# Enter: my_downloads.txt
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
- `NHentaiDownloader` - nhentai API v2 client with concurrent image download
- `HanimeDownloader` - hanime.tv scraper
- `HentaiHavenDownloader` - hentaihaven with yt-dlp integration
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

## Disclaimer

This tool is provided for educational and research purposes only. Users are responsible for complying with the terms of service of any site they access and all applicable laws.

---

## License

MIT
