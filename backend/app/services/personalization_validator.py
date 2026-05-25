from __future__ import annotations

import re
from dataclasses import dataclass

from app.llm.client import ResearchSummary


STOPWORDS = {
    "about",
    "after",
    "against",
    "also",
    "because",
    "between",
    "could",
    "first",
    "found",
    "from",
    "have",
    "into",
    "more",
    "most",
    "only",
    "other",
    "research",
    "their",
    "there",
    "these",
    "those",
    "through",
    "under",
    "with",
    "your",
}

BUZZWORDS = {
    "passionate",
    "driven",
    "cutting-edge",
    "cutting edge",
    "innovative",
    "leverage",
    "impactful",
    "synergy",
    "pioneering",
    "world-class",
}

FORMAL_PHRASES = {
    "i hope this email finds you well",
    "dear professor",
    "to whom it may concern",
    "i am writing to express",
    "esteemed",
}

NATURAL_PHRASES = {
    "i came across your work",
    "i was reading about",
    "i found it interesting that",
}


@dataclass
class EmailScoreResult:
    score: float
    specificity: int
    human_tone: int
    buzzword_score: int
    concise_formal_score: int
    feedback: list[str]


class PersonalizationValidator:
    def score_email(self, email: str, summary: ResearchSummary, professor_name: str) -> EmailScoreResult:
        lowered_email = email.lower()
        words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-]+\b", lowered_email)
        word_count = len(words)

        keyword_candidates = " ".join(
            [summary.main_research_area, *summary.technical_problems, summary.undergraduate_opportunity]
        ).lower()
        keywords = [
            token
            for token in re.findall(r"\b[a-z][a-z0-9\-]{4,}\b", keyword_candidates)
            if token not in STOPWORDS
        ]
        keyword_hits = len({k for k in keywords if k in lowered_email})

        specificity = 0
        if keyword_hits >= 3:
            specificity = 4
        elif keyword_hits == 2:
            specificity = 3
        elif keyword_hits == 1:
            specificity = 2
        if professor_name.split()[-1].lower() in lowered_email and specificity > 0:
            specificity = min(4, specificity + 1)

        human_tone = 0
        if re.search(r"\b(i'm|i've|i'd|don't|can't|it's|i was|i found)\b", lowered_email):
            human_tone += 1
        if any(phrase in lowered_email for phrase in NATURAL_PHRASES):
            human_tone += 1
        sentence_chunks = [s.strip() for s in re.split(r"[.!?]+", email) if s.strip()]
        avg_sentence_words = (sum(len(chunk.split()) for chunk in sentence_chunks) / len(sentence_chunks)) if sentence_chunks else 0
        if 8 <= avg_sentence_words <= 24:
            human_tone += 1

        buzzword_hits = sum(1 for term in BUZZWORDS if term in lowered_email)
        if buzzword_hits == 0:
            buzzword_score = 2
        elif buzzword_hits == 1:
            buzzword_score = 1
        else:
            buzzword_score = 0

        formal_hits = sum(1 for phrase in FORMAL_PHRASES if phrase in lowered_email)
        concise_formal_score = 1 if (120 <= word_count <= 180 and formal_hits == 0) else 0

        total = float(specificity + human_tone + buzzword_score + concise_formal_score)

        feedback: list[str] = []
        if specificity < 3:
            feedback.append("Add one concrete technical detail from the professor's research.")
        if human_tone < 2:
            feedback.append("Use a more natural student voice with simple phrasing and one casual connector.")
        if buzzword_score < 2:
            feedback.append("Remove buzzwords and keep language plain.")
        if concise_formal_score == 0:
            if word_count < 120 or word_count > 180:
                feedback.append("Keep the email between 120 and 180 words.")
            if formal_hits > 0:
                feedback.append("Reduce formal/corporate phrasing.")

        return EmailScoreResult(
            score=total,
            specificity=specificity,
            human_tone=human_tone,
            buzzword_score=buzzword_score,
            concise_formal_score=concise_formal_score,
            feedback=feedback,
        )

