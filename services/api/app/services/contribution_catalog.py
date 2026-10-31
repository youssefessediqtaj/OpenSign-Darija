from dataclasses import dataclass


@dataclass(frozen=True)
class ContributionSign:
    key: str
    label_ar: str
    darija_transliteration: str
    reference_video_identifier: str
    reference_video_path: str
    poster_path: str
    recording_instructions: str
    active: bool
    expected_min_duration_seconds: float
    expected_max_duration_seconds: float


CONTRIBUTION_SIGNS: tuple[ContributionSign, ...] = (
    ContributionSign(
        key="salam",
        label_ar="سلام",
        darija_transliteration="salam",
        reference_video_identifier="opensigne-reference-salam-v1",
        reference_video_path="/reference-signs/salam.mp4",
        poster_path="/reference-signs/posters/salam.svg",
        recording_instructions=(
            "Reproduisez une seule fois le signe « سلام », puis revenez au repos."
        ),
        active=True,
        expected_min_duration_seconds=2.0,
        expected_max_duration_seconds=10.0,
    ),
    ContributionSign(
        key="chokran",
        label_ar="شكرا",
        darija_transliteration="chokran",
        reference_video_identifier="opensigne-reference-chokran-v1",
        reference_video_path="/reference-signs/chokran.mp4",
        poster_path="/reference-signs/posters/chokran.svg",
        recording_instructions=(
            "Reproduisez une seule fois le signe « شكرا », puis revenez au repos."
        ),
        active=True,
        expected_min_duration_seconds=2.0,
        expected_max_duration_seconds=10.0,
    ),
    ContributionSign(
        key="tabib",
        label_ar="طبيب",
        darija_transliteration="tabib",
        reference_video_identifier="opensigne-reference-tabib-v1",
        reference_video_path="/reference-signs/tabib.mp4",
        poster_path="/reference-signs/posters/tabib.svg",
        recording_instructions=(
            "Reproduisez une seule fois le signe « طبيب », puis revenez au repos."
        ),
        active=True,
        expected_min_duration_seconds=2.0,
        expected_max_duration_seconds=10.0,
    ),
    ContributionSign(
        key="mosaada",
        label_ar="مساعدة",
        darija_transliteration="mosaada",
        reference_video_identifier="opensigne-reference-mosaada-v1",
        reference_video_path="/reference-signs/mosaada.mp4",
        poster_path="/reference-signs/posters/mosaada.svg",
        recording_instructions=(
            "Reproduisez une seule fois le signe « مساعدة », puis revenez au repos."
        ),
        active=True,
        expected_min_duration_seconds=2.0,
        expected_max_duration_seconds=10.0,
    ),
    ContributionSign(
        key="maa",
        label_ar="ماء",
        darija_transliteration="maa",
        reference_video_identifier="opensigne-reference-maa-v1",
        reference_video_path="/reference-signs/maa.mp4",
        poster_path="/reference-signs/posters/maa.svg",
        recording_instructions=(
            "Reproduisez une seule fois le signe « ماء », puis revenez au repos."
        ),
        active=True,
        expected_min_duration_seconds=2.0,
        expected_max_duration_seconds=10.0,
    ),
)

CONTRIBUTION_SIGN_BY_KEY = {sign.key: sign for sign in CONTRIBUTION_SIGNS}


def get_active_contribution_sign(key: str) -> ContributionSign | None:
    sign = CONTRIBUTION_SIGN_BY_KEY.get(key)
    return sign if sign and sign.active else None
