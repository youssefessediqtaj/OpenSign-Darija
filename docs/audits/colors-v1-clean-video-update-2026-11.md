# COLORS_V1 cleaned-video update — 2026-11-02

The owner supplied ten cleaned replacements, described as removing logos, text and unnecessary elements. Filename-derived variant mappings and retention of the earlier source IDs are provisional: correspondence and whether editing materially altered a performance require manual review. Rights, consent, signer identity and linguistic review remain unconfirmed or pending; local experimental use was requested. All ten old registered paths are now missing from the active directory, all ten current paths are newly named, and no current hash matches an old hash. There are zero unchanged videos and zero missing expected variants. The original user ZIP remains in Downloads; all ten videos in it match the archived manifest hashes. No legacy MoSL archive was changed.

## Inventory

Checksums are SHA-256. All ten files decoded successfully with FFmpeg. The first/last hand times are detector suggestions, not validated sign boundaries. Full video and both technical and linguistic decisions require review.

| Variant | Old filename | Clean file | Bytes | SHA-256 | Seconds | FPS | Resolution / codec | Frames | Hand suggestion (s); usable / detector |
|---|---|---|---:|---|---:|---:|---|---:|---|
| black_variant_01 | black(1).mov | 03_noir.mp4 | 468737 | `1bd47cf3541ac3d10c43bed11840589a3706a8e984b1717abe2d5c0bd291af2c` | 4.171 | 23.976 | 720×720 / h264 | 100 | 1.13–3.34; 48/100 |
| blue_variant_01 | Bleu.mov | 08_bleu_1.mp4 | 388388 | `a06d085253114987bdd4e33851060664652ac41cd5b9f39348cb7430f790878a` | 3.670 | 23.976 | 720×720 / h264 | 88 | 1.04–2.54; 35/88 |
| blue_variant_02 | Bleu-2.mov | 09_bleu_2.mp4 | 277497 | `662a5765d4c0fe4a5360a186ea3bdbd9334473ba041c6d0a4ebd6d7bf71fade3` | 2.586 | 23.976 | 720×720 / h264 | 62 | 0.42–1.50; 24/62 |
| brown_variant_01 | Brown.mov | 07_marron.mp4 | 403196 | `c312b5d4d05263e1ee985769991bcc721130d9409b3776937f18ca9029ab4e92` | 4.171 | 23.976 | 720×720 / h264 | 100 | 0.83–3.29; 59/100 |
| green_variant_01 | Green.mov | 05_vert.mp4 | 358430 | `81e01862cd579a61c52cea889dbe067547c7dbaace85d1b06fdbc6c9e4d8be29` | 3.587 | 23.976 | 720×720 / h264 | 86 | 0.54–2.46; 40/86 |
| orange_variant_01 | Orange.mov | 10_orange.mp4 | 425637 | `2e645eba0d3726936713fa31530e6463f7ebae2b95fa60b292597f052526ad0a` | 3.170 | 23.976 | 720×720 / h264 | 76 | 0.75–2.17; 33/76 |
| pink_variant_01 | Pink.mov | 06_rose.mp4 | 351527 | `0838580ae80da6cdc0dbbcb7378622602d6a6a7a4591aa7cd5462da4f9c6954a` | 3.128 | 23.976 | 720×720 / h264 | 75 | 0.33–2.13; 43/75 |
| red_variant_01 | Red.mov | 04_rouge.mp4 | 367018 | `6e3a68e26818b5ffbc270d974e6c2ad13ce21fda56f17a7fba967bd40836626e` | 3.378 | 23.976 | 720×720 / h264 | 81 | 0.58–2.29; 40/81 |
| white_variant_01 | White.mov | 02_blanc.mp4 | 300461 | `602a872e499876a4bdaaef060599f4d035ae539d3a4d34874868bdc8b8bbfcab` | 3.086 | 23.976 | 720×720 / h264 | 74 | 0.83–2.59; 40/74 |
| yellow_variant_01 | yellow.mov | 01_jaune.mp4 | 287963 | `9b7a3782fa44b656ef347cb0497d9863864715356c10a557ab2f5bfcd097d826` | 2.961 | 23.976 | 720×720 / h264 | 71 | 0.33–2.09; 43/71 |

