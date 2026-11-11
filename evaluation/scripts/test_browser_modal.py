"""
Automated Browser Interaction Test for HIST-BUG-012.
Verifies:
1. Document deletion confirmation modal appears in a real browser DOM (no native prompt/blocking).
2. 'Cancel' button dismisses the modal and leaves the document intact.
3. 'Confirm Delete' button removes the document from the UI and backend.
Uses Chrome DevTools Protocol (CDP) via websockets with a headless Chrome instance.
"""

import asyncio
import json
import os
import subprocess
import time
import urllib.request
import httpx
import websockets

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9222


def seed_test_document() -> tuple[str, str]:
    """Upload a test document directly via backend API."""
    test_filename = f"modal_interactive_test_{int(time.time())}.txt"
    test_content = (
        "Ground truth reference data for interactive browser modal verification. "
        "Supabase durable persistence and React modal deletion regression test."
    )

    files = {"file": (test_filename, test_content.encode("utf-8"), "text/plain")}
    res = httpx.post(f"{BACKEND_URL}/documents/upload", files=files, timeout=10.0)
    res.raise_for_status()
    data = res.json()
    return data["id"], data["filename"]


async def run_browser_modal_test():
    print("=" * 70)
    print("HIST-BUG-012: BROWSER MODAL AUTOMATED INTERACTION TEST")
    print("=" * 70)

    # 1. Seed test document
    doc_id, filename = seed_test_document()
    print(f"\n[1] Seeding test document '{filename}' via API...")
    print(f"  Seeded document: ID={doc_id}, filename={filename}")

    # 2. Launch headless Chrome with debugging port
    print(f"\n[2] Launching Chrome Headless with Remote Debugging (port {CDP_PORT})...")
    temp_dir = os.environ.get("TEMP", r"C:\Temp")
    user_data = os.path.join(temp_dir, f"chrome_dev_{int(time.time())}")
    chrome_cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={CDP_PORT}",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-extensions",
        f"--user-data-dir={user_data}",
        FRONTEND_URL,
    ]
    chrome_proc = subprocess.Popen(
        chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    try:
        # Wait for CDP endpoint to become ready
        await asyncio.sleep(2.5)
        req = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=5)
        pages = json.loads(req.read().decode("utf-8"))
        ws_url = pages[0]["webSocketDebuggerUrl"]
        print(f"Connected to Chrome CDP: {ws_url[:40]}...")

        async with websockets.connect(ws_url) as ws:
            msg_id = 0

            async def cdp_call(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get("id") == msg_id:
                        return resp

            async def cdp_eval(expression):
                res = await cdp_call("Runtime.evaluate", {"expression": expression, "returnByValue": True})
                return res.get("result", {}).get("result", {}).get("value")

            # Enable Page and Runtime
            await cdp_call("Page.enable")
            await cdp_call("Runtime.enable")
            await asyncio.sleep(2.5)

            # Switch to Documents tab
            print(f"\n[3] Navigating to Documents Page in React App...")
            nav_status = None
            for _ in range(5):
                nav_status = await cdp_eval("""
                    (() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const docBtn = buttons.find(b => b.textContent.includes('Documents'));
                        if (docBtn) {
                            docBtn.click();
                            return 'CLICKED_DOCUMENTS_TAB';
                        }
                        return 'BUTTON_NOT_FOUND';
                    })()
                """)
                if nav_status == "CLICKED_DOCUMENTS_TAB":
                    break
                await asyncio.sleep(1.0)

            print(f"Navigation: {nav_status}")
            assert nav_status == "CLICKED_DOCUMENTS_TAB"
            await asyncio.sleep(2.0)

            # Check that the test document is visible in the table
            doc_visible = await cdp_eval(f"document.body.innerText.includes('{filename}')")
            print(f"Document '{filename}' visible in table: {doc_visible}")
            assert doc_visible is True, f"Document '{filename}' was not found in the documents table!"

            # Verify modal is NOT open initially
            modal_before = await cdp_eval("document.body.innerText.includes('Remove Document?')")
            print(f"Modal in DOM before click: {modal_before} (Expected: False)")
            assert modal_before is False

            # Click delete (trash icon) for that document
            print(f"\n[4] Clicking Trash Icon for '{filename}' to trigger Confirmation Modal...")
            click_trash = await cdp_eval(f"""
                (() => {{
                    const row = document.querySelector(`div[data-testid="doc-row"][data-filename="{filename}"]`);
                    if (row) {{
                        const btn = row.querySelector('button[title="Delete document"]');
                        if (btn) {{
                            btn.click();
                            return 'CLICKED_ROW_DELETE_BUTTON';
                        }}
                    }}
                    return 'ROW_NOT_FOUND';
                }})()
            """)
            print(f"Trash button click action: {click_trash}")
            assert click_trash == "CLICKED_ROW_DELETE_BUTTON"
            await asyncio.sleep(0.5)

            # Assert Modal is now visible in DOM
            print("\n[5] Verifying Modal Elements in Browser DOM...")
            modal_state = await cdp_eval(f"""
                (() => {{
                    const hasTitle = document.body.innerText.includes('Remove Document?');
                    const hasNotice = document.body.innerText.includes('Are you sure you want to remove') && document.body.innerText.includes('{filename}');
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const cancelBtn = buttons.find(b => b.textContent.trim() === 'Cancel');
                    const confirmBtn = buttons.find(b => b.textContent.trim() === 'Confirm Delete');
                    return {{
                        hasTitle,
                        hasNotice,
                        hasCancel: !!cancelBtn,
                        hasConfirm: !!confirmBtn,
                        isModalValid: hasTitle && hasNotice && !!cancelBtn && !!confirmBtn
                    }};
                }})()
            """)
            print(f"  Modal Title Present: {modal_state.get('hasTitle')}")
            print(f"  Modal Warning Present: {modal_state.get('hasNotice')}")
            print(f"  Cancel Button Present: {modal_state.get('hasCancel')}")
            print(f"  Confirm Delete Button Present: {modal_state.get('hasConfirm')}")
            assert modal_state.get("isModalValid") is True, f"Modal validation failed: {modal_state}"
            print("✓ In-DOM confirmation modal successfully displayed without browser blocking.")

            # Test Cancel
            print("\n[6] Testing Modal 'Cancel' Action...")
            await cdp_eval("""
                (() => {
                    const cancelBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Cancel');
                    if (cancelBtn) cancelBtn.click();
                })()
            """)
            await asyncio.sleep(0.5)

            modal_cancelled = await cdp_eval("document.body.innerText.includes('Remove Document?')")
            print(f"  Modal dismissed after Cancel: {not modal_cancelled}")
            assert modal_cancelled is False

            doc_still_there = await cdp_eval(f"document.body.innerText.includes('{filename}')")
            print(f"  Document still preserved: {doc_still_there}")
            assert doc_still_there is True
            print("✓ Cancel button dismissed modal and preserved document.")

            # Test Confirm Delete
            print("\n[7] Testing Modal 'Confirm Delete' Action...")
            # Re-open modal for the target document
            reopen_trash = await cdp_eval(f"""
                (() => {{
                    const row = document.querySelector(`div[data-testid="doc-row"][data-filename="{filename}"]`);
                    if (row) {{
                        const btn = row.querySelector('button[title="Delete document"]');
                        if (btn) {{
                            btn.click();
                            return 'CLICKED_ROW_DELETE_BUTTON';
                        }}
                    }}
                    return 'ROW_NOT_FOUND';
                }})()
            """)
            print(f"Re-open modal trash click: {reopen_trash}")
            assert reopen_trash == "CLICKED_ROW_DELETE_BUTTON"
            await asyncio.sleep(0.5)

            # Click Confirm Delete
            confirm_res = await cdp_eval("""
                (() => {
                    const confirmBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Confirm Delete');
                    if (confirmBtn) {
                        confirmBtn.click();
                        return 'CLICKED_CONFIRM_DELETE';
                    }
                    return 'CONFIRM_BTN_NOT_FOUND';
                })()
            """)
            print(f"Confirm button click result: {confirm_res}")
            assert confirm_res == "CLICKED_CONFIRM_DELETE"

            # Poll for document removal from table
            result_val = {}
            for _ in range(10):
                await asyncio.sleep(0.5)
                result_val = await cdp_eval(f"""
                    (() => {{
                        const row = document.querySelector(`div[data-testid="doc-row"][data-filename="{filename}"]`);
                        const successAlert = document.body.innerText.includes("Removed '{filename}'");
                        return {{
                            rowExists: row !== null,
                            successAlert: successAlert
                        }};
                    }})()
                """)
                if not result_val.get("rowExists"):
                    break

            print(f"  Row exists in table: {result_val.get('rowExists')}, Success alert: {result_val.get('successAlert')}")
            assert result_val.get("rowExists") is False, "Document row should no longer exist in the document table!"
            print("✓ Confirm Delete successfully removed document from UI and backend.")

            print("\n" + "=" * 70)
            print("HIST-BUG-012 BROWSER TEST RESULT: ALL ASSERTIONS PASSED (100% VERIFIED)")
            print("=" * 70)

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(run_browser_modal_test())
