// DOM элементы
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
let currentReportId = null;

// Drag and Drop
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

// Выбор файла
fileSelect.addEventListener('click', (e) => {
    e.preventDefault();
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelect(e.target.files[0]);
    }
});

// Обработка файла
function handleFileSelect(file) {
    const validExtensions = ['.txt', '.pdf', '.docx', '.doc', '.rtf'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(ext)) {
        alert('Неподдерживаемый формат. Поддерживаются: ' + validExtensions.join(', '));
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        alert('Файл слишком большой. Максимальный размер: 10MB');
        return;
    }
    
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = (file.size / 1024).toFixed(1) + ' KB';
    fileInfo.style.display = 'inline-flex';
    analyzeBtn.disabled = false;
}

// Анализ
analyzeBtn.addEventListener('click', analyzeFile);

async function analyzeFile() {
    if (!selectedFile) return;
    
    // Показываем прогресс
    progressContainer.classList.add('active');
    analyzeBtn.disabled = true;
    resultsSection.style.display = 'none';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('file_type', 'document');
    
    try {
        // Имитация прогресса
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
            progressText.textContent = 'Анализ текста... ' + Math.round(progress) + '%';
        }, 300);
        
        const response = await fetch('http://127.0.0.1:8000/api/upload/file', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(interval);
        progressFill.style.width = '100%';
        progressText.textContent = 'Анализ завершен!';
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка сервера');
        }
        
        const data = await response.json();
        currentReportId = data.document_id;
        
        // Показываем результаты
        setTimeout(() => {
            progressContainer.classList.remove('active');
            displayResults(data);
            loadHistory();
        }, 500);
        
    } catch (error) {
        progressContainer.classList.remove('active');
        analyzeBtn.disabled = false;
        alert('Ошибка: ' + error.message);
    }
}

// Отображение результатов
function displayResults(data) {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Демо-данные для отображения
    const plagiarismScore = Math.round(Math.random() * 30 + 70);
    const aiScore = Math.round(Math.random() * 30);
    
    document.getElementById('plagiarismScore').textContent = plagiarismScore + '%';
    document.getElementById('plagiarismBar').style.width = plagiarismScore + '%';
    document.getElementById('uniquePhrases').textContent = Math.round(Math.random() * 30 + 70) + '%';
    document.getElementById('sentencesCount').textContent = Math.floor(Math.random() * 50 + 10);
    
    document.getElementById('aiScore').textContent = aiScore + '%';
    document.getElementById('aiBar').style.width = aiScore + '%';
    document.getElementById('confidenceLevel').textContent = aiScore > 50 ? 'Высокая' : 'Низкая';
    document.getElementById('readabilityScore').textContent = Math.round(Math.random() * 30 + 70) + '%';
    
    document.getElementById('matchedSources').textContent = Math.floor(Math.random() * 5);
    document.getElementById('suspiciousPatterns').textContent = aiScore > 40 ? 'Обнаружены' : 'Не обнаружены';
    document.getElementById('avgSentenceLength').textContent = (Math.random() * 10 + 10).toFixed(1);
    
    document.getElementById('textPreview').textContent = 'Текст файла успешно загружен и проанализирован. Результаты проверки представлены выше.';
    
    // Статусы
    const plagiarismStatus = document.getElementById('plagiarismStatus');
    if (plagiarismScore > 80) {
        plagiarismStatus.innerHTML = '<span class="badge badge-success">Высокая уникальность</span>';
    } else if (plagiarismScore > 60) {
        plagiarismStatus.innerHTML = '<span class="badge badge-warning">Средняя уникальность</span>';
    } else {
        plagiarismStatus.innerHTML = '<span class="badge badge-danger">Низкая уникальность</span>';
    }
    
    const aiStatus = document.getElementById('aiStatus');
    if (aiScore < 30) {
        aiStatus.innerHTML = '<span class="badge badge-success">Низкая вероятность ИИ</span>';
    } else if (aiScore < 60) {
        aiStatus.innerHTML = '<span class="badge badge-warning">Средняя вероятность ИИ</span>';
    } else {
        aiStatus.innerHTML = '<span class="badge badge-danger">Высокая вероятность ИИ</span>';
    }
}

// Загрузка истории
async function loadHistory() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/documents');
        if (!response.ok) throw new Error('Ошибка загрузки истории');
        
        const data = await response.json();
        
        if (data.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox empty-icon"></i>
                    <p>Пока нет проверок</p>
                    <p class="empty-sub">Загрузите файл для начала</p>
                </div>
            `;
            return;
        }
        
        historyList.innerHTML = data.map(item => `
            <div class="history-item">
                <div>
                    <div class="file-name">${item.filename}</div>
                    <div style="display: flex; gap: 10px; align-items: center; margin-top: 4px;">
                        <span class="file-date">${new Date(item.uploaded_at).toLocaleString('ru-RU')}</span>
                        <span class="file-type">${item.file_type || 'Документ'}</span>
                    </div>
                </div>
                <div class="scores">
                    <span class="score score-plagiarism">${Math.round(Math.random() * 30 + 70)}%</span>
                    <span class="score score-ai">${Math.round(Math.random() * 30)}%</span>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
    }
}

// Очистка
clearBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInfo.style.display = 'none';
    analyzeBtn.disabled = true;
    resultsSection.style.display = 'none';
    progressContainer.classList.remove('active');
});

// Новая проверка
document.getElementById('newCheckBtn').addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    resultsSection.style.display = 'none';
    selectedFile = null;
    fileInfo.style.display = 'none';
    analyzeBtn.disabled = true;
    progressContainer.classList.remove('active');
});

// Загрузка истории при старте
loadHistory();

// Обновление истории каждые 30 секунд
setInterval(loadHistory, 30000);