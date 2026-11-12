import io
import socket
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch

import main
from core.completer import configure_completion, suggestions
from scanners.connection import check_connection
from scanners.cookies import check_cookie_security
from scanners.headers import check_security_headers, header_status
from scanners.paths import check_sensitive_path
from scanners.ports import check_ports
from scanners.robots import check_robots_and_sitemap
from utils.url import display_url, is_valid_url, normalize_url


def output_of(function, *args):
    with redirect_stdout(io.StringIO()) as output:
        function(*args)
    return output.getvalue()


class TestTargets(unittest.TestCase):
    def test_valid_targets(self):
        for supplied, expected in {
            "EXAMPLE.test": "https://example.test/",
            "HTTP://localhost:8000/": "http://localhost:8000/",
            "http://127.0.0.1:80/": "http://127.0.0.1:80/",
            "http://[::1]:8000/": "http://[::1]:8000/",
            "bücher.test/café?q=✓#top": "https://xn--bcher-kva.test/caf%C3%A9?q=%E2%9C%93",
        }.items():
            with self.subTest(supplied=supplied):
                self.assertEqual(normalize_url(supplied), expected)
                self.assertTrue(is_valid_url(supplied))

    def test_invalid_targets(self):
        for target in (
            "", "https://", "//example.test", "ftp://example.test",
            "http://user:password@example.test", "https://example.test:0/",
            "https://example.test:65536", "https://example.test:",
            "https://-example.test", "https://example..test", "https://[::1]extra",
            "https://[127.0.0.1]/", "https://[::1", "https://example.test/a b",
            "https://example.test/a\tb", "https://example.test\\other.test",
            "\x1b[31mexample.test",
        ):
            with self.subTest(target=target):
                self.assertFalse(is_valid_url(target))

    def test_display_redacts_query(self):
        self.assertEqual(
            display_url(normalize_url("https://example.test/a?q=private")),
            "https://example.test/a?[redacted]",
        )


class TestHeaderValues(unittest.TestCase):
    def test_hsts(self):
        for values, scheme, expected in (
            (["max-age=10"], "http", "applies to HTTPS only"),
            ([], "https", "missing or empty"),
            (["Max-Age=0"], "https", "disabled by max-age=0"),
            (["max-age=10; max-age=20"], "https", "invalid or missing max-age"),
            (['max-age="120"; includeSubDomains'], "https", "present"),
        ):
            with self.subTest(values=values, scheme=scheme):
                self.assertEqual(header_status("Strict-Transport-Security", values, scheme), expected)

    def test_conflicting_frame_options(self):
        self.assertEqual(
            header_status("X-Frame-Options", ["SAMEORIGIN", "DENY"], "https"),
            "conflicting values",
        )


class TestHttpModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self):
                server = self.server
                server.calls.append((self.command, self.path))
                status, headers, body = server.routes.get(
                    self.path, (404, (), b"not found")
                )
                self.send_response(status)
                for name, value in headers:
                    self.send_header(name, value)
                if not any(name.lower() == "content-length" for name, _ in headers):
                    self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command == "GET" and body:
                    try:
                        self.wfile.write(body)
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                        pass

            do_GET = respond
            do_HEAD = respond

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.server.calls = []
        self.server.routes = {}

    def test_connection_reports_http_error_and_never_follows_redirect(self):
        self.server.routes["/redirect"] = (302, (("Location", "/landing"),), b"")
        self.assertIn("302", output_of(check_connection, self.origin + "/redirect"))
        self.assertIn("404", output_of(check_connection, self.origin + "/missing"))
        self.assertEqual(self.server.calls, [("GET", "/redirect"), ("GET", "/missing")])

    def test_headers_preserve_duplicates_and_do_not_echo_values(self):
        self.server.routes["/"] = (200, (
            ("X-Frame-Options", "DENY"),
            ("X-Frame-Options", "unexpected-private-value"),
            ("X-Content-Type-Options", "NOSNIFF"),
            ("Content-Security-Policy", " "),
            ("X-XSS-Protection", "0"),
        ), b"")
        result = output_of(check_security_headers, self.origin)
        self.assertIn("X-Frame-Options: unrecognized value", result)
        self.assertIn("X-Content-Type-Options: present", result)
        self.assertIn("Content-Security-Policy: missing or empty", result)
        self.assertIn("X-XSS-Protection: legacy header", result)
        self.assertNotIn("unexpected-private-value", result)

    def test_cookie_fields_are_independent_and_values_are_hidden(self):
        self.server.routes["/"] = (200, (
            ("Set-Cookie", "first=private-one; Expires=Wed, 10 Jun 2030 12:00:00 GMT; HttpOnly; Secure; SameSite=Lax"),
            ("Set-Cookie", "second=private-two; SameSite=None"),
            ("Set-Cookie", "malformed"),
        ), b"")
        result = output_of(check_cookie_security, self.origin)
        self.assertIn("(first): Secure, HttpOnly, SameSite=Lax", result)
        self.assertIn("SameSite=None requires Secure", result)
        self.assertIn("Cookie #3: malformed", result)
        self.assertNotIn("private-", result)
        self.assertEqual(self.server.calls, [("GET", "/")])

    def test_no_cookie_fields(self):
        self.assertIn("No Set-Cookie fields", output_of(check_cookie_security, self.origin))

    def test_paths_only_check_the_supplied_path_with_head(self):
        self.server.routes["/"] = (200, (), b"home")
        self.server.routes["/configured"] = (200, (), b"hidden-body")
        self.server.routes["/restricted"] = (403, (), b"")
        self.server.routes["/redirect"] = (302, (("Location", "/configured"),), b"")
        self.server.routes["/no-head"] = (405, (), b"")
        self.server.routes["/not-modified"] = (304, (), b"")
        for path, result in (
            ("", "server returned success for HEAD"),
            ("/configured", "server returned success for HEAD"),
            ("/restricted", "access restricted"),
            ("/missing", "server reported the path missing"),
            ("/redirect", "HTTP 302): redirect"),
            ("/no-head", "server did not accept HEAD"),
            ("/not-modified", "result inconclusive"),
        ):
            with self.subTest(path=path):
                self.assertIn(result, output_of(check_sensitive_path, self.origin + path))
        self.assertEqual(self.server.calls, [
            ("HEAD", "/"), ("HEAD", "/configured"), ("HEAD", "/restricted"),
            ("HEAD", "/missing"), ("HEAD", "/redirect"), ("HEAD", "/no-head"),
            ("HEAD", "/not-modified"),
        ])

    def test_cli_paths_runs_on_bare_target(self):
        self.server.routes["/"] = (200, (), b"home")
        result = subprocess.run(
            [sys.executable, "main.py"],
            input=f"set target {self.origin}\nset mode paths\nshow target\nrun\nexit\n",
            capture_output=True, text=True, timeout=10, check=True,
        )
        self.assertIn(f"Running paths on {self.origin}/", result.stdout)
        self.assertIn("Path check (HTTP 200)", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.server.calls, [("HEAD", "/")])

    def test_robots_and_sitemap_are_origin_root_only(self):
        self.server.routes["/robots.txt"] = (
            200, (), b"User-Agent: *\nDisallow: /hidden # note\nSitemap: /other.xml\n",
        )
        self.server.routes["/sitemap.xml"] = (200, (), b"""
            <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <sitemap><loc>https://example.test/other.xml</loc></sitemap>
              <sitemap/>
            </sitemapindex>""")
        result = output_of(check_robots_and_sitemap, self.origin + "/nested?private=1")
        self.assertIn("disallow directives: 1", result)
        self.assertIn("2 (1 without a location)", result)
        self.assertNotIn("/hidden", result)
        self.assertEqual(self.server.calls, [("GET", "/robots.txt"), ("GET", "/sitemap.xml")])

    def test_bad_robots_still_allows_sitemap_analysis(self):
        self.server.routes["/robots.txt"] = (200, (), b"\xff")
        self.server.routes["/sitemap.xml"] = (200, (), b"""
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <url><loc>https://example.test/</loc></url>
            </urlset>""")
        result = output_of(check_robots_and_sitemap, self.origin)
        self.assertIn("/robots.txt: malformed", result)
        self.assertIn("URL entries: 1 (0 without a location)", result)

    def test_sitemap_rejects_dtd_and_invalid_xml(self):
        for body in (b"<!DOCTYPE urlset><urlset/>", b"<unclosed>"):
            with self.subTest(body=body):
                self.server.routes["/sitemap.xml"] = (200, (), body)
                self.assertIn(
                    "/sitemap.xml: malformed",
                    output_of(check_robots_and_sitemap, self.origin),
                )

    def test_documents_reject_oversize_truncated_and_encoded_responses(self):
        for headers, body, message in (
            ((), b"x" * 512001, "size limit"),
            ((("Content-Length", "120"),), b"short", "incomplete"),
            ((("Content-Encoding", "gzip"),), b"compressed", "unsupported content encoding"),
        ):
            with self.subTest(message=message):
                self.server.routes["/robots.txt"] = (200, headers, body)
                self.assertIn(message, output_of(check_robots_and_sitemap, self.origin))

    def test_cli_subprocess_uses_local_server_and_exits_on_eof(self):
        result = subprocess.run(
            [sys.executable, "main.py"],
            input=f"set target {self.origin}\nset mode connection\nrun\n",
            capture_output=True, text=True, timeout=10, check=True,
        )
        self.assertIn("status 404", result.stdout)
        self.assertIn("Exiting B7XSight", result.stdout)
        self.assertEqual(result.stderr, "")


