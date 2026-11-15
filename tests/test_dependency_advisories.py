"""Known vulnerabilities and incomplete inventories must fail the CI merge gate."""

import io
import json
import runpy
import ssl
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from email.message import Message
from http.client import IncompleteRead
from pathlib import Path
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest
import yaml
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from packaging.requirements import Requirement

from scripts import check_dependency_advisories as audit

NOW = datetime(2026, 11, 12, tzinfo=UTC)
HASH = "a" * 64


def metadata(name="sample", version="1.0", rows=None):
    return {"info": {"name": name, "version": version}, "vulnerabilities": rows or []}


def raw(payload):
    return json.dumps(payload).encode()


def locks(root, first="sample==1.0", second="sample==1.0"):
    records = []
    for pin in (first, second):
        req = Requirement(pin)
        specs = list(req.specifier)
        value = specs[0].version if len(specs) == 1 and specs[0].operator == "==" else pin
        records.append((req.name, value, str(req.marker) if req.marker else ""))
    path = root / audit.LOCKS[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    text = 'version = 1\n[[package]]\nname = "smartguard-validation"\nversion = "0"\nsource = { virtual = "." }\n'
    for name, version, marker in records:
        text += ('[[package]]\nname = ' + json.dumps(name) + '\nversion = ' + json.dumps(version)
                 + '\nsource = { registry = "https://pypi.org/simple" }\n'
                 + 'resolution-markers = [' + json.dumps(marker) + ']\n'
                 + 'sdist = { url = "https://files.pythonhosted.org/packages/sample.tar.gz", hash = "sha256:'
                 + HASH + '", size = 1 }\n')
    path.write_text(text)


def test_real_lock_inventory_includes_all_host_platforms():
    counts, packages = audit.locked_packages(audit.ROOT)
    assert counts == {"ci/uv.lock": 149}
    assert len(packages) == 149
    assert ("homeassistant", "2026.11.0") in packages
    assert ("homeassistant", "2026.11.1") in packages
    assert ("pytest-homeassistant", "2026.11.0") in packages
    assert ("pytest-homeassistant", "2026.11.1") in packages
    assert any(name.startswith("pyobjc-") for name, _ in packages)
    assert any(name.startswith("winrt-") for name, _ in packages)


def test_foreign_markers_are_not_evaluated_and_only_identical_pairs_are_coalesced(tmp_path):
    locks(tmp_path, "Sample_Name[extra]==1.0; sys_platform == 'win32'",
          "sample-name==2.0; sys_platform == 'darwin'")
    counts, packages = audit.locked_packages(tmp_path)
    assert list(packages) == [("sample-name", "1.0"), ("sample-name", "2.0")]
    assert counts == {"ci/uv.lock": 2}
    locks(tmp_path)
    assert audit.locked_packages(tmp_path)[1] == {("sample", "1.0"): list(audit.LOCKS)}


def test_same_version_with_multiple_platform_markers_is_queried_once(tmp_path):
    locks(tmp_path, "sample==1.0; sys_platform == 'linux'", "sample==1.0; sys_platform == 'win32'")
    counts, packages = audit.locked_packages(tmp_path)
    assert counts[audit.LOCKS[0]] == 2
    assert packages == {("sample", "1.0"): list(audit.LOCKS)}


@pytest.mark.parametrize("pin", ["sample>=1.0", "sample==1.*", "sample @ https://example.invalid/a.whl"])
def test_unsafe_locks_fail_before_a_request(tmp_path, pin):
    locks(tmp_path, pin)
    with pytest.raises(audit.AuditError, match="invalid_lock"):
        audit.locked_packages(tmp_path)


@pytest.mark.parametrize("old,new", [
    ('version = 1', 'version = 2'),
    ('https://pypi.org/simple', 'https://example.invalid/simple'),
    ('source = { virtual = "." }', 'source = { editable = "." }'),
    ('sha256:' + HASH, 'sha256:bad'),
    ('name = "smartguard-validation"', 'name = "other-project"'),
    ('version = "1.0"', 'version = 123'),
])
def test_native_lock_unknown_sources_versions_and_hashes_fail_closed(tmp_path, old, new):
    locks(tmp_path)
    path=tmp_path / audit.LOCKS[0]
    assert old in path.read_text()
    path.write_text(path.read_text().replace(old,new))
    with pytest.raises(audit.AuditError):
        audit.locked_packages(tmp_path)


def test_missing_symlink_oversize_and_unbounded_inventories_are_rejected(tmp_path, monkeypatch):
    with pytest.raises(audit.AuditError, match="invalid_lock_file"):
        audit.locked_packages(tmp_path)
    locks(tmp_path)
    target = tmp_path / audit.LOCKS[0]
    other = target.with_name("other.lock")
    other.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(other)
    with pytest.raises(audit.AuditError, match="invalid_lock_file"):
        audit.locked_packages(tmp_path)
    target.unlink()
    locks(tmp_path)
    monkeypatch.setattr(audit, "MAX_LOCK_BYTES", 8)
    with pytest.raises(audit.AuditError, match="oversized_lock"):
        audit.locked_packages(tmp_path)
    monkeypatch.setattr(audit, "MAX_LOCK_BYTES", 4096)
    monkeypatch.setattr(audit, "MAX_PACKAGES", 1)
    locks(tmp_path, second="other==2.0")
    with pytest.raises(audit.AuditError, match="too_many_package_versions"):
        audit.locked_packages(tmp_path)


def test_exact_release_and_valid_withdrawals_only():
    rows = [{"id": "TEST-ACTIVE", "withdrawn": None},
            {"id": "TEST-WITHDRAWN", "withdrawn": "2026-11-01T12:00:00+01:00"}]
    result = audit.parse_metadata(raw(metadata("Sample", "1.0.0", rows)), "sample", "1.0", NOW)
    assert result == {"active_advisories": ["TEST-ACTIVE"], "withdrawn_advisories": ["TEST-WITHDRAWN"]}
    assert audit.parse_metadata(raw(metadata()), "sample", "1.0", NOW)["active_advisories"] == []


@pytest.mark.parametrize("payload", [
    [], None, {}, {"info": None}, {"info": {"name": "sample", "version": "1.0"}},
    {"info": {"name": "sample", "version": "1.0"}, "vulnerabilities": None},
    metadata("other"), metadata(version="2.0"), metadata(name="bad/name"), metadata(version="bad"),
    metadata(rows=[{}]), metadata(rows=[{"id": "TEST\nINJECTION"}]),
    metadata(rows=[{"id": "TEST-ONE"}, {"id": "TEST-ONE"}]),
    metadata(rows=[{"id": "TEST-ONE", "withdrawn": False}]),
    metadata(rows=[{"id": "TEST-ONE", "withdrawn": "yesterday"}]),
    metadata(rows=[{"id": "TEST-ONE", "withdrawn": "2026-11-01T00:00:00"}]),
    metadata(rows=[{"id": "TEST-ONE", "withdrawn": "2026-13-01T00:00:00Z"}]),
    metadata(rows=[{"id": "TEST-ONE", "withdrawn": "2027-01-01T00:00:00Z"}]),
])
def test_incomplete_mismatched_or_invalid_metadata_cannot_be_clean(payload):
    with pytest.raises(audit.AuditError):
        audit.parse_metadata(raw(payload), "sample", "1.0", NOW)


@pytest.mark.parametrize("payload", [b"{", b"\xff", b'{"info":{},"info":{}}', b'{"vulnerabilities":NaN}'])
def test_bad_or_ambiguous_json_fails_without_exporting_raw_content(payload):
    with pytest.raises(audit.AuditError, match="invalid_json"):
        audit.parse_metadata(payload, "sample", "1.0", NOW)


class Response:
    def __init__(self, body=None, *, url="https://pypi.org/pypi/sample/1.0/json", status=200,
                 content_type="application/json", encoding=None):
        self.body = raw(metadata()) if body is None else body
        self.url, self.status = url, status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        if encoding is not None:
            self.headers["Content-Encoding"] = encoding
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def geturl(self):
        return self.url

    def read(self, size):
        assert size == audit.MAX_BYTES + 1
        return self.body[:size]


@pytest.fixture
def transport(monkeypatch):
    opener = Mock()
    factory = Mock(return_value=opener)
    monkeypatch.setattr(audit, "build_opener", factory)
    sleep = Mock()
    monkeypatch.setattr(audit.time, "sleep", sleep)
    return opener, factory, sleep


def test_fixed_origin_verified_tls_no_auth_and_closed_bounded_response(transport):
    opener, factory, sleep = transport
    response = Response()
    opener.open.return_value = response
    assert audit.fetch_release("sample", "1.0", NOW)["active_advisories"] == []
    request = opener.open.call_args.args[0]
    assert request.full_url == "https://pypi.org/pypi/sample/1.0/json"
    assert request.get_header("Authorization") is None
    assert request.get_header("Cookie") is None
    assert opener.open.call_args.kwargs == {"timeout": 10}
    context = next(h._context for h in factory.call_args.args if hasattr(h, "_context"))
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    assert context.minimum_version >= ssl.TLSVersion.TLSv1_2
    assert any(isinstance(h, audit.NoRedirect) for h in factory.call_args.args)
    assert audit.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid") is None
    assert response.closed
    sleep.assert_not_called()


@pytest.mark.parametrize("trusted,hostname,expired", [
    (True, "pypi.org", False), (False, "pypi.org", False),
    (True, "wrong.invalid", False), (True, "pypi.org", True),
])
def test_real_tls_handshake_requires_trust_matching_hostname_and_valid_dates(
        transport, tmp_path, trusted, hostname, expired):
    """Exercise the actual audit context with local, ephemeral certificates."""
    opener, factory, _ = transport
    opener.open.return_value = Response()
    audit.fetch_release("sample", "1.0", NOW)
    context = next(h._context for h in factory.call_args.args if hasattr(h, "_context"))
    now = datetime.now(UTC)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "audit-test-ca")])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(days=3)).not_valid_after(now + timedelta(days=3))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, None, None), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .sign(ca_key, hashes.SHA256()))
    key = ec.generate_private_key(ec.SECP256R1())
    cert = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "pypi.org")]))
            .issuer_name(ca_name).public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=2))
            .not_valid_after(now + timedelta(days=-1 if expired else 1))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("pypi.org")]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.KeyUsage(True, False, False, False, False, False, False, None, None), critical=True)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))
    cert_path, key_path = tmp_path / "cert.pem", tmp_path / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(cert_path, key_path)
    if trusted:
        context.load_verify_locations(cadata=ca.public_bytes(serialization.Encoding.PEM).decode())
    client_in, client_out, server_in, server_out = (ssl.MemoryBIO() for _ in range(4))
    client = context.wrap_bio(client_in, client_out, server_hostname=hostname)
    server = server_context.wrap_bio(server_in, server_out, server_side=True)

    def handshake():
        completed = set()
        for _ in range(10):
            for peer in (client, server):
                try:
                    peer.do_handshake()
                    completed.add(peer)
                except ssl.SSLWantReadError:
                    pass
            server_in.write(client_out.read())
            client_in.write(server_out.read())
            if len(completed) == 2:
                return
        pytest.fail("local TLS handshake did not finish")

    if trusted and hostname == "pypi.org" and not expired:
        handshake()
    else:
        with pytest.raises(ssl.SSLCertVerificationError):
            handshake()


