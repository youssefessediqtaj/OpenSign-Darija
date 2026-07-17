FEATURE_SCHEMA_VERSION = "1.0.0"
FEATURE_COUNT = 63
MASK_FEATURE_COUNT = 21
TARGET_FRAMES = 30


def feature_schema() -> dict[str, object]:
    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "coordinate_format": "torso_normalized_v1",
        "feature_count": FEATURE_COUNT,
        "mask_feature_count": MASK_FEATURE_COUNT,
        "target_frames": TARGET_FRAMES,
        "dtype": "float32",
        "order": "21 compact landmarks, each [x, y, z]",
    }
