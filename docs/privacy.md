# Privacy

## Processed Locally

The browser processes the live camera stream locally to extract landmarks.

## Sent To Server

Only compact normalized landmark features, presence masks, quality metrics, and anonymous/session metadata are sent.

## Not Sent

- raw video;
- JPEG or PNG frames;
- canvas exports;
- audio;
- screenshots;
- full face mesh unless explicitly added in a future schema.

## Stored

The backend stores recognition session metadata and predictions. It does not store the full landmark sequence in PostgreSQL.

## Sensitivity

Landmarks are not fully anonymous. They describe body motion and can be sensitive, so future storage or dataset contribution must require explicit consent and a separate license.
