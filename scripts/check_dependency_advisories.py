"""Fail closed on known vulnerabilities or unknown results for the universal CI lock and all fixture/platform selections."""

import argparse
import json
import re
import ssl
import sys
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from packaging.utils import InvalidName, canonicalize_name
from packaging.version import InvalidVersion, Version

from scripts.check_ci_security import SecurityBaselineError, check_security

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ("ci/uv.lock",)

MAX_BYTES = 2 * 1024 * 1024
MAX_LOCK_BYTES = 4 * 1024 * 1024
MAX_PACKAGES = 512
WORKERS = 8
REQUEST_TIMEOUT = 10
RETRY_DELAY = 1
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
ADVISORY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{1,127}")
RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})")


class AuditError(ValueError):
    """A fixed diagnostic code, never a provider body or exception string."""


class NoRedirect(HTTPRedirectHandler):
    """Never send a release query to another URL or host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def locked_packages(root: Path) -> tuple[dict[str, int], dict[tuple[str, str], list[str]]]:
    """Read every registry record; never evaluate away foreign platforms/groups."""
    counts, packages = {}, {}
    try:
        for name in LOCKS:
            path = root / name
            if path.is_symlink() or not path.is_file():
                raise AuditError("invalid_lock_file")
            with path.open("rb") as source:
                raw = source.read(MAX_LOCK_BYTES + 1)
            if len(raw) > MAX_LOCK_BYTES:
                raise AuditError("oversized_lock")
            lock = tomllib.loads(raw.decode("utf-8"))
            records = lock.get("package")
            if type(lock.get("version")) is not int or lock["version"] != 1:
                raise AuditError("invalid_lock")
            if not isinstance(records, list) or not records:
                raise AuditError("invalid_lock")
            if len(records) > MAX_PACKAGES + 1:
                raise AuditError("too_many_package_versions")
            count, virtual = 0, 0
            for record in records:
                if not isinstance(record, dict):
                    raise AuditError("invalid_lock")
                source = record.get("source")
                if source == {"virtual": "."}:
                    if record.get("name") != "smartguard-validation" or record.get("version") != "0":
                        raise AuditError("invalid_lock")
                    virtual += 1
                    continue
                if source != {"registry": "https://pypi.org/simple"}:
                    raise AuditError("invalid_lock")
                if not isinstance(record.get("name"), str) or not isinstance(record.get("version"), str):
                    raise AuditError("invalid_lock")
                key = (canonicalize_name(record["name"], validate=True), str(Version(record["version"])))
                artifacts = list(record.get("wheels", []))
                if "sdist" in record:
                    artifacts.append(record["sdist"])
                if not artifacts or any(not isinstance(item, dict)
                    or not isinstance(item.get("hash"), str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", item["hash"]) is None
                    for item in artifacts):
                    raise AuditError("invalid_lock")
                count += 1
                owners = packages.setdefault(key, [])
                if name not in owners:
                    owners.append(name)
                if len(packages) > MAX_PACKAGES:
                    raise AuditError("too_many_package_versions")
            if virtual != 1 or not count:
                raise AuditError("invalid_lock")
            counts[name] = count
    except (OSError, UnicodeError, ValueError, TypeError) as err:
        if isinstance(err, AuditError):
            raise
        raise AuditError("invalid_lock") from err
    return counts, dict(sorted(packages.items()))


def unique_object(pairs):
    """Ambiguous JSON objects cannot establish a clean security result."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise AuditError("duplicate_json_key")
        result[key] = value
    return result


def invalid_constant(value):
    raise AuditError("invalid_json_constant")


def parse_metadata(raw: bytes, name: str, version: str, now: datetime) -> dict:
    """Trust only matching release metadata and explicit, valid withdrawal dates."""
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                             parse_constant=invalid_constant)
    except (UnicodeError, ValueError, RecursionError) as err:
        raise AuditError("invalid_json") from err
    if not isinstance(payload, dict) or not isinstance(payload.get("info"), dict):
        raise AuditError("invalid_metadata")
    info = payload["info"]
    try:
        if (not isinstance(info.get("name"), str) or not isinstance(info.get("version"), str)
                or canonicalize_name(info["name"], validate=True) != name
                or Version(info["version"]) != Version(version)):
            raise AuditError("release_identity_mismatch")
    except (InvalidName, InvalidVersion) as err:
        raise AuditError("release_identity_mismatch") from err
    vulnerabilities = payload.get("vulnerabilities")
    if not isinstance(vulnerabilities, list):
        raise AuditError("missing_vulnerability_inventory")
    active, withdrawn, seen = [], [], set()
    for row in vulnerabilities:
        if (not isinstance(row, dict) or not isinstance(row.get("id"), str)
                or ADVISORY_ID.fullmatch(row["id"]) is None or row["id"] in seen):
            raise AuditError("invalid_advisory")
        identifier = row["id"]
        seen.add(identifier)
        if row.get("withdrawn") is None:
            active.append(identifier)
            continue
        timestamp = row["withdrawn"]
        if not isinstance(timestamp, str) or RFC3339.fullmatch(timestamp) is None:
            raise AuditError("invalid_withdrawal")
        try:
            date = datetime.fromisoformat(timestamp.replace("t", "T").replace("z", "+00:00").replace("Z", "+00:00"))
        except ValueError as err:
            raise AuditError("invalid_withdrawal") from err
        if date > now:
            raise AuditError("future_withdrawal")
        withdrawn.append(identifier)
    return {"active_advisories": sorted(active), "withdrawn_advisories": sorted(withdrawn)}