@pytest.mark.parametrize("first", [URLError("PRIVATE_TEST_ERROR"), TimeoutError("PRIVATE_TEST_ERROR"), IncompleteRead(b"PRIVATE_TEST_ERROR", 30)])
def test_transient_transport_has_exactly_one_retry(transport, first):
    opener, _, sleep = transport
    opener.open.side_effect = [first, Response()]
    assert audit.fetch_release("sample", "1.0", NOW)["active_advisories"] == []
    assert opener.open.call_count == 2
    sleep.assert_called_once_with(1)


def test_exhausted_transport_is_unknown_with_no_raw_error(transport):
    opener, _, sleep = transport
    opener.open.side_effect = URLError("PRIVATE_TEST_ERROR")
    with pytest.raises(audit.AuditError, match=r"^transport_error$"):
        audit.fetch_release("sample", "1.0", NOW)
    assert opener.open.call_count == 2
    sleep.assert_called_once_with(1)


@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_retryable_http_statuses_close_the_response_and_retry_once(transport, code):
    opener, _, sleep = transport
    body = io.BytesIO(b"PRIVATE_TEST_ERROR")
    error = HTTPError("https://pypi.org/", code, "PRIVATE_TEST_ERROR", Message(), body)
    opener.open.side_effect = [error, Response()]
    assert audit.fetch_release("sample", "1.0", NOW)["active_advisories"] == []
    assert body.closed and opener.open.call_count == 2
    sleep.assert_called_once_with(1)


