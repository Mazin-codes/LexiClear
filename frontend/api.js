/**
 * LexiClear+ Shared API Client
 * All pages import this via <script src="api.js"></script>
 */

const BASE_URL = "http://localhost:8000";

// ─── Session Storage Cache Keys ───────────────────────────────────────────────
const CACHE_KEY_ANALYSIS = "lc_analysis";
const CACHE_KEY_FILENAME = "lc_filename";
const CACHE_KEY_FILETYPE = "lc_filetype";

// ─── Cache helpers ────────────────────────────────────────────────────────────
function setCachedAnalysis(data)  { sessionStorage.setItem(CACHE_KEY_ANALYSIS, JSON.stringify(data)); }
function getCachedAnalysis()      { const r = sessionStorage.getItem(CACHE_KEY_ANALYSIS); return r ? JSON.parse(r) : null; }
function setCachedFilename(name)  { sessionStorage.setItem(CACHE_KEY_FILENAME, name); }
function getCachedFilename()      { return sessionStorage.getItem(CACHE_KEY_FILENAME) || "Unknown Document"; }
function setCachedFileType(type)  { sessionStorage.setItem(CACHE_KEY_FILETYPE, type); }
function getCachedFileType()      { return sessionStorage.getItem(CACHE_KEY_FILETYPE) || ""; }
function clearCache() {
    sessionStorage.removeItem(CACHE_KEY_ANALYSIS);
    sessionStorage.removeItem(CACHE_KEY_FILENAME);
    sessionStorage.removeItem(CACHE_KEY_FILETYPE);
}

// ─── Upload document ──────────────────────────────────────────────────────────
async function uploadDocument(file) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE_URL}/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
}

// ─── Analyze document ─────────────────────────────────────────────────────────
async function analyzeDocument() {
    const res = await fetch(`${BASE_URL}/analyze`, { method: "POST" });
    if (!res.ok) throw new Error(`Analyze failed: ${res.status}`);
    const data = await res.json();
    setCachedAnalysis(data);
    return data;
}

// ─── Ask a question ───────────────────────────────────────────────────────────
async function askQuestion(question, language = null) {
    const body = { question };
    if (language) body.language = language;
    const res = await fetch(`${BASE_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Ask failed: ${res.status}`);
    }
    return res.json();
}