def fetch_release(name: str, version: str, now: datetime) -> dict:
    """Read fixed-host HTTPS JSON with byte/socket limits and one bounded retry."""
    url = f"https://pypi.org/pypi/{quote(name, safe='')}/{quote(version, safe='')}/json"
    # Keep the standard network/proxy policy and verified origin TLS. Add no
    # API authentication, cookies or redirects; never export proxy/error details.
    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    opener = build_opener(NoRedirect(), HTTPSHandler(context=context, check_hostname=True))
    request = Request(url, headers={"Accept": "application/json", "Accept-Encoding": "identity",
                                    "User-Agent": "ha-smartguard-test-lock-audit/1"})
    for attempt in range(2):
        try:
            with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
                if response.status != 200 or response.geturl() != url:
                    raise AuditError("unexpected_http_response")
                if (response.headers.get_content_type() != "application/json"
                        or response.headers.get("Content-Encoding", "identity").lower() != "identity"):
                    raise AuditError("unexpected_content_type_or_encoding")
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise AuditError("oversized_metadata")
            return parse_metadata(raw, name, version, now)
        except HTTPError as err:
            retry = attempt == 0 and err.code in RETRYABLE_STATUS
            delay = err.headers.get("Retry-After") if err.headers is not None else None
            err.close()
            if retry and (delay is None or (re.fullmatch(r"[0-9]{1,3}", delay) and int(delay) <= RETRY_DELAY)):
                time.sleep(RETRY_DELAY)
                continue
            raise AuditError("http_error") from err
        except (URLError, OSError, HTTPException) as err:
            if attempt == 0:
                time.sleep(RETRY_DELAY)
                continue
            raise AuditError("transport_error") from err
    raise AuditError("request_incomplete")


def audit(root: Path) -> dict:
    """Every selected pair yields either explicit advisories or an unknown result."""
    counts, packages = locked_packages(root)
    now = datetime.now(UTC)

    def check(pair):
        name, version = pair
        row = {"name": name, "version": version, "locks": packages[pair]}
        try:
            row.update(fetch_release(name, version, now))
        except AuditError as err:
            row["unknown"] = str(err)
        return row

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        rows = list(pool.map(check, packages))
    active = sum(len(row.get("active_advisories", [])) for row in rows)
    withdrawn = sum(len(row.get("withdrawn_advisories", [])) for row in rows)
    unknown = sum("unknown" in row for row in rows)
    return {"checked_at_utc": now.isoformat(), "source": "https://pypi.org/pypi/<project>/<version>/json",
            "status": "failed" if active or unknown else "passed", "lock_selections": counts,
            "package_versions_checked": len(rows), "active_advisories": active,
            "withdrawn_advisories": withdrawn, "unknown_results": unknown, "packages": rows}


def main(argv=None) -> int:
    """Emit bounded diagnostics and a machine-readable result; unknown is failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_report",
                        help="emit the report on stdout and diagnostics on stderr")
    args = parser.parse_args(argv)
    try:
        check_security("bootstrap")
        report = audit(ROOT)
    except (AuditError, SecurityBaselineError, OSError) as err:
        code = str(err) if isinstance(err, AuditError) else "security_baseline_or_audit_error"
        print(f"Test-lock advisory audit failed: {code}", file=sys.stderr)
        return 1
    if args.json_report:
        print(json.dumps(report, indent=2))
    diagnostics = sys.stderr if args.json_report else sys.stdout
    print(f"Test-lock advisory audit: {report['package_versions_checked']} package/version pairs; "
          f"{report['active_advisories']} active advisories; {report['unknown_results']} unknown results; "
          f"{report['withdrawn_advisories']} withdrawn advisories.", file=diagnostics)
    for row in report["packages"]:
        if "unknown" in row:
            print(f"UNKNOWN {row['name']}=={row['version']}: {row['unknown']}", file=diagnostics)
        elif row["active_advisories"]:
            print(f"ACTIVE {row['name']}=={row['version']}: " + ", ".join(row["active_advisories"]),
                  file=diagnostics)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
