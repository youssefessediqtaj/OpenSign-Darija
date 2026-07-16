# Manual Browser Testing

Manual checks to run before accepting a dataset release:

1. Start Docker with `docker compose up --build`.
2. Open `http://localhost:8081`.
3. Log in as `contributor@example.test`.
4. Open `/app/contribute/consent` and confirm every checkbox starts unchecked.
5. Grant only landmark consents and confirm video controls remain unavailable.
6. Create a contribution and submit it.
7. Log in as `linguist@example.test`, approve the linguistic review.
8. Log in as `ml-reviewer@example.test`, approve the ML review.
9. Log in as `admin@example.test`, build and validate a dataset version.
10. Confirm the exported manifest has no email or auth user ID.

Real camera/mobile checks are UNCONFIRMED until run on the target browser/device.
