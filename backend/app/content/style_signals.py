"""Deterministic style-signal extraction from a user's own past posts.

No AI call here -- every signal is a plain, reproducible measurement
over the raw text, computed once per voice-profile submission and handed
to `content.voice_profile.v1` as context alongside the samples
themselves. The single AI call turns these numbers plus the actual
writing into a qualitative descriptor; it never has to guess the numbers
itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z']+")
_EMOJI = re.compile("[\U0001f300-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff]")
_HASHTAG = re.compile(r"#\w+")
_FIRST_PERSON = re.compile(r"\b(?:I|me|my|mine|we|us|our|ours)\b", re.IGNORECASE)
_THIRD_PERSON = re.compile(r"\b(?:he|she|they|him|her|them|his|hers|their|theirs)\b", re.IGNORECASE)
_LIST_MARKER = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class StyleSignals:
    sample_count: int
    avg_sentence_length_words: float
    avg_paragraph_length_sentences: float
    line_break_density: float  # newlines per 100 words
    emoji_frequency: float  # emoji per 100 words
    hashtag_frequency: float  # hashtags per post, averaged
    first_person_ratio: float  # share of first-vs-third-person pronoun hits, 0-1
    question_rate: float  # question marks per post, averaged
    uses_lists_ratio: float  # fraction of posts containing a bullet/numbered list
    avg_reading_grade: float  # an approximate Flesch-Kincaid grade level

    def to_context_block(self) -> str:
        return (
            f"- Sample size: {self.sample_count} posts\n"
            f"- Average sentence length: {self.avg_sentence_length_words:.1f} words\n"
            f"- Average paragraph length: {self.avg_paragraph_length_sentences:.1f} sentences\n"
            f"- Line-break density: {self.line_break_density:.1f} per 100 words\n"
            f"- Emoji frequency: {self.emoji_frequency:.1f} per 100 words\n"
            f"- Hashtag frequency: {self.hashtag_frequency:.1f} per post\n"
            f"- First-person pronoun share (vs. third-person): {self.first_person_ratio * 100:.0f}%\n"
            f"- Questions per post: {self.question_rate:.1f}\n"
            f"- Uses a bullet or numbered list in {self.uses_lists_ratio * 100:.0f}% of posts\n"
            f"- Approximate reading grade level: {self.avg_reading_grade:.1f}"
        )


def _count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _reading_grade(*, words: list[str], sentence_count: int) -> float:
    if not words or sentence_count == 0:
        return 0.0
    syllables = sum(_count_syllables(word) for word in words)
    words_per_sentence = len(words) / sentence_count
    syllables_per_word = syllables / len(words)
    return 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59


def compute_style_signals(samples: list[str]) -> StyleSignals:
    if not samples:
        raise ValueError("compute_style_signals requires at least one sample")

    total_words = 0
    total_sentences = 0
    total_paragraphs = 0
    total_newlines = 0
    total_emoji = 0
    total_hashtags = 0
    total_questions = 0
    first_person_hits = 0
    third_person_hits = 0
    posts_with_lists = 0
    all_words: list[str] = []

    for sample in samples:
        words = _WORD.findall(sample)
        all_words.extend(words)
        total_words += len(words)

        sentences = [part for part in _SENTENCE_BOUNDARY.split(sample.strip()) if part.strip()]
        total_sentences += max(1, len(sentences))

        paragraphs = [part for part in sample.split("\n\n") if part.strip()]
        total_paragraphs += max(1, len(paragraphs))

        total_newlines += sample.count("\n")
        total_emoji += len(_EMOJI.findall(sample))
        total_hashtags += len(_HASHTAG.findall(sample))
        total_questions += sample.count("?")
        first_person_hits += len(_FIRST_PERSON.findall(sample))
        third_person_hits += len(_THIRD_PERSON.findall(sample))
        if _LIST_MARKER.search(sample):
            posts_with_lists += 1

    count = len(samples)
    words_per_100 = total_words / 100 if total_words else 1.0
    pronoun_hits = first_person_hits + third_person_hits

    return StyleSignals(
        sample_count=count,
        avg_sentence_length_words=(total_words / total_sentences) if total_sentences else 0.0,
        avg_paragraph_length_sentences=(
            (total_sentences / total_paragraphs) if total_paragraphs else 0.0
        ),
        line_break_density=total_newlines / words_per_100,
        emoji_frequency=total_emoji / words_per_100,
        hashtag_frequency=total_hashtags / count,
        first_person_ratio=(first_person_hits / pronoun_hits) if pronoun_hits else 0.0,
        question_rate=total_questions / count,
        uses_lists_ratio=posts_with_lists / count,
        avg_reading_grade=_reading_grade(words=all_words, sentence_count=total_sentences),
    )
