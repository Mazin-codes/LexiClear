document.addEventListener("DOMContentLoaded", () => {
    // Nav Elements
    const navButtons = document.querySelectorAll(".nav-btn");
    const panels = document.querySelectorAll(".endpoint-panel");

    // History log container
    const historyContainer = document.getElementById("history-container");

    // File Upload Elements
    const fileDropzone = document.getElementById("file-dropzone");
    const fileInput = document.getElementById("file-input");
    const selectedFileName = document.getElementById("selected-file-name");
    const btnExecuteUpload = document.getElementById("btn-execute-upload");
    const codeUpload = document.getElementById("code-upload");
    const metaUpload = document.getElementById("meta-upload");
    const statusUpload = document.getElementById("status-upload");
    const timeUpload = document.getElementById("time-upload");

    // Analyze Elements
    const btnExecuteAnalyze = document.getElementById("btn-execute-analyze");
    const codeAnalyze = document.getElementById("code-analyze");
    const metaAnalyze = document.getElementById("meta-analyze");
    const statusAnalyze = document.getElementById("status-analyze");
    const timeAnalyze = document.getElementById("time-analyze");

    // Ask Elements
    const textareaAskBody = document.getElementById("textarea-ask-body");
    const btnExecuteAsk = document.getElementById("btn-execute-ask");
    const codeAsk = document.getElementById("code-ask");
    const metaAsk = document.getElementById("meta-ask");
    const statusAsk = document.getElementById("status-ask");
    const timeAsk = document.getElementById("time-ask");

    let uploadedFile = null;

    // --- TAB NAVIGATION ---
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            navButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const endpoint = btn.getAttribute("data-endpoint");
            panels.forEach(panel => {
                if (panel.id === `panel-${endpoint}`) {
                    panel.classList.remove("hidden");
                } else {
                    panel.classList.add("hidden");
                }
            });
        });
    });

    // --- FILE DROPZONE HANDLERS ---
    fileDropzone.addEventListener("click", () => fileInput.click());
    fileDropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        fileDropzone.classList.add("dragover");
    });
    fileDropzone.addEventListener("dragleave", () => {
        fileDropzone.classList.remove("dragover");
    });
    fileDropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        fileDropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
            alert("Please select a PDF file.");
            return;
        }
        uploadedFile = file;
        selectedFileName.textContent = `Selected: ${file.name} (${formatBytes(file.size)})`;
        btnExecuteUpload.disabled = false;
    }

    // --- EXECUTE UPLOAD ---
    btnExecuteUpload.addEventListener("click", async () => {
        if (!uploadedFile) return;
        
        btnExecuteUpload.disabled = true;
        btnExecuteUpload.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Executing...`;
        
        const startTime = performance.now();
        const formData = new FormData();
        formData.append("file", uploadedFile);

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData
            });
            const duration = Math.round(performance.now() - startTime);
            const data = await parseResponse(response);
            
            displayResponse(response.status, response.statusText, duration, data, codeUpload, metaUpload, statusUpload, timeUpload);
            logHistory("POST /upload", response.status, duration);
        } catch (error) {
            const duration = Math.round(performance.now() - startTime);
            displayResponse(500, "Internal Error", duration, { error: error.message }, codeUpload, metaUpload, statusUpload, timeUpload);
            logHistory("POST /upload", 500, duration);
        } finally {
            btnExecuteUpload.disabled = false;
            btnExecuteUpload.innerHTML = `<i class="fa-solid fa-play"></i> Send Request`;
        }
    });

    // --- EXECUTE ANALYZE ---
    btnExecuteAnalyze.addEventListener("click", async () => {
        btnExecuteAnalyze.disabled = true;
        btnExecuteAnalyze.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Executing...`;
        
        const startTime = performance.now();

        try {
            const response = await fetch("/analyze", {
                method: "POST"
            });
            const duration = Math.round(performance.now() - startTime);
            const data = await parseResponse(response);
            
            displayResponse(response.status, response.statusText, duration, data, codeAnalyze, metaAnalyze, statusAnalyze, timeAnalyze);
            logHistory("POST /analyze", response.status, duration);
        } catch (error) {
            const duration = Math.round(performance.now() - startTime);
            displayResponse(500, "Internal Error", duration, { error: error.message }, codeAnalyze, metaAnalyze, statusAnalyze, timeAnalyze);
            logHistory("POST /analyze", 500, duration);
        } finally {
            btnExecuteAnalyze.disabled = false;
            btnExecuteAnalyze.innerHTML = `<i class="fa-solid fa-play"></i> Send Request`;
        }
    });

    // --- EXECUTE ASK ---
    btnExecuteAsk.addEventListener("click", async () => {
        const bodyText = textareaAskBody.value.trim();
        let payload;
        try {
            payload = JSON.parse(bodyText);
        } catch (e) {
            alert("Invalid JSON format in request body.");
            return;
        }

        btnExecuteAsk.disabled = true;
        btnExecuteAsk.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Executing...`;
        
        const startTime = performance.now();

        try {
            const response = await fetch("/ask", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });
            const duration = Math.round(performance.now() - startTime);
            const data = await parseResponse(response);
            
            displayResponse(response.status, response.statusText, duration, data, codeAsk, metaAsk, statusAsk, timeAsk);
            logHistory("POST /ask", response.status, duration);
        } catch (error) {
            const duration = Math.round(performance.now() - startTime);
            displayResponse(500, "Internal Error", duration, { error: error.message }, codeAsk, metaAsk, statusAsk, timeAsk);
            logHistory("POST /ask", 500, duration);
        } finally {
            btnExecuteAsk.disabled = false;
            btnExecuteAsk.innerHTML = `<i class="fa-solid fa-play"></i> Send Request`;
        }
    });

    // --- HELPER FUNCTIONS ---
    async function parseResponse(response) {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            return await response.json();
        } else {
            const text = await response.text();
            return { error: text || `HTTP ${response.status} ${response.statusText}` };
        }
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function displayResponse(statusCode, statusText, duration, body, codeElement, metaElement, statusElement, timeElement) {
        metaElement.classList.remove("hidden");
        statusElement.textContent = `${statusCode} ${statusText}`;
        timeElement.textContent = `${duration}ms`;

        if (statusCode >= 200 && statusCode < 300) {
            statusElement.className = "badge status-badge";
        } else {
            statusElement.className = "badge status-badge badge-error";
        }

        codeElement.textContent = JSON.stringify(body, null, 2);
    }

    function logHistory(endpoint, statusCode, duration) {
        const emptyMsg = historyContainer.querySelector(".history-empty");
        if (emptyMsg) {
            emptyMsg.remove();
        }

        const isSuccess = statusCode >= 200 && statusCode < 300;
        const statusClass = isSuccess ? "history-status-success" : "history-status-error";
        const icon = isSuccess ? "fa-solid fa-circle-check" : "fa-solid fa-circle-xmark";

        const logItem = document.createElement("div");
        logItem.className = "history-item fade-in";
        logItem.innerHTML = `
            <div class="history-item-left">
                <i class="${icon} ${statusClass}"></i>
                <span>${endpoint}</span>
            </div>
            <div class="history-item-right">
                <span class="history-time">${duration}ms</span>
            </div>
        `;
        
        historyContainer.prepend(logItem);
    }
});
