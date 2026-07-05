// ============================================================
// 🔧 РЕАЛЬНЫЙ РЕЖИМ (РАБОТАЕТ С БЭКЕНДОМ)
// ============================================================

console.log("🔄 Подключение к бэкенду...");

const API_URL = 'http://127.0.0.1:8000/api';

let history = JSON.parse(localStorage.getItem("history") || "[]");
let selectedFile = null;
let currentDocumentId = null;

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

// Drag and Drop
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

    // Обновляем прогресс
    if (progressFill) progressFill.style.width = "0%";
    if (progressText) progressText.textContent = "⏳ Загрузка файла...";

    try {
        // 1. Загружаем файл
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('file_type', 'document');

        const uploadResponse = await fetch(`${API_URL}/upload/file`, {
            method: 'POST',
            body: formData
        });

        if (progressFill) progressFill.style.width = "40%";
        if (progressText) progressText.textContent = "⏳ Файл загружен, анализируем...";

        if (!uploadResponse.ok) {
            const error = await uploadResponse.json();
            throw new Error(error.detail || 'Ошибка загрузки файла');
        }

        const uploadResult = await uploadResponse.json();
        currentDocumentId = uploadResult.document_id;
        console.log('Файл загружен:', uploadResult);

        if (progressFill) progressFill.style.width = "60%";
        if (progressText) progressText.textContent = "⏳ Проверка на плагиат...";

        // 2. Проверка на плагиат
        const plagResponse = await fetch(`${API_URL}/analysis/plagiarism/${currentDocumentId}`, {
            method: 'POST'
        });

        if (!plagResponse.ok) {
            throw new Error('Ошибка проверки на плагиат');
        }

        const plagResult = await plagResponse.json();
        console.log('Результат плагиата:', plagResult);

        if (progressFill) progressFill.style.width = "80%";
        if (progressText) progressText.textContent = "⏳ Проверка на ИИ...";

        // 3. Проверка на ИИ
        const aiResponse = await fetch(`${API_URL}/analysis/ai-detection/${currentDocumentId}`, {
            method: 'POST'
        });

        if (!aiResponse.ok) {
            throw new Error('Ошибка проверки на ИИ');
        }

        const aiResult = await aiResponse.json();
        console.log('Результат ИИ:', aiResult);

        if (progressFill) progressFill.style.width = "100%";
        if (progressText) progressText.textContent = "✅ Готово!";

        // Отображаем результаты
        setTimeout(() => {
            if (progressContainer) progressContainer.classList.remove("active");
            if (analyzeBtn) analyzeBtn.disabled = false;

            // Показываем результаты
            displayResults(plagResult, aiResult, uploadResult);

            // Сохраняем в историю
            saveToHistory(selectedFile.name, plagResult.similarity_score, aiResult.ai_probability);
            loadHistory();
        }, 500);

    } catch (error) {
        console.error('Ошибка:', error);
        if (progressText) progressText.textContent = "❌ Ошибка: " + error.message;
        if (progressFill) progressFill.style.width = "100%";
        if (progressFill) progressFill.style.background = "#dc3545";

        setTimeout(() => {
            if (progressContainer) progressContainer.classList.remove("active");
            if (analyzeBtn) analyzeBtn.disabled = false;
            alert('❌ Ошибка анализа: ' + error.message);
        }, 2000);
    }
}

