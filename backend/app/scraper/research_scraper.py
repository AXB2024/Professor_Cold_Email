from __future__ import annotations

import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.core.config import Settings
from app.models.schemas import ProfessorInput

logger = logging.getLogger(__name__)


class ResearchScraper:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def extract_research_text(self, professor: ProfessorInput) -> str:
        if professor.research_text:
            return self._clean_text(professor.research_text)

        if not professor.website_url:
            raise ValueError("No research source was provided.")

        logger.info("Scraping research text for %s from %s", professor.name, professor.website_url)
        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(str(professor.website_url))
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "form", "noscript", "svg"]):
            tag.decompose()

        for noisy in soup.find_all(
            attrs={"class": re.compile(r"nav|menu|footer|sidebar|cookie|social", re.I)}
        ):
            noisy.decompose()

        for noisy in soup.find_all(attrs={"id": re.compile(r"nav|menu|footer|sidebar|cookie|social", re.I)}):
            noisy.decompose()

        text_blocks: list[str] = []
        for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            text = self._clean_text(tag.get_text(" ", strip=True))
            if len(text.split()) >= 8:
                text_blocks.append(text)

        if not text_blocks:
            fallback = self._clean_text(soup.get_text(" ", strip=True))
            return fallback[: self.settings.max_scraped_chars]

        deduped: list[str] = []
        seen: set[str] = set()
        for block in text_blocks:
            key = block.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(block)

        joined = "\n".join(deduped)
        return joined[: self.settings.max_scraped_chars]

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

