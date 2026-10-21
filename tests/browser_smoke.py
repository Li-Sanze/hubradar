"""Run offline report regression checks in a locally installed Chromium browser.

Example:
  python tests/browser_smoke.py gallery/honojs__hono/index.html --kind hono \
    --out reports/browser-hono --capture flow

No Playwright downloads or editor/private-Skill dependencies are required.
"""

import argparse
import base64
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import websocket


class DevTools:
    """Minimal test-only CDP client; the product has no browser-driver dependency."""

    def __init__(self, address):
        self.socket = websocket.create_connection(address, timeout=10, suppress_origin=True,
                                                  http_no_proxy=["127.0.0.1", "localhost"])
        self.counter = 0
        self.session = None
        self.network = []

    def call(self, method, **params):
        self.counter += 1
        message = {"id": self.counter, "method": method, "params": params}
        if self.session:
            message["sessionId"] = self.session
        self.socket.send(json.dumps(message))
        while True:
            response = json.loads(self.socket.recv())
            if response.get("method") == "Network.requestWillBeSent":
                self.network.append(response["params"]["request"]["url"])
            if response.get("id") == self.counter:
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response.get("result", {})

    def evaluate(self, expression, *, wait=False):
        response = self.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=wait)
        if "exceptionDetails" in response:
            raise RuntimeError(response["exceptionDetails"])
        return response.get("result", {}).get("value")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--browser", default=shutil.which("chromium") or shutil.which("google-chrome")
                        or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    parser.add_argument("--legacy-headless", action="store_true", help="For Chromium versions supporting --headless=old")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--kind", choices=["hono", "radar", "extended", "invalid"], required=True)
    parser.add_argument("--theme", choices=["light", "dark"], default="light")
    parser.add_argument("--capture", choices=["top", "flow", "states"], default="flow")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    options = json.dumps({"kind": args.kind, "theme": args.theme, "capture": args.capture})
    bootstrap = """<script>
window.hubradarTestErrors=[];window.hubradarTestNetwork=[];window.hubradarTestCSP=[];
addEventListener("error", e=>hubradarTestErrors.push(e.message));
addEventListener("unhandledrejection", e=>hubradarTestErrors.push(String(e.reason)));
addEventListener("securitypolicyviolation", e=>hubradarTestCSP.push(e.blockedURI));
const originalFetch=window.fetch;
window.fetch=(...args)=>{hubradarTestNetwork.push(String(args[0]));return originalFetch(...args)};
const originalOpen=XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open=function(method,url,...rest){hubradarTestNetwork.push(String(url));return originalOpen.call(this,method,url,...rest)};
</script>"""
    source = args.report.read_text(encoding="utf-8")
    source = source.replace('<script id="hubradar-mermaid">', bootstrap + '<script id="hubradar-mermaid">', 1)
    checks = Path(__file__).with_name("browser_report_checks.js").read_text(encoding="utf-8")
    injection = f"<script>window.hubradarTestOptions={options};\n{checks}</script>"
    # A JS dependency can itself contain "</body>". Only modify the final HTML tag.
    before, after = source.rsplit("</body>", 1)
    source = before + injection + "</body>" + after
    page = args.out.resolve() / "browser-fixture.html"
    page.write_text(source, encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="hubradar-browser-") as profile, \
            (args.out / "browser.stderr.txt").open("w") as error_log:
        process = subprocess.Popen(
            [args.browser, "--headless=old" if args.legacy_headless else "--headless",
             "--disable-gpu", "--disable-background-networking", "--no-first-run", "--hide-scrollbars",
             "--remote-debugging-port=0",
             f"--user-data-dir={profile}", f"--window-size={args.width},{args.height}",
             "about:blank"], stdout=subprocess.DEVNULL, stderr=error_log,
        )
        client = None
        try:
            endpoint = Path(profile) / "DevToolsActivePort"
            deadline = time.monotonic() + 15
            while not endpoint.exists():
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Browser did not start; inspect browser.stderr.txt")
                time.sleep(.1)
            port, path = endpoint.read_text().splitlines()[:2]
            client = DevTools(f"ws://127.0.0.1:{port}{path}")
            target = client.call("Target.createTarget", url="about:blank")["targetId"]
            client.session = client.call("Target.attachToTarget", targetId=target, flatten=True)["sessionId"]
            client.call("Page.enable")
            client.call("Runtime.enable")
            client.call("Network.enable")
            client.call("Emulation.setDeviceMetricsOverride", width=args.width, height=args.height,
                        deviceScaleFactor=1, mobile=False)
            client.call("Page.navigate", url=page.as_uri())
            deadline = time.monotonic() + 30
            payload = None
            while not payload:
                try:
                    payload = client.evaluate('document.getElementById("hubradar-browser-result")?.textContent')
                except RuntimeError:
                    # Navigation may briefly replace the initial execution context.
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError("Browser checks timed out; inspect browser.stderr.txt")
                if not payload:
                    time.sleep(.1)
            data = json.loads(payload)
            client.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))", wait=True)
            screenshot = client.call("Page.captureScreenshot", format="png", captureBeyondViewport=False)["data"]
            (args.out / "screenshot.png").write_bytes(base64.b64decode(screenshot))
            data["metrics"]["network_requests"] = [url for url in client.network if url.startswith(("http:", "https:"))]
            data["checks"]["zero_external_network_requests"] = not data["metrics"]["network_requests"]
        finally:
            if client:
                try:
                    client.session = None
                    client.call("Browser.close")
                except Exception:
                    pass
                client.socket.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
    data["requested_width"] = args.width
    data["checks"]["requested_viewport"] = data["viewport"] == args.width
    (args.out / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "viewport": data["viewport"], "checks": len(data["checks"]),
        "failed": [name for name, passed in data["checks"].items() if not passed],
        "natural_widths": [diagram["naturalWidth"] for diagram in data["metrics"].get("light", [])],
        "network_requests": data["metrics"].get("network_requests", []), "errors": data["errors"],
    }, ensure_ascii=False))
    return 0 if all(data["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