@pytest.mark.parametrize("code,delay", [(404, None), (302, None), (429, "2"), (429, "bad"),
                                      (429, "²"), (429, "99999999999"), (503, "-1")])
def test_permanent_redirect_or_excessive_retry_after_does_not_loop(transport, code, delay):
    opener, _, sleep = transport
    headers = Message()
    if delay is not None:
        headers["Retry-After"] = delay
    opener.open.side_effect = HTTPError("https://pypi.org/", code, "PRIVATE_TEST_ERROR", headers, io.BytesIO())
    with pytest.raises(audit.AuditError, match=r"^http_error$"):
        audit.fetch_release("sample", "1.0", NOW)
    assert opener.open.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize("options", [{"status": 201}, {"url": "https://example.invalid"},
                                     {"content_type": "text/html"}, {"encoding": "gzip"},
                                     {"body": b"x" * (audit.MAX_BYTES + 1)}])
def test_unexpected_or_oversized_response_is_not_retried(transport, options):
    opener, _, sleep = transport
    response = Response(**options)
    opener.open.return_value = response
    with pytest.raises(audit.AuditError):
        audit.fetch_release("sample", "1.0", NOW)
    assert response.closed and opener.open.call_count == 1
    sleep.assert_not_called()


def test_complete_audit_keeps_active_withdrawn_and_unknown_results(tmp_path, monkeypatch):
    locks(tmp_path, second="other==2.0")
    def fetch(name, version, now):
        if name == "other":
            raise audit.AuditError("transport_error")
        return {"active_advisories": ["TEST-ACTIVE"], "withdrawn_advisories": ["TEST-WITHDRAWN"]}
    monkeypatch.setattr(audit, "fetch_release", fetch)
    report = audit.audit(tmp_path)
    assert report["status"] == "failed" and report["package_versions_checked"] == 2
    assert (report["active_advisories"], report["withdrawn_advisories"], report["unknown_results"]) == (1, 1, 1)
    assert datetime.fromisoformat(report["checked_at_utc"]).tzinfo is not None
    monkeypatch.setattr(audit, "fetch_release", lambda *args: {"active_advisories": [], "withdrawn_advisories": []})
    assert audit.audit(tmp_path)["status"] == "passed"


