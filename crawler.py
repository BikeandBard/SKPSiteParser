"""
crawler.py — BFS-обходчик сайта.

Собирает все внутренние URL, строит словарь parent → [children].
Исключает якоря, внешние домены, файлы, mailto/tel/javascript.
"""

import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import Config
from logger import setup_logger, retry_on_error

# Расширения файлов, которые исключаем
SKIP_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".zip", ".rar", ".tar", ".gz", ".7z",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".exe", ".msi", ".dmg", ".apk",
    ".csv", ".json", ".xml",
    ".ico", ".woff", ".woff2", ".ttf", ".eot",
}

# Протоколы, которые исключаем
SKIP_PROTOCOLS = {"mailto:", "tel:", "javascript:", "fax:", "skype:", "viber:", "whatsapp:"}

def _is_same_domain(url: str, base_domain: str) -> bool:
    """Проверяет, принадлежит ли URL тому же домену (и поддоменам)."""
    parsed = urlparse(url)
    if not parsed.netloc:
        return True  # относительная ссылка
    return parsed.netloc == base_domain or parsed.netloc.endswith(f".{base_domain}")


def _is_skip_url(url: str) -> bool:
    """Проверяет, нужно ли пропустить URL."""
    if "#" in url:
        parsed = urlparse(url)
        if not parsed.path and not parsed.query:
            return True
        return False

    for proto in SKIP_PROTOCOLS:
        if url.strip().lower().startswith(proto):
            return True

    path = urlparse(url).path.lower()
    for ext in SKIP_EXTENSIONS:
        if path.endswith(ext):
            return True

    return False


def _normalize_url(href: str, base_url: str) -> str | None:
    """Нормализует href в абсолютный URL."""
    if not href or not href.strip():
        return None

    href = href.strip()

    if _is_skip_url(href):
        return None

    if href in ("", "/", "#"):
        return None

    absolute = urljoin(base_url, href)

    parsed = urlparse(absolute)
    absolute = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        absolute += f"?{parsed.query}"

    absolute = absolute.rstrip("/")

    return absolute


@retry_on_error(attempts=2, delay=1.0)
def _fetch_page(url: str, timeout: int) -> requests.Response:
    """Загружает страницу с retry-логикой."""
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    response.raise_for_status()
    return response


def crawl(config: Config) -> tuple[list[str], dict[str, list[str]]]:
    """
    BFS-обход сайта.

    Args:
        config: объект конфигурации

    Returns:
        (all_urls, links_dict):
            all_urls — список всех найденных URL
            links_dict — словарь {parent_url: [child_url1, child_url2, ...]}
    """
    logger = setup_logger("crawler", config.log_file)
    logger.info("Начинаю обход сайта: %s (глубина: %d)", config.start_url, config.max_depth)

    base_domain = urlparse(config.start_url).netloc

    queue: deque[tuple[str, int]] = deque()
    queue.append((config.start_url.rstrip("/"), 0))

    visited: set[str] = set()
    all_urls: list[str] = []
    links_dict: dict[str, list[str]] = {}

    while queue:
        url, depth = queue.popleft()

        if url in visited:
            continue

        if depth > config.max_depth:
            continue

        logger.info("[Глубина %d] Загружаю: %s", depth, url)
        visited.add(url)
        all_urls.append(url)

        try:
            response = _fetch_page(url, config.timeout_seconds)
        except requests.exceptions.Timeout:
            logger.error("Timeout при загрузке: %s", url)
            links_dict[url] = []
            continue
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError при загрузке: %s", url)
            links_dict[url] = []
            continue
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP %s при загрузке: %s",
                         e.response.status_code if e.response else "?", url)
            links_dict[url] = []
            continue
        except Exception as e:
            logger.error("Ошибка при загрузке %s: %s", url, e)
            links_dict[url] = []
            continue

        children: list[str] = []
        try:
            soup = BeautifulSoup(response.text, "lxml")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                normalized = _normalize_url(href, url)
                if normalized is None:
                    continue
                if not _is_same_domain(normalized, base_domain):
                    continue
                if normalized in visited:
                    continue
                children.append(normalized)
        except Exception as e:
            logger.error("Ошибка парсинга HTML на %s: %s", url, e)

        links_dict[url] = children

        for child in children:
            if child not in visited and child not in {u for u, _ in queue}:
                queue.append((child, depth + 1))

        time.sleep(config.delay_seconds)

    logger.info("Обход завершён. Найдено страниц: %d", len(all_urls))
    return all_urls, links_dict