class TestCliAndFailures(unittest.TestCase):
    def test_help_and_completion_share_modes(self):
        result = output_of(main.print_help, main.MODES)
        for mode in main.MODES:
            self.assertIn(mode, result)
        self.assertEqual(suggestions("SET MODE r", "r", main.MODES), ["robots "])
        self.assertEqual(suggestions("show ", "", main.MODES), ["target ", "mode "])
        self.assertEqual(suggestions("run ", "", main.MODES), [])

    def test_missing_readline_is_supported(self):
        with patch.dict(sys.modules, {"readline": None}):
            configure_completion(main.MODES)

    def test_cli_keeps_last_valid_selection(self):
        commands = [
            "run", "set target http://example.test/?key=private-value",
            "set target https://user:pass@example.test", "set mode headers",
            "set mode bad", "show target", "run", "exit",
        ]
        with patch("builtins.input", side_effect=commands), patch.object(
            main, "MODES", {"headers": (lambda target: print("Header check invoked"), "Headers")}
        ):
            result = output_of(main.main)
        self.assertIn("Set both target and mode", result)
        self.assertIn("Current target: http://example.test/?[redacted]", result)
        self.assertIn("Header check invoked", result)
        self.assertNotIn("private-value", result)

    def test_network_error_output_omits_exception_details(self):
        with patch("utils.http.HTTPConnection.request", side_effect=TimeoutError("secret")):
            result = output_of(check_connection, "http://example.test")
        self.assertIn("Connection failed (TimeoutError)", result)
        self.assertNotIn("secret", result)

    def test_ports_use_only_web_defaults(self):
        with patch("scanners.ports.socket.create_connection", side_effect=ConnectionRefusedError) as dial:
            result = output_of(check_ports, "https://example.test/")
        self.assertEqual([call.args[0] for call in dial.call_args_list], [
            ("example.test", 80), ("example.test", 443),
        ])
        self.assertIn("TCP 443: connection refused", result)

    def test_port_checks_explicit_loopback_port(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            result = output_of(check_ports, f"http://127.0.0.1:{port}/")
        self.assertEqual(result, f"TCP {port}: open\n")
