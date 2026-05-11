import json, urllib.request, base64, os, time, subprocess, sys
import websocket as ws_mod

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_DIR = r"c:\Users\simao\Desktop\Brandings\temporary screenshots"
URL = "http://localhost:3000/catalogo.html"

subprocess.run(["powershell", "-Command",
    "Get-NetTCPConnection -LocalPort 9223 -ErrorAction SilentlyContinue | "
    "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
    capture_output=True)
time.sleep(1)

proc = subprocess.Popen([CHROME, "--headless", "--remote-debugging-port=9223",
    "--remote-allow-origins=*", "--disable-gpu", "--window-size=1440,900",
    "--disable-extensions", URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

tabs = json.loads(urllib.request.urlopen("http://localhost:9223/json/list").read())
tab = next((t for t in tabs if "catalogo" in t.get("url", "")), tabs[0])
ws_url = tab.get("webSocketDebuggerUrl") or tab.get("webSocketUrl")
print("WS:", ws_url)

ws = ws_mod.create_connection(ws_url, suppress_origin=True)
_id = [0]

def send(method, params=None):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id[0]:
            return msg

send("Page.enable")
time.sleep(2)

for y, fname in [(0, "cat-top.png"), (900, "cat-product.png"), (1800, "cat-mid.png")]:
    send("Runtime.evaluate", {"expression": f"window.scrollTo(0, {y})"})
    time.sleep(0.4)
    result = send("Page.captureScreenshot", {"format": "png"})
    img = base64.b64decode(result["result"]["data"])
    path = os.path.join(OUT_DIR, fname)
    open(path, "wb").write(img)
    print("Saved", fname)

ws.close()
proc.terminate()
print("Done")
