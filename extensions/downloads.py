import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests


DATA_SOURCES_DIR = Path("/Users/platonkurbatov/Desktop/TMK2/data_sources")
_CROSSREF_API_URL = "https://api.crossref.org/works"


def ensure_data_sources_dir() -> None:
    DATA_SOURCES_DIR.mkdir(parents=True, exist_ok=True)


def _guess_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = os.path.basename(path)
    if not name:
        return "downloaded.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def download_pdf(url: str) -> Path:
    ensure_data_sources_dir()

    filename = _guess_filename_from_url(url)
    target_path = DATA_SOURCES_DIR / filename

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    content_disp = response.headers.get("content-disposition", "")
    if "filename=" in content_disp:
        # очень простое извлечение, без сложного парсинга
        fname = content_disp.split("filename=")[-1].strip('"; ')
        if fname:
            target_path = DATA_SOURCES_DIR / fname

    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return target_path


def download_arxiv_pdf(arxiv_id: str) -> Path:
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    ensure_data_sources_dir()

    safe_id = arxiv_id.replace("/", "_")
    target_path = DATA_SOURCES_DIR / f"arxiv_{safe_id}.pdf"

    response = requests.get(pdf_url, stream=True, timeout=60)
    response.raise_for_status()

    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return target_path


def download_arxiv_batch(ids: list[str]) -> list[Path]:
    paths: list[Path] = []
    for arxiv_id in ids:
        try:
            path = download_arxiv_pdf(arxiv_id)
            print(f"Downloaded arXiv {arxiv_id} -> {path}")
            paths.append(path)
        except Exception as exc:  # pragma: no cover - защитный принт
            print(f"Failed to download arXiv {arxiv_id}: {exc}")
    return paths


def download_crossref_metallurgy(
    rows: int = 20,
    query: str | None = None,
) -> list[Path]:
    ensure_data_sources_dir()

    base_query = "metallurgy"
    if query:
        base_query = f"{base_query} {query}"

    params: dict[str, str | int] = {
        "filter": "type:journal-article",
        "rows": rows,
        "sort": "published",
        "order": "desc",
        "query": base_query,
    }

    resp = requests.get(_CROSSREF_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("message", {}).get("items", [])
    print(f"CrossRef returned {len(items)} items for query {base_query!r}")
    downloaded_paths: list[Path] = []

    for item in items:
        links = item.get("link") or []
        pdf_url = None
        for link in links:
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL")
                break
        if not pdf_url:
            doi = item.get("DOI", "unknown DOI")
            title = " ".join(item.get("title") or []) or "unknown"
            print(f"No direct PDF link for {doi} :: {title!r}")
            continue

        try:
            path = download_pdf(pdf_url)
            title = " ".join(item.get("title") or []) or "unknown"
            print(f"Downloaded metallurgy article: {title!r} -> {path}")
            downloaded_paths.append(path)
        except Exception as exc:  # pragma: no cover - защитный принт
            doi = item.get("DOI", "unknown DOI")
            print(f"Failed to download PDF for {doi}: {exc}")

    if not downloaded_paths:
        print(
            "No PDFs were downloaded from CrossRef "
            "(either no items, or none exposed a direct application/pdf link)."
        )

    return downloaded_paths


def download_mdpi_metals_issue(issue_url: str) -> list[Path]:
    ensure_data_sources_dir()

    if "mdpi.com/2075-4701/" not in issue_url:
        raise ValueError(
            "download_mdpi_metals_issue ожидает URL выпуска журнала Metals, "
            "например: https://www.mdpi.com/2075-4701/15/1"
        )

    resp = requests.get(
        issue_url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/129.0 Safari/537.36"
            )
        },
    )
    resp.raise_for_status()
    html = resp.text

    article_paths = set(
        re.findall(r'"/(2075-4701/\d+/\d+/\d+)"', html)
    )
    if not article_paths:
        print("No article links found on issue page.")
        return []

    print(f"Found {len(article_paths)} article links on Metals issue page.")

    downloaded: list[Path] = []
    base = "https://www.mdpi.com"
    for path_part in sorted(article_paths):
        pdf_url = f"{base}/{path_part}/pdf"
        try:
            p = download_pdf(pdf_url)
            print(f"Downloaded MDPI Metals PDF: {pdf_url} -> {p}")
            downloaded.append(p)
        except Exception as exc:
            print(f"Failed to download MDPI Metals PDF {pdf_url}: {exc}")

    return downloaded


def download_from_file(urls_file: Path | str) -> list[Path]:
    ensure_data_sources_dir()

    path = Path(urls_file)
    if not path.exists():
        raise FileNotFoundError(f"URLs file not found: {path}")

    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    print(f"Found {len(urls)} URLs in {path}")

    downloaded: list[Path] = []
    for url in urls:
        try:
            p = download_pdf(url)
            print(f"Downloaded PDF from {url} -> {p}")
            downloaded.append(p)
        except Exception as exc:  # pragma: no cover - защитный принт
            print(f"Failed to download {url}: {exc}")

    return downloaded


if __name__ == "__main__":
    # Примеры использования:
    # 1) Скачивание конкретной статьи по прямому URL (если знаешь ссылку на PDF):
    # url = "https://example.com/some-paper.pdf"
    # print(download_pdf(url))

    # 2) Скачивание нескольких статей с arXiv:
    # Пример 2: скачивание нескольких статей с arXiv:
    example_ids = [
        "2401.00001",
        "2307.12345",
    ]
    download_arxiv_batch(example_ids)

    # Пример 3: скачать свежие статьи по металлургии из CrossRef (если есть open‑access PDF):
    # download_crossref_metallurgy(rows=10)

    # Пример 4: скачать все статьи из выпуска журнала Metals (MDPI, open‑access):
    # example_issue_url = "https://www.mdpi.com/2075-4701/15/1"
    # download_mdpi_metals_issue(example_issue_url)

    # Пример 5: скачать PDF по списку ссылок из текстового файла.
    # Создай файл pdf_urls.txt в корне проекта и запиши по одному URL на строку.
    # urls_list_file = Path("/Users/platonkurbatov/Desktop/TMK2/pdf_urls.txt")
    # download_from_file(urls_list_file)



