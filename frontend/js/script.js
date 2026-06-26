// ============================================================
// 🔧 ДЕМО-РЕЖИМ (РАБОТАЕТ БЕЗ БЭКЕНДА)
// ============================================================

console.log("🔄 Демо-режим загружен!");

let history = JSON.parse(localStorage.getItem("history") || "[]");
let selectedFile = null;

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const fileSelect = document.getElementById("fileSelect");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const progressContainer = document.getElementById("progressContainer");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const resultsSection = document.getElementById("results");
const historyList = document.getElementById("historyList");

if (dropZone) {
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

if (fileSelect) {
    fileSelect.addEventListener("click", (e) => {
        e.preventDefault();
        if (fileInput) fileInput.click();
    });
}

if (fileInput) {
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    const validExtensions = [".txt", ".pdf", ".docx", ".doc", ".rtf"];
    const ext = "." + file.name.split(".").pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
        alert("❌ Неподдерживаемый формат. Поддерживаются: " + validExtensions.join(", "));
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert("❌ Файл слишком большой. Максимальный размер: 10MB");
        return;
    }

    selectedFile = file;
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = (file.size / 1024).toFixed(1) + " KB";
    if (fileInfo) fileInfo.style.display = "inline-flex";
    if (analyzeBtn) analyzeBtn.disabled = false;
}

if (analyzeBtn) {
    analyzeBtn.addEventListener("click", analyzeFile);
}

async function analyzeFile() {
    if (!selectedFile) {
        alert("❌ Выберите файл!");
        return;
    }

    if (progressContainer) progressContainer.classList.add("active");
    if (analyzeBtn) analyzeBtn.disabled = true;
    if (resultsSection) resultsSection.style.display = "none";

    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 8 + 2;
        if (progress > 100) progress = 100;
        if (progressFill) progressFill.style.width = progress + "%";
        if (progressText) progressText.textContent = "⏳ Анализ... " + Math.round(progress) + "%";
    }, 300);

    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1500));

    clearInterval(interval);
    if (progressFill) progressFill.style.width = "100%";
    if (progressText) progressText.textContent = "✅ Готово!";

    const plagScore = Math.round(Math.random() * 35 + 60);
    const aiScore = Math.round(Math.random() * 35 + 5);

    setTimeout(() => {
        if (progressContainer) progressContainer.classList.remove("active");
        if (analyzeBtn) analyzeBtn.disabled = false;
        displayResults(plagScore, aiScore);
        saveToHistory(selectedFile.name, plagScore, aiScore);
        loadHistory();
    }, 500);
}

function displayResults(plagScore, aiScore) {
    if (resultsSection) resultsSection.style.display = "block";
    if (resultsSection) resultsSection.scrollIntoView({ behavior: "smooth" });

    const el = (id) => document.getElementById(id);

    if (el("plagiarismScore")) el("plagiarismScore").textContent = plagScore + "%";
    if (el("plagiarismBar")) el("plagiarismBar").style.width = plagScore + "%";
    if (el("aiScore")) el("aiScore").textContent = aiScore + "%";
    if (el("aiBar")) el("aiBar").style.width = aiScore + "%";

    if (el("textPreview")) {
        el("textPreview").textContent = "📄 Текст проанализирован. Результаты выше.";
    }

    const plagStatus = el("plagiarismStatus");
    if (plagStatus) {
        if (plagScore > 80) plagStatus.innerHTML = "<span class=\"badge badge-success\">✅ Высокая уникальность</span>";
        else if (plagScore > 60) plagStatus.innerHTML = "<span class=\"badge badge-warning\">⚠️ Средняя уникальность</span>";
        else plagStatus.innerHTML = "<span class=\"badge badge-danger\">❌ Низкая уникальность</span>";
    }

    const aiStatus = el("aiStatus");
    if (aiStatus) {
        if (aiScore < 30) aiStatus.innerHTML = "<span class=\"badge badge-success\">✅ Написано человеком</span>";
        else if (aiScore < 60) aiStatus.innerHTML = "<span class=\"badge badge-warning\">⚠️ Возможно ИИ</span>";
        else aiStatus.innerHTML = "<span class=\"badge badge-danger\">❌ Высокая вероятность ИИ</span>";
    }
}

function saveToHistory(filename, plagScore, aiScore) {
    history.unshift({ filename, date: new Date().toLocaleString("ru-RU"), plagScore, aiScore });
    if (history.length > 50) history = history.slice(0, 50);
    localStorage.setItem("history", JSON.stringify(history));
}

function loadHistory() {
    if (!historyList) return;
    if (history.length === 0) {
        historyList.innerHTML = "<div class=\"empty-state\"><i class=\"fas fa-inbox empty-icon\"></i><p>Пока нет проверок</p></div>";
        return;
    }
    historyList.innerHTML = history.map(item => `
        <div class="history-item">
            <div><div class="file-name">${item.filename}</div>
            <div style="display:flex;gap:10px;margin-top:4px;"><span class="file-date">${item.date}</span></div></div>
            <div class="scores"><span class="score score-plagiarism">🟢 ${item.plagScore}%</span><span class="score score-ai">🤖 ${item.aiScore}%</span></div>
        </div>
    `).join("");
}

if (clearBtn) {
    clearBtn.addEventListener("click", () => {
        selectedFile = null;
        if (fileInfo) fileInfo.style.display = "none";
        if (analyzeBtn) analyzeBtn.disabled = true;
        if (resultsSection) resultsSection.style.display = "none";
        if (progressContainer) progressContainer.classList.remove("active");
    });
}

const newCheckBtn = document.getElementById("newCheckBtn");
if (newCheckBtn) {
    newCheckBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
        if (resultsSection) resultsSection.style.display = "none";
        selectedFile = null;
        if (fileInfo) fileInfo.style.display = "none";
        if (analyzeBtn) analyzeBtn.disabled = true;
        if (progressContainer) progressContainer.classList.remove("active");
    });
}

const clearHistoryBtn = document.getElementById("clearHistoryBtn");
if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener("click", () => {
        if (confirm("Очистить всю историю?")) {
            history = [];
            localStorage.setItem("history", JSON.stringify(history));
            loadHistory();
        }
    });
}

loadHistory();
console.log("✅ ДЕМО-РЕЖИМ загружен!");
console.log("📊 Результаты генерируются случайно");
