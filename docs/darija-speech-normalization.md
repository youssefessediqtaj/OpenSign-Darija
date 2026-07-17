# Darija Speech Normalization

The speech service keeps `original_text`, `normalized_text`, text hashes and `normalization_version` separate.

Rules in `darija-normalizer-1.0.0`:

- Unicode NFKC normalization
- invisible/control character removal
- repeated whitespace collapse
- repeated punctuation cleanup
- limited Arabizi dictionary conversion, for example `3afak 3awnouni` -> `عافاك عاونوني`
- known Latin Darija words, for example `bghit lma` -> `بغيت الما`
- Moroccan phone-like numbers read digit by digit
- simple known amounts, for example `20 درهم` -> `عشرين درهم`

Unknown Latin tokens are preserved by the normalizer and should be corrected by the user before relying on pronunciation.
