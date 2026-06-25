# CP45: Article Fetch / Extraction MVP

## Goal
Extend the CP44 URL input workflow with a safe, limited static HTML article extractor. Users provide a URL, the system fetches the raw HTML (no JS rendering), extracts title/description/body text, and feeds it into the existing source-contract pipeline.

## What This Is

**Static HTML extraction only.** The system makes a single HTTP GET request, reads the raw HTML response (max 512 KB, 6-second timeout), parses it with Python's built-in `html.parser`, and extracts text content. No JavaScript execution, no browser automation, no image/CSS download.

## What This Is NOT

- Not a crawler — no recursive crawling, no sitemap following
- No JS rendering (no Playwright, Puppeteer, Selenium)
- No login/session/cookie handling
- Not guaranteed to work on every website (SPAs, AMP pages, paywalled content will likely fail)
- No batch fetching — one URL at a time
- Not a replacement for a real news API

## API

### POST /api/article/extract

Fetch a URL and extract article fields.

**Input:**
```json
{ "url": "https://openai.com/blog/example" }
```

**Output (success):**
```json
{
  "ok": true,
  "article": {
    "url": "https://openai.com/blog/example",
    "title": "OpenAI Blog — Example Post",
    "description": "Description from og:description or meta.",
    "body_text": "First ~3000 chars of body text...",
    "source_domain": "openai.com",
    "content_type": "text/html",
    "fetched": true
  }
}
```

**Output (failure):**
```json
{ "ok": false, "error": "URL extraction failed: ..." }
```

### POST /api/episode/source-contract

New `source_type: url_fetch`:

```json
{
  "source_type": "url_fetch",
  "url": "https://openai.com/blog/example",
  "source_id": "openai_blog",
  "tags": ["api", "release"],
  "limit": 1,
  "template_id": "breaking_news_v1",
  "episode_title": "官方博客速讯",
  "episode_subtitle": "URL 抽取生成"
}
```

Flow: `fetch_and_extract_article(url)` → extract fields → `normalize_url_item()` → episode_items → contract.

If extraction fails, returns `ok: false` with a message suggesting fallback to manual URL input.

## Extraction Rules

**Title priority:** `og:title` > `<title>` > first `<h1>`

**Description priority:** `og:description` > `<meta name="description">` > first `<p>` paragraph

**Body text:**
- Parsed with `html.parser`
- Strips `<script>`, `<style>`, `<noscript>`, `<svg>`, `<math>` content
- Collapses whitespace
- Limited to 3000 characters

**Truncation:**
- `title`: max 200 chars
- `description`: max 500 chars
- `body_text`: max 3000 chars

## Security Restrictions

- URL scheme must be `http://` or `https://` — `javascript:`, `file://`, `data:` etc. rejected
- No private IPs: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`
- No localhost / `127.0.0.1` / `::1`
- No `0.0.0.0`
- Response max 512 KB
- Timeout 6 seconds
- Content-Type must be `text/html` or `application/xhtml+xml`
- User-Agent: `chalk-news-video/0.1` (identifies as article extractor bot)

## Frontend

In the URL input section of the Source Contract Panel:

1. User enters a URL
2. Clicks **"自动抽取 URL"** (Auto-extract URL)
3. System calls `POST /api/article/extract`
4. On success: `source-url-title` and `source-url-summary` are auto-filled
5. User reviews the extracted content, optionally edits it
6. User clicks **"从 URL 生成栏目"** to generate the contract

On extraction failure, the form remains usable — the user can fill title/summary manually.

## Fallback

If URL extraction fails (network error, non-HTML page, SPA without server-rendered content), the user can still use the CP44 **manual URL input** path: fill in title and summary manually and click "从 URL 生成栏目".

## Not Done
- No JS rendering / SPA support
- No Playwright or browser automation
- No real news API integration
- No real LLM / TTS
- No Remotion
- No batch / sitemap crawling
- No login / session handling
- No outputs written

## Tests
```bash
python scripts/test_cp45_article_fetch_extraction.py
```

Tests cover: HTML extraction (title, description, og:, script/style stripping, truncation), security validation (private IPs, localhost, bad schemes), API error handling, and contract generation path.
