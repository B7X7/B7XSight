# B7XSight

B7XSight runs low-impact web configuration checks from an interactive Python console. Use it only on hosts and paths you own or have explicit permission to assess.

## Install

Use Python 3.10 or newer.

```sh
git clone https://github.com/B7X7/B7XSight.git
cd B7XSight
python -m pip install -r requirements.txt
python main.py
```

Use `python3` instead where your system names the executable that way. On Windows, `py` also works when the Python launcher is installed.

## Use the console

```text
set target https://authorized.example/
set mode headers
run
show target
show mode
help
exit
```

Replace `authorized.example` with a host you have permission to assess. Bare hostnames default to HTTPS. Use an explicit `http://` URL for HTTP-only targets. An explicit port is optional. The console also supports `clear` and tab completion where Python's readline module is available.

- `connection` makes one GET and reports the HTTP status. Any HTTP status establishes that the server answered.
- `headers` inspects one GET response for common security headers and checks basic HSTS, X-Content-Type-Options and X-Frame-Options values. Review policy effectiveness in the application context.
- `cookies` inspects each Set-Cookie field for Secure, HttpOnly and SameSite. The output includes cookie names and omits values. These checks cannot determine the sensitivity of individual cookies or whether the browser accepts them.
- `paths` sends one HEAD request to the exact non-root path you supply. For example, set the target to `https://authorized.example/internal/status` before running the mode. A 2xx response warrants manual verification because generic fallback pages can also return 2xx. HEAD behavior may differ from GET.
- `robots` reads the origin's `/robots.txt` and `/sitemap.xml`. It summarizes recognized robots directives and counts entries in a sitemap or sitemap index. It does not visit listed paths or child sitemaps. Analysis accepts UTF-8 robots files and uncompressed sitemap XML, capped at 512,000 bytes and 1 MiB respectively.
- `ports` checks TCP connectivity without sending application data. With an explicit URL port it checks that port only. Otherwise it checks 80 and 443 sequentially.

HTTP checks verify TLS certificates and hostnames. Requests are direct and do not follow redirects. Connection and response operations use a five-second socket timeout. TCP port checks use a two-second socket timeout per address attempt. The console redacts query strings in its output. Supply targets without credentials or other secrets.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests use local loopback fixtures and mocks. No external target is required.