function displayResults(plagResult, aiResult, uploadResult) {
    if (resultsSection) resultsSection.style.display = "block";
    if (resultsSection) resultsSection.scrollIntoView({ behavior: "smooth" });

    const el = (id) => document.getElementById(id);

    // Плагиат
    const plagScore = Math.round(plagResult.similarity_score || 0);
    if (el("plagiarismScore")) el("plagiarismScore").textContent = plagScore + "%";
    if (el("plagiarismBar")) el("plagiarismBar").style.width = plagScore + "%";

    // Уникальные фразы
    if (el("uniquePhrases")) {
        const unique = plagResult.unique_phrases_percentage || 0;
        el("uniquePhrases").textContent = unique + "%";
    }
    if (el("sentencesCount")) {
        el("sentencesCount").textContent = plagResult.total_sentences || 0;
    }

    // ИИ
    const aiScore = Math.round(aiResult.ai_probability || 0);
    if (el("aiScore")) el("aiScore").textContent = aiScore + "%";
    if (el("aiBar")) el("aiBar").style.width = aiScore + "%";

    if (el("confidenceLevel")) el("confidenceLevel").textContent = aiResult.confidence_level || "-";
    if (el("readabilityScore")) el("readabilityScore").textContent = aiResult.readability_score || "-";

    // Статусы
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

    // Детали
    if (el("matchedSources")) {
        const sources = plagResult.matched_sources || [];
        el("matchedSources").textContent = sources.length > 0 ? sources.join(', ') : '0';
    }
    if (el("suspiciousPatterns")) {
        const patterns = aiResult.suspicious_patterns || [];
        el("suspiciousPatterns").textContent = patterns.length > 0 ? patterns.join(', ') : 'Нет';
    }
    if (el("avgSentenceLength")) {
        el("avgSentenceLength").textContent = aiResult.avg_sentence_length || 0;
    }

    // Превью текста
    if (el("textPreview")) {
        const preview = uploadResult.content_preview || "Текст проанализирован";
        el("textPreview").textContent = preview;
    }
}

function saveToHistory(filename, plagScore, aiScore) {
    history.unshift({
        filename,
        date: new Date().toLocaleString("ru-RU"),
        plagScore: Math.round(plagScore || 0),
        aiScore: Math.round(aiScore || 0)
    });
    if (history.length > 50) history = history.slice(0, 50);
    localStorage.setItem("history", JSON.stringify(history));
}

function loadHistory() {
    if (!historyList) return;
    if (history.length === 0) {
        historyList.innerHTML = `<div class="empty-state">
            <i class="fas fa-inbox empty-icon"></i>
            <p>Пока нет проверок</p>
            <p class="empty-sub">Загрузите файл для начала</p>
        </div>`;
        return;
    }
    historyList.innerHTML = history.map(item => `
        <div class="history-item">
            <div>
                <div class="file-name">${item.filename}</div>
                <div style="display:flex;gap:10px;margin-top:4px;">
                    <span class="file-date">${item.date}</span>
                </div>
            </div>
            <div class="scores">
                <span class="score score-plagiarism">🟢 ${item.plagScore}%</span>
                <span class="score score-ai">🤖 ${item.aiScore}%</span>
            </div>
        </div>
    `).join("");
}

// Очистка
if (clearBtn) {
    clearBtn.addEventListener("click", () => {
        selectedFile = null;
        currentDocumentId = null;
        if (fileInfo) fileInfo.style.display = "none";
        if (analyzeBtn) analyzeBtn.disabled = true;
        if (resultsSection) resultsSection.style.display = "none";
        if (progressContainer) progressContainer.classList.remove("active");
        if (progressFill) {
            progressFill.style.width = "0%";
            progressFill.style.background = "#4f46e5";
        }
    });
}

// Новая проверка
const newCheckBtn = document.getElementById("newCheckBtn");
if (newCheckBtn) {
    newCheckBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
        if (resultsSection) resultsSection.style.display = "none";
        selectedFile = null;
        currentDocumentId = null;
        if (fileInfo) fileInfo.style.display = "none";
        if (analyzeBtn) analyzeBtn.disabled = true;
        if (progressContainer) progressContainer.classList.remove("active");
        if (progressFill) {
            progressFill.style.width = "0%";
            progressFill.style.background = "#4f46e5";
        }
    });
}

// Очистка истории
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

// Загрузка истории при старте
loadHistory();
console.log("✅ Режим с бэкендом загружен!");
console.log(`📡 API URL: ${API_URL}`);

// Проверка соединения с бэкендом
async function checkBackend() {
    try {
        const response = await fetch('http://127.0.0.1:8000/health');
        if (response.ok) {
            console.log('✅ Бэкенд доступен!');
        } else {
            console.warn('⚠️ Бэкенд не отвечает');
        }
    } catch (error) {
        console.warn('⚠️ Бэкенд не доступен:', error.message);
    }
}
checkBackend();