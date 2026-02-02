#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import json
import os
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _parse_tm(value: Any) -> Optional[dt.datetime]:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _parse_date(value: Any) -> Optional[dt.date]:
    if value is None:
        return None
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.datetime):
        return value.date()
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _in_date_range(tm_value: Any, date_start: Optional[dt.date], date_end: Optional[dt.date]) -> bool:
    if date_start is None and date_end is None:
        return True
    tm_dt = _parse_tm(tm_value)
    if tm_dt is None:
        return False
    d = tm_dt.date()
    if date_start is not None and d < date_start:
        return False
    if date_end is not None and d > date_end:
        return False
    return True


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _is_valid_utm_source(value: Any) -> bool:
    # Expected format like: xxx_to_yyy
    return _is_nonempty_str(value) and "_to_" in value.strip()


def _is_truthy_flag(value: Any) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        s = value.strip().lower()
        return s in {"true", "1", "yes", "y", "t", "on"}
    return False


def _load_json_any(path: str) -> Any:
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: JSON Lines
        items = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
        return items


def _parse_extra(extra: Any) -> Dict[str, Any]:
    if extra is None:
        return {}
    if isinstance(extra, dict):
        return extra
    if isinstance(extra, str):
        extra = extra.strip()
        if not extra:
            return {}
        try:
            parsed = json.loads(extra)
            return parsed if isinstance(parsed, dict) else {"_value": parsed}
        except json.JSONDecodeError:
            return {"_raw": extra}
    return {"_value": extra}