@pytest.mark.parametrize("unknown,active", [(False, False), (True, False), (False, True)])
@pytest.mark.parametrize("json_report", [False, True])
def test_cli_emits_report_and_fails_for_every_nonclean_result(tmp_path, monkeypatch, capsys, unknown, active, json_report):
    locks(tmp_path)
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    if unknown:
        def fetch(*args):
            raise audit.AuditError("invalid_json")
    else:
        def fetch(*args):
            return {"active_advisories": ["TEST-ACTIVE"] if active else [], "withdrawn_advisories": []}
    monkeypatch.setattr(audit, "fetch_release", fetch)
    assert audit.main(["--json"] if json_report else []) == int(unknown or active)
    output = capsys.readouterr()
    if json_report:
        result = json.loads(output.out)
        assert result["package_versions_checked"] == 1
        assert result["unknown_results"] == int(unknown)
        assert result["active_advisories"] == int(active)
    diagnostics = output.err if json_report else output.out
    assert "PRIVATE_TEST_ERROR" not in output.out + output.err
    assert ("UNKNOWN" in diagnostics) is unknown
    assert ("ACTIVE" in diagnostics) is active
    assert {path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()} == set(audit.LOCKS)


def test_bootstrap_and_audit_errors_never_export_paths(monkeypatch, capsys):
    def fail(*args):
        raise audit.SecurityBaselineError("PRIVATE_TEST_ERROR")
    monkeypatch.setattr(audit, "check_security", fail)
    assert audit.main([]) == 1
    assert "PRIVATE_TEST_ERROR" not in capsys.readouterr().err
    monkeypatch.setattr(audit, "check_security", lambda *args: {})
    monkeypatch.setattr(audit, "audit", Mock(side_effect=OSError("PRIVATE_TEST_ERROR")))
    assert audit.main(["--json"]) == 1
    output = capsys.readouterr()
    assert output.out == "" and "PRIVATE_TEST_ERROR" not in output.err


