from __future__ import annotations

from dataclasses import dataclass


DATASET_SOURCE = "mosl-video-dataset"
DATASET_VERSION = "source-import-v1"


@dataclass(frozen=True)
class MoslCategory:
    source_folder: str
    display_name: str
    mode: str


CATEGORIES: tuple[MoslCategory, ...] = (
    MoslCategory("mosl_videos_dataset_Diverse", "Diverse", "WORD_ISOLATED"),
    MoslCategory("mosl_videos_dataset_Letters", "Letters", "ALPHABET_STATIC"),
    MoslCategory("mosl_videos_dataset_Numbers", "Numbers", "WORD_ISOLATED"),
    MoslCategory("mosl_videos_dataset_Pronouns", "Pronouns", "WORD_ISOLATED"),
    MoslCategory(
        "mosl_videos_dataset_days_months_seasons",
        "Days_Months_Seasons",
        "WORD_ISOLATED",
    ),
)

CATEGORY_BY_FOLDER = {item.source_folder: item for item in CATEGORIES}