def _iter_records(json_data: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(json_data, list):
        for item in json_data:
            if isinstance(item, dict):
                yield item
        return
    if isinstance(json_data, dict):
        # Some exports may wrap records under a key; try common ones.
        for key in ("data", "rows", "records", "items", "list"):
            value = json_data.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
                return
    raise SystemExit("Unsupported JSON format: expected a list of objects (or a dict wrapping a list).")


def step1_app_landing_launch(
    input_path: str,
    output_csv: str,
    output_summary_json: str,
    date_start: Optional[dt.date],
    date_end: Optional[dt.date],
) -> None:
    data = _load_json_any(input_path)
    records = list(_iter_records(data))

    raw_total = len(records)
    event_counts = Counter(r.get("event") for r in records)

    filtered_rows: List[Dict[str, Any]] = []
    utm_missing = 0
    utm_empty = 0
    utm_invalid_format = 0
    invitation_code_missing = 0
    invitation_code_empty = 0
    date_filtered_out = 0
    utm_invalid_values = Counter()

    for r in records:
        if r.get("event") != "app_landing_launch":
            continue
        if not _in_date_range(r.get("tm"), date_start, date_end):
            date_filtered_out += 1
            continue

        extra = _parse_extra(r.get("extra"))
        utm = extra.get("utmSource")
        if "utmSource" not in extra:
            utm_missing += 1
            continue
        if not _is_nonempty_str(utm):
            utm_empty += 1
            continue
        if not _is_valid_utm_source(utm):
            utm_invalid_format += 1
            utm_invalid_values[str(utm).strip()] += 1
            continue

        utm_str = str(utm).strip()

        raw_invitation_code = extra.get("invitationCode")
        if "invitationCode" not in extra:
            invitation_code_missing += 1
            continue
        invitation_code_str = str(raw_invitation_code).strip() if raw_invitation_code is not None else ""
        if not invitation_code_str:
            invitation_code_empty += 1
            continue

        raw_device_id = extra.get("device_id")
        device_id_str = str(raw_device_id).strip() if raw_device_id is not None else ""

        filtered_rows.append(
            {
                "tm": r.get("tm", ""),
                "to_date": r.get("to_date", ""),
                "user_id": r.get("user_id", ""),
                "platform": r.get("platform", ""),
                "pkg": r.get("pkg", ""),
                "ver": r.get("ver", ""),
                "ip_addr": r.get("ip_addr", ""),
                "model": r.get("model", ""),
                "android_id": r.get("android_id", ""),
                "nickname": r.get("nickname", ""),
                "device_id": device_id_str,
                "utmSource": utm_str,
                "device_model": extra.get("device_model", ""),
                "pwa_installed": extra.get("pwa_installed", ""),
                "new_user": extra.get("new_user", ""),
                "fbclid": extra.get("fbclid", ""),
                "invitationCode": invitation_code_str,
            }
        )

    # Dedupe by invitationCode: keep earliest tm (ties: first encountered).
    filtered_rows.sort(key=lambda r: (_parse_tm(r.get("tm")) or dt.datetime.max))
    deduped: Dict[str, Dict[str, Any]] = {}
    duplicates = 0
    for row in filtered_rows:
        key = row["invitationCode"]
        if key in deduped:
            duplicates += 1
            continue
        deduped[key] = row

    deduped_rows = list(deduped.values())

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_summary_json) or ".", exist_ok=True)

    fieldnames = [
        "invitationCode",
        "utmSource",
        "tm",
        "to_date",
        "platform",
        "device_model",
        "pwa_installed",
        "new_user",
        "device_id",
        "fbclid",
        "user_id",
        "pkg",
        "ver",
        "ip_addr",
        "model",
        "android_id",
        "nickname",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped_rows)

    by_utm = Counter(r["utmSource"] for r in deduped_rows)
    by_platform = Counter(r.get("platform", "") for r in deduped_rows)
    by_device_model = Counter(r.get("device_model", "") for r in deduped_rows)

    summary = {
        "input_path": input_path,
        "output_csv": output_csv,
        "raw_total_rows": raw_total,
        "raw_event_counts": dict(event_counts),
        "stage": "step1",
        "filter": {
            "event": "app_landing_launch",
            "extra.utmSource": "non-empty string",
            "extra.invitationCode": "non-empty string",
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None,
        },
        "raw_app_landing_launch_rows": event_counts.get("app_landing_launch", 0),
        "date_filtered_out_rows": date_filtered_out,
        "utmSource_missing_in_extra": utm_missing,
        "utmSource_empty_or_blank": utm_empty,
        "utmSource_invalid_format": utm_invalid_format,
        "utmSource_invalid_values_top": dict(utm_invalid_values.most_common(20)),
        "invitationCode_missing_in_extra": invitation_code_missing,
        "invitationCode_empty_or_blank": invitation_code_empty,
        "kept_after_filter": len(filtered_rows),
        "dedupe_key": "invitationCode",
        "deduped_unique_invitationCode": len(deduped_rows),
        "dedupe_dropped_rows": duplicates,
        "breakdown": {
            "by_utmSource": dict(by_utm),
            "by_platform": dict(by_platform),
            "by_device_model": dict(by_device_model),
        },
    }

    with open(output_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def step2_pwa_cta_click(
    input_path: str,
    output_csv: str,
    output_summary_json: str,
    date_start: Optional[dt.date],
    date_end: Optional[dt.date],
) -> None:
    data = _load_json_any(input_path)
    records = list(_iter_records(data))

    raw_total = len(records)
    event_counts = Counter(r.get("event") for r in records)

    filtered_rows: List[Dict[str, Any]] = []
    utm_missing = 0
    utm_empty = 0
    utm_invalid_format = 0
    invitation_code_missing = 0
    invitation_code_empty = 0
    date_filtered_out = 0
    utm_invalid_values = Counter()

    for r in records:
        if r.get("event") != "pwa_cta_click":
            continue
        if not _in_date_range(r.get("tm"), date_start, date_end):
            date_filtered_out += 1
            continue

        extra = _parse_extra(r.get("extra"))
        utm = extra.get("utmSource")
        if "utmSource" not in extra:
            utm_missing += 1
            continue
        if not _is_nonempty_str(utm):
            utm_empty += 1
            continue
        if not _is_valid_utm_source(utm):
            utm_invalid_format += 1
            utm_invalid_values[str(utm).strip()] += 1
            continue

        utm_str = str(utm).strip()

        raw_invitation_code = extra.get("invitationCode")
        if "invitationCode" not in extra:
            invitation_code_missing += 1
            continue
        invitation_code_str = str(raw_invitation_code).strip() if raw_invitation_code is not None else ""
        if not invitation_code_str:
            invitation_code_empty += 1
            continue

        raw_device_id = extra.get("device_id")
        device_id_str = str(raw_device_id).strip() if raw_device_id is not None else ""

        filtered_rows.append(
            {
                "tm": r.get("tm", ""),
                "to_date": r.get("to_date", ""),
                "user_id": r.get("user_id", ""),
                "platform": r.get("platform", ""),
                "pkg": r.get("pkg", ""),
                "ver": r.get("ver", ""),
                "ip_addr": r.get("ip_addr", ""),
                "model": r.get("model", ""),
                "android_id": r.get("android_id", ""),
                "nickname": r.get("nickname", ""),
                "device_id": device_id_str,
                "utmSource": utm_str,
                "button_name": extra.get("button_name", ""),
                "device_model": extra.get("device_model", ""),
                "pwa_installed": extra.get("pwa_installed", ""),
                "new_user": extra.get("new_user", ""),
                "fbclid": extra.get("fbclid", ""),
                "invitationCode": invitation_code_str,
            }
        )

    # Dedupe by invitationCode: keep earliest tm (ties: first encountered).
    filtered_rows.sort(key=lambda r: (_parse_tm(r.get("tm")) or dt.datetime.max))
    deduped: Dict[str, Dict[str, Any]] = {}
    duplicates = 0
    for row in filtered_rows:
        key = row["invitationCode"]
        if key in deduped:
            duplicates += 1
            continue
        deduped[key] = row

    deduped_rows = list(deduped.values())

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_summary_json) or ".", exist_ok=True)

    fieldnames = [
        "invitationCode",
        "utmSource",
        "button_name",
        "tm",
        "to_date",
        "platform",
        "device_model",
        "pwa_installed",
        "new_user",
        "device_id",
        "fbclid",
        "user_id",
        "pkg",
        "ver",
        "ip_addr",
        "model",
        "android_id",
        "nickname",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped_rows)

    by_utm = Counter(r["utmSource"] for r in deduped_rows)
    by_platform = Counter(r.get("platform", "") for r in deduped_rows)
    by_device_model = Counter(r.get("device_model", "") for r in deduped_rows)
    by_button_name = Counter(r.get("button_name", "") for r in deduped_rows)

    summary = {
        "input_path": input_path,
        "output_csv": output_csv,
        "raw_total_rows": raw_total,
        "raw_event_counts": dict(event_counts),
        "stage": "step2",
        "filter": {
            "event": "pwa_cta_click",
            "extra.utmSource": "non-empty string",
            "extra.invitationCode": "non-empty string",
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None,
        },
        "raw_pwa_cta_click_rows": event_counts.get("pwa_cta_click", 0),
        "date_filtered_out_rows": date_filtered_out,
        "utmSource_missing_in_extra": utm_missing,
        "utmSource_empty_or_blank": utm_empty,
        "utmSource_invalid_format": utm_invalid_format,
        "utmSource_invalid_values_top": dict(utm_invalid_values.most_common(20)),
        "invitationCode_missing_in_extra": invitation_code_missing,
        "invitationCode_empty_or_blank": invitation_code_empty,
        "kept_after_filter": len(filtered_rows),
        "dedupe_key": "invitationCode",
        "deduped_unique_invitationCode": len(deduped_rows),
        "dedupe_dropped_rows": duplicates,
        "breakdown": {
            "by_utmSource": dict(by_utm),
            "by_platform": dict(by_platform),
            "by_device_model": dict(by_device_model),
            "by_button_name": dict(by_button_name),
        },
    }

    with open(output_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def step3_guide_page_view(
    input_path: str,
    output_csv: str,
    output_summary_json: str,
    date_start: Optional[dt.date],
    date_end: Optional[dt.date],
) -> None:
    data = _load_json_any(input_path)
    records = list(_iter_records(data))

    raw_total = len(records)
    event_counts = Counter(r.get("event") for r in records)

    filtered_rows: List[Dict[str, Any]] = []
    invitation_code_missing = 0
    invitation_code_empty = 0
    invitation_code_nonempty_rows = 0
    date_filtered_out = 0

    for r in records:
        if r.get("event") != "guide_page_view":
            continue
        if not _in_date_range(r.get("tm"), date_start, date_end):
            date_filtered_out += 1
            continue

        user_id = r.get("user_id")
        user_id_str = str(user_id).strip() if user_id is not None else ""
        if not user_id_str:
            continue

        extra = _parse_extra(r.get("extra"))
        invitation_code = extra.get("invitation_code")
        if "invitation_code" not in extra:
            invitation_code_missing += 1
            continue
        elif not _is_nonempty_str(invitation_code):
            invitation_code_empty += 1
            continue

        invitation_code_nonempty_rows += 1

        invitation_code_str = invitation_code.strip() if isinstance(invitation_code, str) else (invitation_code or "")
        filtered_rows.append(
            {
                "tm": r.get("tm", ""),
                "to_date": r.get("to_date", ""),
                "user_id": user_id_str,
                "platform": r.get("platform", ""),
                "pkg": r.get("pkg", ""),
                "ver": r.get("ver", ""),
                "ip_addr": r.get("ip_addr", ""),
                "model": r.get("model", ""),
                "android_id": r.get("android_id", ""),
                "nickname": r.get("nickname", ""),
                "invitation_code": invitation_code_str,
                "extra_userId": extra.get("userId", ""),
            }
        )

    filtered_rows.sort(key=lambda r: (_parse_tm(r.get("tm")) or dt.datetime.max))
    deduped: Dict[str, Dict[str, Any]] = {}
    duplicates = 0
    for row in filtered_rows:
        key = row["user_id"]
        if key in deduped:
            duplicates += 1
            continue
        deduped[key] = row

    deduped_rows = list(deduped.values())

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_summary_json) or ".", exist_ok=True)

    fieldnames = [
        "user_id",
        "tm",
        "to_date",
        "platform",
        "invitation_code",
        "extra_userId",
        "pkg",
        "ver",
        "ip_addr",
        "model",
        "android_id",
        "nickname",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped_rows)

    by_platform = Counter(r.get("platform", "") for r in deduped_rows)
    invitation_code_nonempty = sum(1 for r in deduped_rows if _is_nonempty_str(r.get("invitation_code")))

    summary = {
        "input_path": input_path,
        "output_csv": output_csv,
        "raw_total_rows": raw_total,
        "raw_event_counts": dict(event_counts),
        "stage": "step3",
        "filter": {
            "event": "guide_page_view",
            "extra.invitation_code": "non-empty string",
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None,
        },
        "raw_guide_page_view_rows": event_counts.get("guide_page_view", 0),
        "date_filtered_out_rows": date_filtered_out,
        "invitation_code_missing_in_extra": invitation_code_missing,
        "invitation_code_empty_or_blank": invitation_code_empty,
        "invitation_code_nonempty_rows": invitation_code_nonempty_rows,
        "kept_after_filter": len(filtered_rows),
        "dedupe_key": "user_id",
        "deduped_unique_user_id": len(deduped_rows),
        "dedupe_dropped_rows": duplicates,
        "breakdown": {
            "by_platform": dict(by_platform),
            "invitation_code_nonempty_count": invitation_code_nonempty,
        },
    }

    with open(output_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def step4_guide_bind(
    input_path: str,
    output_csv: str,
    output_summary_json: str,
    date_start: Optional[dt.date],
    date_end: Optional[dt.date],
) -> None:
    data = _load_json_any(input_path)
    records = list(_iter_records(data))

    raw_total = len(records)
    event_counts = Counter(r.get("event") for r in records)

    google_click_users = set()
    apple_click_users = set()
    bind_result_users: Dict[str, set] = defaultdict(set)

    per_user: Dict[str, Dict[str, Any]] = {}
    bind_result_missing = 0
    bind_result_empty = 0
    google_click_present = 0
    apple_click_present = 0
    date_filtered_out = 0

    for r in records:
        if r.get("event") != "guide_bind":
            continue
        if not _in_date_range(r.get("tm"), date_start, date_end):
            date_filtered_out += 1
            continue

        user_id = r.get("user_id")
        user_id_str = str(user_id).strip() if user_id is not None else ""
        if not user_id_str:
            continue

        extra = _parse_extra(r.get("extra"))
        tm = r.get("tm", "")

        click_google_bind = extra.get("click_google_bind")
        click_apple_bind = extra.get("click_apple_bind")
        bind_result = extra.get("bind_result")

        if "click_google_bind" in extra:
            google_click_present += 1
        if "click_apple_bind" in extra:
            apple_click_present += 1

        if _is_truthy_flag(click_google_bind):
            google_click_users.add(user_id_str)
        if _is_truthy_flag(click_apple_bind):
            apple_click_users.add(user_id_str)

        if "bind_result" not in extra:
            bind_result_missing += 1
        else:
            if not _is_nonempty_str(bind_result):
                bind_result_empty += 1
            else:
                bind_result_users[bind_result.strip()].add(user_id_str)

        row = per_user.get(user_id_str)
        tm_dt = _parse_tm(tm)
        if row is None:
            per_user[user_id_str] = {
                "user_id": user_id_str,
                "first_tm": tm,
                "first_to_date": r.get("to_date", ""),
                "first_platform": r.get("platform", ""),
                "pkg": r.get("pkg", ""),
                "ver": r.get("ver", ""),
                "ip_addr": r.get("ip_addr", ""),
                "model": r.get("model", ""),
                "android_id": r.get("android_id", ""),
                "nickname": r.get("nickname", ""),
                "extra_userId": extra.get("userId", ""),
                "clicked_google_bind": False,
                "clicked_apple_bind": False,
                "bind_results": set(),
                "_first_tm_dt": tm_dt,
            }
            row = per_user[user_id_str]
        else:
            existing_tm_dt = row.get("_first_tm_dt")
            if tm_dt is not None and (existing_tm_dt is None or tm_dt < existing_tm_dt):
                row["_first_tm_dt"] = tm_dt
                row["first_tm"] = tm
                row["first_to_date"] = r.get("to_date", "")
                row["first_platform"] = r.get("platform", "")
                row["pkg"] = r.get("pkg", "")
                row["ver"] = r.get("ver", "")
                row["ip_addr"] = r.get("ip_addr", "")
                row["model"] = r.get("model", "")
                row["android_id"] = r.get("android_id", "")
                row["nickname"] = r.get("nickname", "")
                row["extra_userId"] = extra.get("userId", "")

        if _is_truthy_flag(click_google_bind):
            row["clicked_google_bind"] = True
        if _is_truthy_flag(click_apple_bind):
            row["clicked_apple_bind"] = True
        if _is_nonempty_str(bind_result):
            row["bind_results"].add(bind_result.strip())

    # CSV: one row per user_id with aggregated flags.
    rows = list(per_user.values())
    rows.sort(key=lambda r: (r.get("_first_tm_dt") or dt.datetime.max, r.get("user_id", "")))

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_summary_json) or ".", exist_ok=True)

    fieldnames = [
        "user_id",
        "first_tm",
        "first_to_date",
        "first_platform",
        "clicked_google_bind",
        "clicked_apple_bind",
        "bind_results",
        "extra_userId",
        "pkg",
        "ver",
        "ip_addr",
        "model",
        "android_id",
        "nickname",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            out = dict(r)
            out.pop("_first_tm_dt", None)
            out["bind_results"] = ";".join(sorted(out.get("bind_results", set())))
            writer.writerow(out)

    bind_result_counts = {k: len(v) for k, v in sorted(bind_result_users.items(), key=lambda kv: (-len(kv[1]), kv[0]))}

    summary = {
        "input_path": input_path,
        "output_csv": output_csv,
        "raw_total_rows": raw_total,
        "raw_event_counts": dict(event_counts),
        "stage": "step4",
        "filter": {
            "event": "guide_bind",
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None,
        },
        "raw_guide_bind_rows": event_counts.get("guide_bind", 0),
        "date_filtered_out_rows": date_filtered_out,
        "dedupe": {
            "click_google_bind": {"dedupe_key": "user_id", "unique_user_id": len(google_click_users)},
            "click_apple_bind": {"dedupe_key": "user_id", "unique_user_id": len(apple_click_users)},
            "bind_result": {"dedupe_key": "user_id", "unique_user_id_by_value": bind_result_counts},
        },
        "extra_field_presence": {
            "click_google_bind_present_rows": google_click_present,
            "click_apple_bind_present_rows": apple_click_present,
            "bind_result_missing_in_extra_rows": bind_result_missing,
            "bind_result_empty_or_blank_rows": bind_result_empty,
        },
        "csv_rows_unique_user_id": len(rows),
    }

    with open(output_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def step5_guide_result(
    input_path: str,
    output_csv: str,
    output_summary_json: str,
    date_start: Optional[dt.date],
    date_end: Optional[dt.date],
) -> None:
    data = _load_json_any(input_path)
    records = list(_iter_records(data))

    raw_total = len(records)
    event_counts = Counter(r.get("event") for r in records)

    filtered_rows: List[Dict[str, Any]] = []
    guide_result_missing = 0
    guide_result_empty = 0
    date_filtered_out = 0

    for r in records:
        if r.get("event") != "guide_result":
            continue
        if not _in_date_range(r.get("tm"), date_start, date_end):
            date_filtered_out += 1
            continue

        user_id = r.get("user_id")
        user_id_str = str(user_id).strip() if user_id is not None else ""
        if not user_id_str:
            continue

        extra = _parse_extra(r.get("extra"))
        guide_result = extra.get("guide_result")
        if "guide_result" not in extra:
            guide_result_missing += 1
        elif not _is_nonempty_str(guide_result):
            guide_result_empty += 1

        guide_result_str = guide_result.strip() if isinstance(guide_result, str) else (guide_result or "")
        filtered_rows.append(
            {
                "user_id": user_id_str,
                "tm": r.get("tm", ""),
                "to_date": r.get("to_date", ""),
                "platform": r.get("platform", ""),
                "guide_result": guide_result_str,
                "extra_userId": extra.get("userId", ""),
                "pkg": r.get("pkg", ""),
                "ver": r.get("ver", ""),
                "ip_addr": r.get("ip_addr", ""),
                "model": r.get("model", ""),
                "android_id": r.get("android_id", ""),
                "nickname": r.get("nickname", ""),
            }
        )

    # Dedupe by user_id: keep earliest tm.
    filtered_rows.sort(key=lambda r: (_parse_tm(r.get("tm")) or dt.datetime.max))
    deduped: Dict[str, Dict[str, Any]] = {}
    duplicates = 0
    for row in filtered_rows:
        key = row["user_id"]
        if key in deduped:
            duplicates += 1
            continue
        deduped[key] = row

    deduped_rows = list(deduped.values())

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_summary_json) or ".", exist_ok=True)

    fieldnames = [
        "user_id",
        "tm",
        "to_date",
        "platform",
        "guide_result",
        "extra_userId",
        "pkg",
        "ver",
        "ip_addr",
        "model",
        "android_id",
        "nickname",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped_rows)

    by_platform = Counter(r.get("platform", "") for r in deduped_rows)
    by_result = Counter(r.get("guide_result", "") for r in deduped_rows if _is_nonempty_str(r.get("guide_result")))

    summary = {
        "input_path": input_path,
        "output_csv": output_csv,
        "raw_total_rows": raw_total,
        "raw_event_counts": dict(event_counts),
        "stage": "step5",
        "filter": {
            "event": "guide_result",
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None,
        },
        "raw_guide_result_rows": event_counts.get("guide_result", 0),
        "date_filtered_out_rows": date_filtered_out,
        "guide_result_missing_in_extra": guide_result_missing,
        "guide_result_empty_or_blank": guide_result_empty,
        "kept_after_filter": len(filtered_rows),
        "dedupe_key": "user_id",
        "uv_unique_user_id": len(deduped_rows),
        "dedupe_dropped_rows": duplicates,
        "breakdown": {"by_platform": dict(by_platform), "by_guide_result": dict(by_result)},
    }

    with open(output_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="funnel",
        description="Funnel report helpers for local event-log JSON exports.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    step1 = sub.add_parser(
        "step1",
        help="Step 1: app_landing_launch where extra.utmSource+invitationCode have value, dedupe by invitationCode.",
    )
    step1.add_argument(
        "--input",
        default="data/app_landing_launch.json",
        help="Input JSON export (default: data/app_landing_launch.json)",
    )
    step1.add_argument(
        "--out-csv",
        default="out/step1_app_landing_launch_utmSource_dedup.csv",
        help="Output CSV path (default: out/step1_app_landing_launch_utmSource_dedup.csv)",
    )
    step1.add_argument(
        "--out-summary",
        default="out/step1_app_landing_launch_utmSource_dedup.summary.json",
        help="Output summary JSON path (default: out/step1_app_landing_launch_utmSource_dedup.summary.json)",
    )
    step1.add_argument("--date-start", default=None, help="Filter by tm date >= YYYY-MM-DD (optional)")
    step1.add_argument("--date-end", default=None, help="Filter by tm date <= YYYY-MM-DD (optional)")

    step2 = sub.add_parser(
        "step2",
        help="Step 2: pwa_cta_click where extra.utmSource+invitationCode have value, dedupe by invitationCode.",
    )
    step2.add_argument(
        "--input",
        default="data/pwa_cta_click.json",
        help="Input JSON export (default: data/pwa_cta_click.json)",
    )
    step2.add_argument(
        "--out-csv",
        default="out/step2_pwa_cta_click_utmSource_dedup.csv",
        help="Output CSV path (default: out/step2_pwa_cta_click_utmSource_dedup.csv)",
    )
    step2.add_argument(
        "--out-summary",
        default="out/step2_pwa_cta_click_utmSource_dedup.summary.json",
        help="Output summary JSON path (default: out/step2_pwa_cta_click_utmSource_dedup.summary.json)",
    )
    step2.add_argument("--date-start", default=None, help="Filter by tm date >= YYYY-MM-DD (optional)")
    step2.add_argument("--date-end", default=None, help="Filter by tm date <= YYYY-MM-DD (optional)")

    step3 = sub.add_parser(
        "step3",
        help="Step 3: guide_page_view dedupe by user_id.",
    )
    step3.add_argument(
        "--input",
        default="data/guide_page_view.json",
        help="Input JSON export (default: data/guide_page_view.json)",
    )
    step3.add_argument(
        "--out-csv",
        default="out/step3_guide_page_view_dedup_user_id.csv",
        help="Output CSV path (default: out/step3_guide_page_view_dedup_user_id.csv)",
    )
    step3.add_argument(
        "--out-summary",
        default="out/step3_guide_page_view_dedup_user_id.summary.json",
        help="Output summary JSON path (default: out/step3_guide_page_view_dedup_user_id.summary.json)",
    )
    step3.add_argument("--date-start", default=None, help="Filter by tm date >= YYYY-MM-DD (optional)")
    step3.add_argument("--date-end", default=None, help="Filter by tm date <= YYYY-MM-DD (optional)")

    step4 = sub.add_parser(
        "step4",
        help="Step 4: guide_bind (dedupe user_id separately for clicks and bind_result).",
    )
    step4.add_argument(
        "--input",
        default="data/guide_bind.json",
        help="Input JSON export (default: data/guide_bind.json)",
    )
    step4.add_argument(
        "--out-csv",
        default="out/step4_guide_bind_dedup_user_id.csv",
        help="Output CSV path (default: out/step4_guide_bind_dedup_user_id.csv)",
    )
    step4.add_argument(
        "--out-summary",
        default="out/step4_guide_bind_dedup_user_id.summary.json",
        help="Output summary JSON path (default: out/step4_guide_bind_dedup_user_id.summary.json)",
    )
    step4.add_argument("--date-start", default=None, help="Filter by tm date >= YYYY-MM-DD (optional)")
    step4.add_argument("--date-end", default=None, help="Filter by tm date <= YYYY-MM-DD (optional)")

    step5 = sub.add_parser(
        "step5",
        help="Step 5: guide_result dedupe UV by user_id.",
    )
    step5.add_argument(
        "--input",
        default="data/guide_result.json",
        help="Input JSON export (default: data/guide_result.json)",
    )
    step5.add_argument(
        "--out-csv",
        default="out/step5_guide_result_dedup_user_id.csv",
        help="Output CSV path (default: out/step5_guide_result_dedup_user_id.csv)",
    )
    step5.add_argument(
        "--out-summary",
        default="out/step5_guide_result_dedup_user_id.summary.json",
        help="Output summary JSON path (default: out/step5_guide_result_dedup_user_id.summary.json)",
    )
    step5.add_argument("--date-start", default=None, help="Filter by tm date >= YYYY-MM-DD (optional)")
    step5.add_argument("--date-end", default=None, help="Filter by tm date <= YYYY-MM-DD (optional)")

    args = parser.parse_args(argv)

    date_start = _parse_date(getattr(args, "date_start", None))
    date_end = _parse_date(getattr(args, "date_end", None))

    if args.cmd == "step1":
        step1_app_landing_launch(args.input, args.out_csv, args.out_summary, date_start, date_end)
        return
    if args.cmd == "step2":
        step2_pwa_cta_click(args.input, args.out_csv, args.out_summary, date_start, date_end)
        return
    if args.cmd == "step3":
        step3_guide_page_view(args.input, args.out_csv, args.out_summary, date_start, date_end)
        return
    if args.cmd == "step4":
        step4_guide_bind(args.input, args.out_csv, args.out_summary, date_start, date_end)
        return
    if args.cmd == "step5":
        step5_guide_result(args.input, args.out_csv, args.out_summary, date_start, date_end)
        return

    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
