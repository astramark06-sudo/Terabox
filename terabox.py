"""Local TeraBox download helper using the service's browser interface."""
import argparse
from pathlib import Path
import re
from urllib.parse import urlsplit

DOMAINS = {"terabox.com", "1024terabox.com", "1024tera.com", "terabox.app", "teraboxlink.com"}


def validate_share_url(value):
    value = value.strip()
    try:
        u = urlsplit(value)
        if (u.scheme != "https" or u.username is not None or u.password is not None
                or u.port is not None or not u.hostname
                or not any(u.hostname == d or u.hostname == "www." + d for d in DOMAINS)
                or not (re.fullmatch(r"/s/[A-Za-z0-9_-]+/?", u.path)
                        or (u.path == "/sharing/link" and u.query))):
            raise ValueError
    except ValueError:
        raise ValueError("Enter a supported HTTPS TeraBox share URL.") from None
    return value


def reserve_name(directory, suggested):
    # Do not allow paths, control characters or Windows device names from a server.
    name = re.sub(r'[\x00-\x1f<>:"/\\|?*]', "_", suggested).strip(" .") or "download"
    if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        name = "_" + name
    p = Path(name)
    suffix = p.suffix[:20]
    stem = (p.stem if p.suffix else name)[:110]
    for i in range(10000):
        target = directory / (stem + (f" ({i})" if i else "") + suffix)
        try:
            with target.open("xb"):
                pass
            return target
        except FileExistsError:
            continue
    raise OSError("Too many files with the same name.")


def save_download(download, directory, show_url=False):
    target = reserve_name(directory, download.suggested_filename)
    try:
        download.save_as(str(target))
    except Exception:
        target.unlink(missing_ok=True)
        raise
    print(f"Saved: {target}", flush=True)
    if show_url:
        u = urlsplit(download.url)
        if u.scheme == "https" and u.hostname and u.username is None and u.password is None:
            print("Browser download URL (private, may expire or require this session):", download.url, flush=True)
        else:
            print("No reusable HTTPS URL was exposed by the browser.", flush=True)
    return target


def run(url, directory, show_url=False, browser_path=None):
    from playwright.sync_api import sync_playwright, Error
    directory.mkdir(parents=True, exist_ok=True)
    completed = []
    failed = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, executable_path=browser_path)
        context = browser.new_context(accept_downloads=True)

        def on_download(download):
            try:
                completed.append(save_download(download, directory, show_url))
            except Exception as exc:
                failed.append(type(exc).__name__)
                print("Download failed:", type(exc).__name__, flush=True)

        def attach(page):
            page.on("download", on_download)

        context.on("page", attach)
        page = context.new_page()
        print("Use the official page to select files and click Download. Sign in if required.", flush=True)
        print("Keep the browser open until downloads finish, then close all tabs.", flush=True)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Error:
            print("Navigation did not finish. Check the browser, connection and share availability.", flush=True)
        try:
            while browser.is_connected() and context.pages:
                try:
                    context.pages[0].wait_for_timeout(250)
                except Error:
                    if not browser.is_connected() or not context.pages:
                        break
        except KeyboardInterrupt:
            print("Stopped by user.", flush=True)
        finally:
            if browser.is_connected():
                browser.close()
    print(f"Completed: {len(completed)}; failed: {len(failed)}", flush=True)
    return 0 if completed and not failed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", help="TeraBox share URL; prompted if omitted")
    parser.add_argument("--output", type=Path, default=Path.home() / "Downloads" / "TeraBox")
    parser.add_argument("--show-url", action="store_true", help="Print private browser download URLs locally")
    parser.add_argument("--browser-path", help="Optional installed Chromium executable")
    args = parser.parse_args()
    try:
        url = validate_share_url(args.url or input("TeraBox share URL: "))
        return run(url, args.output.expanduser().resolve(), args.show_url, args.browser_path)
    except (ValueError, EOFError) as exc:
        print(str(exc) or "No URL supplied.")
        return 2
    except ImportError:
        print("Install Playwright: python -m pip install playwright; python -m playwright install chromium")
        return 2
    except Exception as exc:
        print("Unable to start or complete downloader:", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