## Dataset and features

The active `ml/data/colors_v1/source_v1/manifest.json` fingerprint is `634b7acde5d19f5c5d49a7ecd110aacda4cfa0b0a3715b37c36b0d1a56b1ea90`. The previous manifest fingerprint was `7b8c4a6c6f6b2084676b63328f5504793fa094ad9c43982eb4f476efa061220e`; its manifest, CSV and checksums are preserved under `ml/data/colors_v1/history/source-v1-before-cleaning/`. The active CSV and SHA256SUMS describe only the cleaned files. The earlier replacement inventory remains a historical working note, not an active manifest. Both blue variants map to blue.

All ten files were reprocessed with the existing MediaPipe VIDEO contract into `ml/data/colors_v1/features_clean_v2/`; tensors have shape 60×75×3 and masks 60×75. Each feature embeds its source SHA-256. The old `features_v1/` remains historical; fitting the active manifest with it fails with `feature provenance does not match manifest`. Preprocessing used entire clips, not approved boundaries.

The refreshed private packet is `ml/data/colors_v1/review_phase3/index.html`. Source-hash query strings distinguish cached previews, and the former packet is retained under `ml/data/colors_v1/history/review_phase3-before-cleaning/`. All ten technical and linguistic statuses are pending. A review-generator seek-to-EOF issue discovered on the cleaned clips was fixed by seeking to valid frame indices.

## Training and runtime

The current template package `artifacts/colors_v1/experimental/template-clean-v2.npz` loaded all ten source-bound tensors. A separate one-epoch compatibility smoke run in `artifacts/colors_v1/experimental/gru-smoke-clean-v2/` exported ONNX; its training report records the current fingerprint and maximum PyTorch/ONNX error 8.940696716308594e-08 on its smoke input. This is in-sample only, uncalibrated, and not a measure of recognition accuracy. It was not registered or promoted.

The existing `template-v1.npz`, `gru-smoke-v1/checkpoint.pt`, `gru-smoke-v1/model.onnx` and `registry-gru-smoke-v1.json` retain the previous dataset fingerprint `7b8c4a6c6f6b2084676b63328f5504793fa094ad9c43982eb4f476efa061220e`. The local diagnostic configuration still points to this historical model, and the registry identifies it as not trained on the cleaned replacements. No frontend source-video assets or camera/API contracts required alteration. No runtime restart or deployment was performed.

## Validation and remaining gates

Dataset validation reported ten records, nine classes, ten variants, all files decoding, no errors and ten pending reviews. `shasum -a 256 -c SHA256SUMS.txt` passed all ten files. A direct feature check verified dimensions, masks, source hashes, review bindings and rejection of the historical features against the new manifest.

Full source/performer rights and consent, technical segmentation, linguistic review, identity/lineage, camera-to-video feature parity, independent signer-disjoint evaluation and unknown-sign calibration remain unresolved. The smoke artifacts are not production-ready. Because the standard `make test-all` runs a frontend build, it was run with a temporary Makefile override for `test-frontend` that executes unit tests and lint but omits the build. All other targets retain their normal recipes; see the final task report for the command and results.

The no-build `make test-all` run passed: architecture 14, API 81, inference 33, ML 53, speech 9, frontend unit 54, Playwright 8 passed / 1 skipped; Ruff, MyPy and frontend lint passed. The skipped Playwright case requires a validated fake-camera video. Exact invocation: `make test-all 'MAKE=make -f Makefile -f /tmp/opensigne-no-rebuild.mk'`; the temporary override runs `npm test -- --run` and `npm run lint` in place of the normal frontend test recipe, omitting its `npm run build` step.
