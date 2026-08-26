# Browser Save Mechanics Research

**Ticket:** #9 (wayfinder:research)
**Branch:** `research/browser-save-mechanics`
**Date:** 2026-08-26

---

## 1. File System Access API Support Across Target Browsers

### Summary Table

| Browser | `showOpenFilePicker` | `showSaveFilePicker` | `showDirectoryPicker` | OPFS (`navigator.storage.getDirectory`) | Min Version |
|---------|---------------------|---------------------|----------------------|----------------------------------------|-------------|
| **Chrome (Desktop)** | ✅ | ✅ | ✅ | ✅ | 86+ |
| **Edge (Desktop)** | ✅ | ✅ | ✅ | ✅ | 86+ |
| **Opera** | ✅ | ✅ | ✅ | ✅ | 72+ |
| **Chrome for Android** | ✅ | ❌ (no `createWritable`) | ❌ | ✅ | 86+ |
| **Firefox (Desktop)** | ❌ | ❌ | ❌ | ✅ | 111+ (OPFS only) |
| **Firefox for Android** | ❌ | ❌ | ❌ | ✅ | 111+ (OPFS only) |
| **Safari (macOS)** | ❌ | ❌ | ❌ | ✅ | 15.2+ (OPFS only) |
| **Safari (iOS/iPadOS)** | ❌ | ❌ | ❌ | ✅ | 15.2+ (OPFS only) |
| **Samsung Internet** | ❌ | ❌ | ❌ | ❌ | — |

### Key Details

- **Chromium-based browsers (Chrome, Edge, Opera)** — Full support for local-disk picker methods since version 86/72. The API is enabled by default; no flags needed in current versions.
- **Firefox** — Mozilla published a **harmful standards position** on the local-disk picker methods (`showOpenFilePicker`, `showSaveFilePicker`, `showDirectoryPicker`). They ship only the **Origin Private File System (OPFS)** via `navigator.storage.getDirectory()`.
- **Safari / WebKit** — Apple opposes the local-disk pickers (security concerns). They ship only OPFS from Safari 15.2+. No flags or settings enable the pickers.
- **Mobile browsers** — No mobile browser exposes the picker methods. Chrome Android has `showOpenFilePicker` but **lacks `createWritable`**, making write operations impossible via the API.
- **Global picker availability** — ~27% of users (Chromium desktop only). OPFS is available in all modern engines.

### OPFS (Origin Private File System)

- Available in **all modern engines**: Chrome 86+, Edge 86+, Firefox 111+, Safari 15.2+
- Private to the origin, not user-visible on disk
- In Web Workers: `FileSystemSyncAccessHandle` for synchronous random-access I/O (used by SQLite-on-web, etc.)
- Does **not** provide user-facing file picker dialogs — purely programmatic sandboxed storage

---

## 2. Fallback Patterns When API Unavailable

### A. Download/Upload Cycle (Primary Fallback)

**Write (Save):**
```javascript
function downloadViaBlob(content, filename, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 100);
}
```

- Works in **all browsers** including Safari, Firefox, mobile
- Triggers browser's default download behavior (typically to `~/Downloads`)
- **Cannot overwrite existing files** — each save creates a new file
- No user choice of save location

**Read (Open):**
```javascript
function pickFileFallback() {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.style.display = 'none';
    input.onchange = () => resolve(input.files[0]);
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
  });
}
```

- Uses hidden `<input type="file">` — universal support
- Returns a `File` object (Blob subclass) readable via `.text()`, `.stream()`, `.arrayBuffer()`

### B. Clipboard-Based Fallback

**Write (Copy to Clipboard):**
```javascript
async function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  // Legacy fallback for non-secure contexts
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  const success = document.execCommand('copy');
  document.body.removeChild(textarea);
  return success;
}
```

- **Async Clipboard API** (`navigator.clipboard.writeText`) — requires secure context, user gesture
- **Legacy `execCommand('copy')`** — works in non-secure contexts, broader reach (including WebViews)
- **Firefox desktop**: supports `writeText` but **not** `navigator.share`
- **Safari iOS**: requires synchronous `Blob` construction inside gesture; async breaks it
- Not a true "save to file" — user must paste elsewhere

### C. `file://` Protocol Limitations

| Aspect | Behavior |
|--------|----------|
| **Secure Context** | Per spec, `file:` origins are "potentially trustworthy" — but **most browsers treat them as opaque origins** |
| **File System Access API** | **Blocked** in `file://` — `showOpenFilePicker` throws `SecurityError` (opaque origin check) |
| **OPFS** | May work in some implementations but not guaranteed |
| **Clipboard API** | `navigator.clipboard` is `undefined` on `file://` — must use `execCommand` |
| **Service Workers** | Not registered on `file://` — no offline/caching |
| **Workarounds** | Use `--allow-file-access-from-files` (Chromium flag) for local testing; serve via `localhost` for real use |

**Critical**: The File System Access API spec explicitly rejects opaque origins. Since `file://` origins are often opaque, the API is unavailable. The WICG issue #58 discusses this — consensus is that `file:` should be allowed but implementations vary.

---

## 3. Security Context Requirements

### Secure Context Definition (W3C)

A context is secure when:
- Scheme is `https:` or `wss:`
- Host is `localhost`, `127.0.0.1`, `::1`, or `*.localhost` (per RFC 6761)
- **`file:` scheme** — spec says "potentially trustworthy" but **implementations treat as opaque**

