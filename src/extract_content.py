"""Article body extractor.

Strategy (per Checkpoint 1 spec):
1. Try `trafilatura.extract` (boilerplate removal).
2. Fall back to `requests` + `BeautifulSoup`, concatenating <p> tags.
3. Return "" if both fail; the caller decides the fallback to RSS summary.

No headless browser, no JavaScript rendering. Pure HTTP + HTML parse.
"""


import requests
from bs4 import BeautifulSoup


DEFAULT_TIMEOUT = 15  # seconds
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36 "
    "chalk-news-video/0.6 (+https://example.invalid)"
)
MIN_PARAGRAPH_LEN = 30  # drop trivially short <p> bodies
MIN_EXTRACTED_LEN = 50  # treat trafilatura output shorter than this as empty


def _try_trafilatura(url):
    try:
        import trafilatura  # imported lazily so a missing dep doesn't kill BS path
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )
        if text and len(text.strip()) >= MIN_EXTRACTED_LEN:
            return text.strip()
    except Exception:
        pass
    return ""


def _try_beautifulsoup(url, timeout):
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup.find_all(["script", "style", "noscript", "nav",
                                   "footer", "header", "aside"]):
            tag.decompose()

        # Prefer <article> if present
        article = soup.find("article")
        target = article or soup.body or soup

        paras = []
        for p in target.find_all("p"):
            txt = p.get_text(separator=" ", strip=True)
            if len(txt) >= MIN_PARAGRAPH_LEN:
                paras.append(txt)

        if paras:
            return "\n\n".join(paras).strip()
    except Exception:
        pass
    return ""


def extract_article_content(url, timeout=DEFAULT_TIMEOUT):
    """Return the extracted article text, or "" on failure.

    Args:
        url: absolute http(s) URL of the article.
        timeout: HTTP timeout in seconds (default 15).

    Returns:
        Stripped article body, or "" if neither extractor produced usable text.
    """
    if not url:
        return ""
    url = str(url).strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return ""

    text = _try_trafilatura(url)
    if text:
        return text

    return _try_beautifulsoup(url, timeout)