@pytest.mark.parametrize("flag", ["--ignore", "--index-url", "--skip-unknown", "--output"])
def test_no_ignore_or_alternate_registry_switch_exists(flag):
    with pytest.raises(SystemExit) as error:
        audit.main([flag, "sample"])
    assert error.value.code == 2


def test_cli_cannot_overwrite_files_or_follow_output_symlinks(tmp_path, monkeypatch):
    protected = tmp_path / "protected.json"
    protected.write_text("preserve")
    link = tmp_path / "report.json"
    link.symlink_to(protected)
    inspect = Mock()
    monkeypatch.setattr(audit, "audit", inspect)
    for argv in (["--output", str(protected)], ["--output", str(link)],
                 ["--output", str(tmp_path / ".." / "outside.json")],
                 ["--output=/etc/audit-test.json"], ["--json", str(protected)]):
        with pytest.raises(SystemExit) as error:
            audit.main(argv)
        assert error.value.code == 2
        assert protected.read_text() == "preserve"
        assert link.is_symlink()
    inspect.assert_not_called()


def test_module_entry_point_exposes_the_bounded_cli_without_network(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check_dependency_advisories", "--help"])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(Path(audit.__file__)), run_name="__main__")
    assert error.value.code == 0
    assert "--json" in capsys.readouterr().out


def test_ci_requires_advisories_and_daily_job_uses_identical_audit_steps():
    root = Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".github/workflows/validate.yml").read_text())
    daily = yaml.safe_load((root / ".github/workflows/dependency-audit.yml").read_text())
    gate = ci["jobs"]["quality"]
    assert gate["if"] == "${{ always() }}"
    assert set(gate["needs"]) == {"compatibility", "advisories", "codeql"}
    step = gate["steps"][0]
    for result in ("success", "failure", "skipped", "cancelled"):
        env = {name: "success" for name in ("COMPATIBILITY_RESULT", "ADVISORIES_RESULT", "CODEQL_RESULT")}
        env["ADVISORIES_RESULT"] = result
        assert (subprocess.run(["bash", "-c", step["run"]], env=env).returncode == 0) is (result == "success")
    assert step["env"]["ADVISORIES_RESULT"] == "${{ needs.advisories.result }}"
    assert ci["permissions"] == daily["permissions"] == {"contents": "read"}
    assert ci["jobs"]["advisories"]["steps"] == daily["jobs"]["advisories"]["steps"]
    assert ci["jobs"]["advisories"]["timeout-minutes"] == 15
    assert ci["jobs"]["compatibility"]["env"]["UV_OFFLINE"] == "true"
    trigger = daily.get("on", daily.get(True))
    assert set(trigger) == {"schedule", "workflow_dispatch"}
    assert trigger["schedule"] == [{"cron": "17 5 * * *"}]
    for step in ci["jobs"]["advisories"]["steps"]:
        if "uses" in step:
            assert len(step["uses"].split("@", 1)[1]) == 40
        assert "secrets" not in step
