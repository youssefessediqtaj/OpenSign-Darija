# Privacy And Security

The public recognition page is anonymous and landmark-only.

The browser must not send raw video, images, canvas screenshots, microphone audio,
base64 camera payloads, persistent visitor IDs, arbitrary text-to-speech input, or
direct requests to internal inference or speech services.

The API validates closed schemas and returns compact known/UNKNOWN decisions. It
does not persist recognition records and does not mount auth, admin, dataset, or
database routes. Speech is requested only for API-verified supported sign keys.

Nginx is the public boundary on port `8081`; internal service ports are not exposed
to the host.
