# TeraBox local downloader

A browser-based helper for files you are authorized to download. It uses TeraBox's normal download interface rather than a third-party download server. It does not bypass account, payment, or access requirements.

## Setup (desktop Python 3.10+)

```sh
python -m pip install playwright
python -m playwright install chromium
python terabox.py
```

Paste the HTTPS share URL when prompted. In the opened browser, sign in if necessary, select the permitted files, and click Download. Keep the browser open until saving finishes. Files are saved to Downloads/TeraBox under your home directory by default. Duplicate names are preserved, not overwritten.

Optional: run `python terabox.py --show-url` to display the browser's HTTPS download URL locally when available. Such URLs may be temporary or session-bound; they are not guaranteed to work separately. Do not publish them. Use `--output` to select a different output directory.

## Verification

```sh
python -m unittest -v
```

Four offline unit tests passed, covering URL validation, safe output names, duplicate preservation, and failure cleanup. A real Chromium offline download was also saved and its bytes verified. Live TeraBox access was unavailable in the development environment, so live service compatibility and the requested download remain unverified.

## Design reference

The Ronnie7866/terabox-downloader-online repository describes a server-side link-resolution approach requiring session cookies. This independent implementation instead uses an interactive local browser, without extracting or storing account cookies. It is not a headless direct-link API and does not automate selecting files.
