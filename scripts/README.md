# Funnel scripts

## Step 1 (current)

Filter `app_landing_launch` where `extra.utmSource` and `extra.invitationCode` have non-empty values, then dedupe by `extra.invitationCode`.

```bash
python3 scripts/funnel.py step1 \
  --input data/app_landing_launch.json \
  --out-csv out/step1_app_landing_launch_utmSource_dedup.csv \
  --out-summary out/step1_app_landing_launch_utmSource_dedup.summary.json
```

The script prints the same summary JSON to stdout.

## Step 2 (current)

Filter `pwa_cta_click` where `extra.utmSource` and `extra.invitationCode` have non-empty values, then dedupe by `extra.invitationCode`.

```bash
python3 scripts/funnel.py step2 \
  --input data/pwa_cta_click.json \
  --out-csv out/step2_pwa_cta_click_utmSource_dedup.csv \
  --out-summary out/step2_pwa_cta_click_utmSource_dedup.summary.json
```

## Step 3 (current)

Filter `guide_page_view` where `extra.invitation_code` has a non-empty value, then dedupe by `user_id`.

```bash
python3 scripts/funnel.py step3 \
  --input data/guide_page_view.json \
  --out-csv out/step3_guide_page_view_dedup_user_id.csv \
  --out-summary out/step3_guide_page_view_dedup_user_id.summary.json
```

## Step 4 (current)

Use `guide_bind` and compute 3 metrics, each independently deduped by `user_id`:

- `extra.click_google_bind` (google bind click)
- `extra.click_apple_bind` (apple bind click)
- `extra.bind_result` (dedupe `user_id` per result value)

```bash
python3 scripts/funnel.py step4 \
  --input data/guide_bind.json \
  --out-csv out/step4_guide_bind_dedup_user_id.csv \
  --out-summary out/step4_guide_bind_dedup_user_id.summary.json
```

## Step 5 (current)

Filter `guide_result` and count UV deduped by `user_id`.

```bash
python3 scripts/funnel.py step5 \
  --input data/guide_result.json \
  --out-csv out/step5_guide_result_dedup_user_id.csv \
  --out-summary out/step5_guide_result_dedup_user_id.summary.json
```

## Extending for later funnel steps

Add a new subcommand in `scripts/funnel.py` and reuse:

- `_load_json_any()` / `_iter_records()` for reading exports
- `_parse_extra()` to decode the `extra` JSON string
- the same join key (`device_id`) if later steps need to attribute downstream events back to step 1