### File System Access API Requirements

1. **Secure Context** — `window.isSecureContext === true`
2. **User Gesture** — Must be called from transient activation (`click`, `pointerdown`, `keydown`)
3. **Top-Level Context** — Not in cross-origin iframe without `allow="file-system-access"`
4. **Same-Origin with Top-Level** — `environment.origin === topLevelOrigin`

### Permission Model

- **Read permission** — Granted implicitly when user picks file via picker
- **Write permission** — Granted for `showSaveFilePicker`; for existing handles, requires `requestPermission({ mode: 'readwrite' })` with user gesture
- **Persistence** — Handles can be serialized to IndexedDB and restored across sessions
- **Revocation** — Permission lost when all tabs for origin close; must re-prompt on return
- **Private Browsing** — IndexedDB serialization fails silently; wrap in try/catch

---

## 4. Polyfills and Established Patterns

### A. `browser-fs-access` (GoogleChromeLabs)

- **Not a polyfill** — a **ponyfill** (feature-detects, imports only needed code)
- Methods: `fileOpen()`, `directoryOpen()`, `fileSave()`
- Transparent fallback to `<input type="file">` and Blob download
- Used by **Excalidraw**, **Figma**, **VS Code for Web**
- Check `supported` property to detect native API availability

### B. `saschanaz/file-system-access`

- Full ponyfill implementing `showOpenFilePicker`, `showSaveFilePicker`, `showDirectoryPicker`
- Storage adapters: `node`, `deno`, `indexeddb`, `memory`, `cache`
- `indexeddb` adapter — works in browser but **fails in private mode**
- Directory picker fallback uses `webkitdirectory` (poor mobile support)
- Drag-and-drop via `getAsFileSystemHandle()` polyfill (requires File and Directory Entries API)

### C. `StreamSaver.js` / Custom Service Worker Pattern

- For **large file streaming** to disk without loading into memory
- Requires Service Worker (HTTPS only)
- Falls back to in-memory buffering + Blob download

### D. Established UX Pattern (Excalidraw, FieldKit)

```javascript
// Progressive enhancement pattern
if ('showSaveFilePicker' in window) {
  try {
    const handle = await showSaveFilePicker({ suggestedName: filename, types: [...] });
    const writable = await handle.createWritable();
    await writable.write(blob);
    await writable.close();
    return 'saved';
  } catch (err) {
    if (err.name === 'AbortError') return 'cancelled';
    // Fall through to download fallback
  }
}
// Universal fallback
downloadViaBlob(blob, filename);
```

- **Always build fallback first**, layer premium API on top
- Feature-detect with `'showOpenFilePicker' in window` — **never UA sniff**
- Handle `AbortError` silently (user cancelled)
- Route `SecurityError` / `NotAllowedError` to fallback

---

## 5. `docs-graph.html` File I/O Precedent

### Current State

- **No file I/O whatsoever** — it is a **self-contained static artifact**
- Graph data embedded as `<script type="application/json" id="graph-data">`
- Loaded via `JSON.parse(document.getElementById('graph-data').textContent)`
- Footer explicitly states: *"This file is a snapshot. The live surface is http://127.0.0.1:8787 — run python3 tools/serve_vault.py and open it. That page re-reads the working tree on every load and tells you when the repository has moved under it; this one cannot."*

### Implications for Orchestration Canvas

- The canvas will need **real file I/O** (save/load orchestration definitions)
- Cannot follow `docs-graph.html` pattern — it's a read-only visualization
- Must implement the **progressive enhancement pattern** above
- Target browsers: Chrome/Edge (full API), Firefox/Safari (fallback only), mobile (fallback only)

---

## Recommendations for Orchestration Canvas Spec

1. **Adopt `browser-fs-access`** as the abstraction layer — handles detection, fallback, and edge cases
2. **Design for download/upload cycle as primary UX** on Firefox/Safari/mobile
3. **Persist file handles in IndexedDB** for "reopen last file" workflow (Chromium only)
4. **Require HTTPS/localhost** for deployment — `file://` will not work for File System Access API
5. **Implement clipboard copy** as tertiary fallback for sharing/copying definitions
6. **Test matrix**:
   - Chrome Desktop (Windows/macOS/Linux) — full API
   - Edge Desktop — full API
   - Firefox Desktop — fallback only
   - Safari macOS — fallback only
   - Safari iOS — fallback only
   - Chrome Android — read API only, write via fallback
   - Private/Incognito modes — handle IndexedDB serialization failure

---

## References

- [File System Access API - Chrome Developers](https://developer.chrome.com/docs/capabilities/web-apis/file-system-access)
- [WICG File System Access Spec](https://wicg.github.io/file-system-access/)
- [Can I Use - Native File System API](https://caniuse.com/native-filesystem-api)
- [browser-fs-access (GoogleChromeLabs)](https://github.com/GoogleChromeLabs/browser-fs-access)
- [saschanaz/file-system-access](https://github.com/saschanaz/file-system-access)
- [Secure Contexts Spec](https://w3c.github.io/webappsec-secure-contexts/)
- [Excalidraw File Handling](https://github.com/excalidraw/excalidraw)
- [FieldKit: Real Files and Native Sharing](https://dev.to/alex_truhniy/real-files-and-native-sharing-from-a-web-app-file-system-access-web-share-fieldkit-5-1f9h)