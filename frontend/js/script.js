// ============================================================
// 🔧 ДЕМО-РЕЖИМ (РАБОТАЕТ БЕЗ БЭКЕНДА)
// ============================================================

let history = JSON.parse(localStorage.getItem('history') || '[]');

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileSelect = document.getElementById('fileSelect');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('results');
const historyList = document.getElementById('historyList');

let selectedFile = null;

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileSelect.addEventListener('click', (e) => {
    e.preventDefault();
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    const validExtensions = ['.txt', '.pdf', '.docx', '.doc', '.rtf'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
        alert('❌ Неподдерживаемый формат. Поддерживаются: ' + validExtensions.join(', '));
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert('❌ Файл слишком большой. Максимальный размер: 10MB');
        return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = (file.size / 1024).toFixed(1) + ' KB';
    fileInfo.style.display = 'inline-flex';
    analyzeBtn.disabled = false;
}

analyzeBtn.addEventListener('click', analyzeFile);

async function analyzeFile() {
    if (!selectedFile) return;

    progressContainer.classList.add('active');
    analyzeBtn.disabled = true;
    resultsSection.style.display = 'none';

    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 8 + 2;
        if (progress > 100) progress = 100;
        progressFill.style.width = progress + '%';
        progressText.textContent = '⏳ Анализ текста... ' + Math.round(progress) + '%';
    }, 300);

    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1500));

    clearInterval(interval);
    progressFill.style.width = '100%';
    progressText.textContent = '✅ Анализ завершен!';

    const plagScore = Math.round(Math.random() * 35 + 60);
    const aiScore = Math.round(Math.random() * 35 + 5);
    const uniquePhrases = Math.round(Math.random() * 30 + 65);
    const sentences = Math.floor(Math.random() * 50 + 10);
    const matchedSources = Math.floor(Math.random() * 6);
    const readability = Math.round(Math.random() * 30 + 60);
    const avgLength = (Math.random() * 10 + 8).toFixed(1);

    setTimeout(() => {
        progressContainer.classList.remove('active');
        analyzeBtn.disabled = false;
        displayResults(plagScore, aiScore, uniquePhrases, sentences, matchedSources, readability, avgLength);
        saveToHistory(selectedFile.name, plagScore, aiScore);
        loadHistory();
    }, 500);
}

function displayResults(plagScore, aiScore, uniquePhrases, sentences, matchedSources, readability, avgLength) {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });

    document.getElementById('plagiarismScore').textContent = plagScore + '%';
    document.getElementById('plagiarismBar').style.width = plagScore + '%';
    document.getElementById('uniquePhrases').textContent = uniquePhrases + '%';
    document.getElementById('sentencesCount').textContent = sentences;
    document.getElementById('matchedSources').textContent = matchedSources;

    document.getElementById('aiScore').textContent = aiScore + '%';
    document.getElementById('aiBar').style.width = aiScore + '%';
    document.getElementById('confidenceLevel').textContent = aiScore > 35 ? 'Средняя' : 'Низкая';
    document.getElementById('readabilityScore').textContent = readability + '%';
    document.getElementById('suspiciousPatterns').textContent = aiScore > 30 ? 'Обнаружены' : 'Не обнаружены';
    document.getElementById('avgSentenceLength').textContent = avgLength;

    document.getElementById('textPreview').textContent =
        '📄 Текст успешно проанализирован. Результаты проверки на плагиат и ИИ представлены выше.';

    const plagStatus = document.getElementById('plagiarismStatus');
    if (plagScore > 80) {
        plagStatus.innerHTML = '<span class="badge badge-success">✅ Высокая уникальность</span>';
    } else if (plagScore > 60) {
        plagStatus.innerHTML = '<span class="badge badge-warning">⚠️ Средняя уникальность</span>';
    } else {
        plagStatus.innerHTML = '<span class="badge badge-danger">❌ Низкая уникальность</span>';
    }

    const aiStatus = document.getElementById('aiStatus');
    if (aiScore < 30) {
        aiStatus.innerHTML = '<span class="badge badge-success">✅ Написано человеком</span>';
    } else if (aiScore < 60) {
        aiStatus.innerHTML = '<span class="badge badge-warning">⚠️ Возможно ИИ</span>';
    } else {
        aiStatus.innerHTML = '<span class="badge badge-danger">❌ Высокая вероятность ИИ</span>';
    }
}

function saveToHistory(filename, plagScore, aiScore) {
    history.unshift({
        filename: filename,
        date: new Date().toLocaleString('ru-RU'),
        plagScore: plagScore,
        aiScore: aiScore
    });
    if (history.length > 50) history = history.slice(0, 50);
    localStorage.setItem('history', JSON.stringify(history));
}

function loadHistory() {
    if (history.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox empty-icon"></i>
                <p>Пока нет проверок</p>
                <p class="empty-sub">Загрузите файл для начала</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = history.map(item => `
        <div class="history-item">
            <div>
                <div class="file-name">${item.filename}</div>
                <div style="display: flex; gap: 10px; align-items: center; margin-top: 4px;">
                    <span class="file-date">${item.date}</span>
                </div>
            </div>
            <div class="scores">
                <span class="score score-plagiarism">🟢 ${item.plagScore}%</span>
                <span class="score score-ai">🤖 ${item.aiScore}%</span>
            </div>
        </div>
    `).join('');
}

clearBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInfo.style.display = 'none';
    analyzeBtn.disabled = true;
    resultsSection.style.display = 'none';
    progressContainer.classList.remove('active');
});

document.getElementById('newCheckBtn').addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    resultsSection.style.display = 'none';
    selectedFile = null;
    fileInfo.style.display = 'none';
    analyzeBtn.disabled = true;
    progressContainer.classList.remove('active');
});

document.getElementById('clearHistoryBtn').addEventListener('click', () => {
    if (confirm('Очистить всю историю?')) {
        history = [];
        localStorage.setItem('history', JSON.stringify(history));
        loadHistory();
    }
});

loadHistory();
console.log('✅ Plagiarism & AI Detector (ДЕМО-РЕЖИМ) загружен!');
console.log('📊 Результаты генерируются случайно для демонстрации');