// ─── Text-to-Speech ───────────────────────────────────────────────────────────
async function speakText(text, language = "en") {
    if (!text) throw new Error("No text provided for speech.");
    // Clean markdown formatting characters
    const cleanText = String(text)
        .replace(/[*#_`~|\-]/g, " ")
        .replace(/\s+/g, " ")
        .trim();

    const res = await fetch(`${BASE_URL}/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: cleanText, language }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `TTS failed: ${res.status}`);
    }
    const buffer = await res.arrayBuffer();
    const audioBlob = new Blob([buffer], { type: "audio/wav" });
    return URL.createObjectURL(audioBlob);
}

// ─── Translation ──────────────────────────────────────────────────────────────
async function translateText(text, targetLanguage = "Hindi") {
    const res = await fetch(`${BASE_URL}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, target_language: targetLanguage }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Translation failed: ${res.status}`);
    }
    return res.json();
}

// ─── HTML escaping ────────────────────────────────────────────────────────────
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// ─── Inline markdown (bold, italic, code) — operates on already-escaped text ──
function _inline(escaped) {
    return escaped
        .replace(/\*\*(.+?)\*\*/g, "<strong class=\"font-semibold text-primary\">$1</strong>")
        .replace(/\*(.+?)\*/g,     "<em class=\"italic\">$1</em>")
        .replace(/`(.+?)`/g,       "<code class=\"bg-surface-container px-1 rounded text-xs font-mono\">$1</code>");
}

// ─── Full markdown renderer ───────────────────────────────────────────────────
/**
 * Convert a markdown string to HTML.
 * Handles: headings (# ## ###), bold (**), italic (*), code (`),
 * unordered lists (- / *), and markdown tables (| col | col |).
 * HTML is escaped first to prevent XSS.
 */
function renderMarkdown(md) {
    if (!md) return "";

    const lines  = String(md).split("\n");
    let html     = "";
    let inList   = false;
    let inTable  = false;
    let colCount = 0;

    const closeList  = () => { if (inList)  { html += "</ul>"; inList  = false; } };
    const closeTable = () => { if (inTable) { html += "</tbody></table></div>"; inTable = false; colCount = 0; } };

    for (let i = 0; i < lines.length; i++) {
        const raw     = lines[i];
        const trimmed = raw.trim();

        // ── Table rows ──────────────────────────────────────────────────────
        if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
            // Separator row  (e.g. |---|---|)
            if (/^\|[\s\-:|]+\|$/.test(trimmed)) {
                if (!inTable) continue;   // skip separator before any table starts
                continue;                 // skip separator inside table
            }

            const cells = trimmed
                .split("|")
                .filter((_, ci, a) => ci > 0 && ci < a.length - 1)
                .map(c => c.trim());

            if (!inTable) {
                closeList();
                colCount = cells.length;
                html += `<div class="overflow-x-auto my-3 rounded-lg border border-outline-variant">
                         <table class="w-full text-sm border-collapse">
                         <thead class="bg-surface-container-high">
                         <tr>${cells.map(c => `<th class="px-3 py-2 text-left font-semibold text-on-surface text-xs border-b border-outline-variant whitespace-nowrap">${_inline(escapeHtml(c))}</th>`).join("")}</tr>
                         </thead><tbody>`;
                inTable = true;
            } else {
                // Pad or trim to header column count
                while (cells.length < colCount) cells.push("");
                html += `<tr class="border-b border-outline-variant/50 even:bg-surface-container-lowest hover:bg-secondary-container/20 transition-colors">
                         ${cells.slice(0, colCount).map(c => `<td class="px-3 py-2 text-on-surface-variant align-top text-xs">${_inline(escapeHtml(c))}</td>`).join("")}
                         </tr>`;
            }
            continue;
        } else {
            closeTable();
        }

        // ── Headings ────────────────────────────────────────────────────────
        if (trimmed.startsWith("### ")) {
            closeList();
            html += `<h3 class="font-semibold text-primary text-sm mt-4 mb-1">${_inline(escapeHtml(trimmed.slice(4)))}</h3>`;
        } else if (trimmed.startsWith("## ")) {
            closeList();
            html += `<h2 class="font-bold text-primary text-[15px] mt-5 mb-2 pb-1 border-b border-outline-variant/50">${_inline(escapeHtml(trimmed.slice(3)))}</h2>`;
        } else if (trimmed.startsWith("# ")) {
            closeList();
            html += `<h1 class="font-bold text-primary text-[17px] mt-5 mb-2">${_inline(escapeHtml(trimmed.slice(2)))}</h1>`;

        // ── List items ───────────────────────────────────────────────────────
        } else if (/^[-*] /.test(trimmed)) {
            if (!inList) { html += `<ul class="my-2 space-y-1 list-disc list-inside pl-1">`; inList = true; }
            html += `<li class="text-on-surface-variant text-sm leading-relaxed">${_inline(escapeHtml(trimmed.slice(2)))}</li>`;

        // ── Numbered list ────────────────────────────────────────────────────
        } else if (/^\d+\. /.test(trimmed)) {
            if (!inList) { html += `<ol class="my-2 space-y-1 list-decimal list-inside pl-1">`; inList = true; }
            html += `<li class="text-on-surface-variant text-sm leading-relaxed">${_inline(escapeHtml(trimmed.replace(/^\d+\. /, "")))}</li>`;

        // ── Horizontal rule ──────────────────────────────────────────────────
        } else if (/^(-{3,}|_{3,}|\*{3,})$/.test(trimmed)) {
            closeList();
            html += `<hr class="border-outline-variant my-3">`;

        // ── Empty line ───────────────────────────────────────────────────────
        } else if (trimmed === "") {
            closeList();
            // Don't add a visible break if previous element already has margin

        // ── Regular paragraph ────────────────────────────────────────────────
        } else {
            closeList();
            html += `<p class="text-sm text-on-surface my-1 leading-relaxed">${_inline(escapeHtml(trimmed))}</p>`;
        }
    }

    closeList();
    closeTable();
    return html;
}

function cleanMarkdownText(str) {
    if (!str) return "";
    return String(str)
        .replace(/\*\*/g, "")
        .replace(/\*/g, "")
        .replace(/`/g, "")
        .replace(/^#+\s*/, "")
        .trim();
}

// ─── Risk table parser ────────────────────────────────────────────────────────
/**
 * Parse the risk markdown (which may be a table OR heading-based) into
 * structured risk objects: { severity, title, explanation, impact, clause, recommendation }
 */
function parseRisksFromMarkdown(markdown) {
    if (!markdown) return [];
    if (markdown.trim() === "No significant legal risks detected.") return [];

    const risks = [];

    // ── Detect table format ────────────────────────────────────────────────
    const tableLines = markdown.split("\n").filter(l => l.trim().startsWith("|"));
    if (tableLines.length >= 3) {
        // Parse header to find column positions
        const headerCells = tableLines[0]
            .split("|")
            .filter((_, i, a) => i > 0 && i < a.length - 1)
            .map(c => c.trim().toLowerCase());

        const idx = (keywords) => headerCells.findIndex(h => keywords.some(k => h.includes(k)));
        const catIdx   = idx(["category", "risk cat", "type"]);
        const levelIdx = idx(["level", "risk level", "severity"]);
        const clauseIdx= idx(["clause", "relevant"]);
        const explIdx  = idx(["explanation", "plain", "explain"]);
        const impactIdx= idx(["impact", "ignored", "consequence"]);
        const recIdx   = idx(["recommend", "suggestion", "action"]);

        for (let i = 1; i < tableLines.length; i++) {
            const row = tableLines[i].trim();
            if (/^\|[\s\-:|]+\|$/.test(row)) continue; // separator

            const cols = row
                .split("|")
                .filter((_, ci, a) => ci > 0 && ci < a.length - 1)
                .map(c => c.trim());

            if (!cols.length || cols.every(c => !c)) continue;

            const getCol = (idx) => idx >= 0 && idx < cols.length ? cols[idx] : "";

            const levelText = getCol(levelIdx);
            let severity = "low";
            if (/high/i.test(levelText))        severity = "high";
            else if (/med/i.test(levelText))    severity = "medium";

            const rawTitle = getCol(catIdx) || getCol(0) || "Unknown Risk";

            risks.push({
                severity,
                title:          cleanMarkdownText(rawTitle),
                explanation:    cleanMarkdownText(getCol(explIdx)),
                impact:         cleanMarkdownText(getCol(impactIdx)),
                clause:         cleanMarkdownText(getCol(clauseIdx)),
                recommendation: cleanMarkdownText(getCol(recIdx)),
            });
        }

        if (risks.length) return risks;
    }

    // ── Fallback: heading-based format ─────────────────────────────────────
    const sections = markdown.split(/^#{2,3}\s/m).filter(Boolean);
    for (const section of sections) {
        const lines   = section.trim().split("\n");
        const heading = lines[0].trim();
        const body    = lines.slice(1).join("\n").trim();

        let severity = "low";
        if (/high/i.test(heading))   severity = "high";
        else if (/med/i.test(heading)) severity = "medium";

        const rawTitle = heading
            .replace(/^(high|medium|low)\s*risk\s*[:\-]?/i, "")
            .replace(/risk\s*[:\-]?/i, "")
            .trim() || heading;

        const getField = (labels) => {
            for (const label of labels) {
                const m = body.match(new RegExp(`\\*{0,2}${label}\\*{0,2}\\s*:?\\s*([^\n]+)`, "i"));
                if (m) return m[1].trim();
            }
            return "";
        };

        risks.push({
            severity,
            title:          cleanMarkdownText(rawTitle),
            explanation:    cleanMarkdownText(getField(["Explanation", "Risk Category"])),
            impact:         cleanMarkdownText(getField(["Possible Impact", "Impact"])),
            clause:         cleanMarkdownText(getField(["Relevant Clause", "Clause"])),
            recommendation: cleanMarkdownText(getField(["Recommendation"])),
        });
    }

    return risks;
}

// ─── Toast notification ───────────────────────────────────────────────────────
function showToast(msg, type = "info") {
    const existing = document.getElementById("lc-toast");
    if (existing) existing.remove();

    const colors = {
        info:    "background:#303032;color:#f3f0f2",
        error:   "background:#991b1b;color:#fff",
        success: "background:#044e58;color:#fff",
    };
    const icons = { info: "info", error: "error", success: "check_circle" };

    const toast = document.createElement("div");
    toast.id = "lc-toast";
    toast.style.cssText = `position:fixed;bottom:24px;left:50%;transform:translateX(-50%);${colors[type]};padding:12px 24px;border-radius:999px;font-size:14px;font-weight:600;box-shadow:0 4px 24px rgba(0,0,0,.18);z-index:9999;display:flex;align-items:center;gap:8px;white-space:nowrap`;
    toast.innerHTML = `<span class="material-symbols-outlined" style="font-size:18px">${icons[type]}</span>${escapeHtml(msg)}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
