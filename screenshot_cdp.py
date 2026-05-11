import subprocess, time, json, urllib.request, base64, os, sys

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_DIR = r"c:\Users\simao\Desktop\Brandings\temporary screenshots"
URL = "http://localhost:3000"

# Kill any leftover Chrome on port 9223
subprocess.run(["powershell", "-Command",
    "Get-NetTCPConnection -LocalPort 9223 -ErrorAction SilentlyContinue | "
    "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
    capture_output=True)
time.sleep(1)

proc = subprocess.Popen([
    CHROME,
    "--headless", "--remote-debugging-port=9223", "--remote-allow-origins=*",
    "--disable-gpu", "--window-size=1440,900", "--disable-extensions",
    URL
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(3)

tabs = json.loads(urllib.request.urlopen("http://localhost:9223/json/list").read())
print(f"Tabs: {[t.get('url') for t in tabs]}")
tab = next((t for t in tabs if "localhost:3000" in t.get("url", "")), tabs[0])
ws_url = tab.get("webSocketDebuggerUrl") or tab.get("webSocketUrl")
print(f"WS: {ws_url}")

import websocket as ws_mod

ws_conn = ws_mod.create_connection(ws_url, suppress_origin=True)
_id = [0]

def send(method, params=None):
    _id[0] += 1
    ws_conn.send(json.dumps({"id": _id[0], "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws_conn.recv())
        if msg.get("id") == _id[0]:
            return msg
        # ignore events

# Wait for page load
send("Page.enable")
time.sleep(2)

# Make all fade-in elements visible
send("Runtime.evaluate", {
    "expression": "document.querySelectorAll('.fade-in').forEach(e => { e.classList.add('visible'); })"
})
time.sleep(0.5)

# Get page total height
result = send("Runtime.evaluate", {"expression": "document.body.scrollHeight"})
total_h = result["result"]["result"]["value"]
print(f"Page height: {total_h}px")

scroll_positions = [
    (0,    "page-0-hero.png"),
    (800,  "page-800-stats-catalog.png"),
    (1700, "page-1700-featured.png"),
    (2600, "page-2600-about.png"),
    (3500, "page-3500-process.png"),
    (4400, "page-4400-testimonials.png"),
    (5300, "page-5300-cta-contact.png"),
    (total_h - 900, "page-end-footer.png"),
]

for y, fname in scroll_positions:
    if y < 0:
        y = 0
    send("Runtime.evaluate", {"expression": f"window.scrollTo(0, {y})"})
    time.sleep(0.4)
    result = send("Page.captureScreenshot", {"format": "png"})
    img = base64.b64decode(result["result"]["data"])
    path = os.path.join(OUT_DIR, fname)
    with open(path, "wb") as f:
        f.write(img)
    print(f"Saved {fname}")

ws_conn.close()
proc.terminate()
print("All done.")
