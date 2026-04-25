const API_BASE = '/api';
let currentStudentId = 'S001';
let performanceChart = null;
let currentQuizContent = null;
let libraryContent = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStudents();
    setupEventListeners();
});

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // Student selection
    document.getElementById('studentSelect').addEventListener('change', (e) => {
        currentStudentId = e.target.value;
        loadDashboard();
    });

    // Library filters
    document.getElementById('librarySearch').addEventListener('input', () => displayLibrary(libraryContent));
    document.getElementById('subjectFilter').addEventListener('change', () => displayLibrary(libraryContent));

    // Modal close
    document.querySelector('.close').onclick = () => {
        document.getElementById('quizModal').style.display = "none";
    };

    // Quiz submit
    document.getElementById('submitQuizBtn').onclick = submitQuiz;

    window.onclick = (event) => {
        if (event.target == document.getElementById('quizModal')) {
            document.getElementById('quizModal').style.display = "none";
        }
    };
}

async function loadStudents() {
    const response = await fetch(`${API_BASE}/students`);
    const students = await response.json();
    
    const select = document.getElementById('studentSelect');
    select.innerHTML = students.map(s => `<option value="${s.student_id}">${s.name}</option>`).join('');
    
    if (students.length > 0) {
        currentStudentId = students[0].student_id;
        loadDashboard();
    }
}

async function loadDashboard() {
    // 1. Load Profile and Analytics
    const response = await fetch(`${API_BASE}/student/${currentStudentId}`);
    const data = await response.json();
    
    updateProfileUI(data.profile);
    if (data.analytics) {
        updateStatsUI(data.analytics);
        updateChart(data.analytics);
        updateActivityTable(data.analytics.history);
    }

    // 2. Load Recommendations & Pathway
    const recResponse = await fetch(`${API_BASE}/recommendations/${currentStudentId}`);
    const recs = await recResponse.json();
    displayRecommendations(recs);
    displayPathway(recs);

    // 3. Load Library
    const libResponse = await fetch(`${API_BASE}/content`);
    const content = await libResponse.json();
    libraryContent = content;
    displayLibrary(libraryContent);
}

function updateActivityTable(history) {
    const tbody = document.querySelector('#activityTable tbody');
    if (!tbody) return;
    tbody.innerHTML = history.map(row => `
        <tr>
            <td>${row.title}</td>
            <td>${row.type}</td>
            <td>${row.score !== null ? row.score : '-'}</td>
            <td>${row.time_spent}m</td>
            <td>${new Date(row.timestamp).toLocaleDateString()}</td>
        </tr>
    `).join('');
}

function updateProfileUI(profile) {
    document.getElementById('studentName').textContent = profile.name;
    document.getElementById('studentLevel').textContent = profile.level;
    document.getElementById('studentInterests').textContent = profile.interests;
}

function updateStatsUI(analytics) {
    document.getElementById('avgScore').textContent = `${Math.round(analytics.avg_score)}%`;
    document.getElementById('totalTime').textContent = `${analytics.total_time}m`;
    document.getElementById('completedCount').textContent = analytics.completed_count;
    
    // Predictive UI
    const trendEl = document.getElementById('growthTrend');
    if (trendEl) {
        trendEl.textContent = analytics.trend;
        trendEl.style.color = analytics.trend === 'Improving' ? '#4ade80' : 
                             analytics.trend === 'Declining' ? '#f87171' : 'white';
    }
    const predEl = document.getElementById('predictedScore');
    if (predEl) predEl.textContent = Math.round(analytics.predicted_next);
}

function displayPathway(items) {
    const pathwayList = document.getElementById('pathwayList');
    if (!pathwayList) return;
    if (!items || !items.adaptive || items.adaptive.length === 0) {
        pathwayList.innerHTML = '<div class="empty-state">No adaptive learning path is available yet. Complete a quiz to generate recommendations.</div>';
        return;
    }

    pathwayList.innerHTML = items.adaptive.map((item, index) => `
        <div class="pathway-item">
            <div class="pathway-node">${index + 1}</div>
            <div class="pathway-content">
                <h4>${item.title}</h4>
                <p><small>${item.subject} • ${item.type}</small></p>
                <button class="btn-learn" onclick="openQuiz('${item.content_id}', '${item.title}', '${item.subject}')">
                    Launch Step
                </button>
            </div>
        </div>
    `).join('');
}

function openQuiz(contentId, title, subject) {
    currentQuizContent = { contentId, title, subject };
    document.getElementById('quizTitle').textContent = `Quiz: ${title}`;
    document.getElementById('quizSubject').textContent = subject;
    document.getElementById('quizModal').style.display = "block";
}

async function submitQuiz() {
    const score = parseInt(document.getElementById('quizScore').value);
    const response = await fetch(`${API_BASE}/quiz/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            student_id: currentStudentId,
            content_id: currentQuizContent.contentId,
            score: score
        })
    });

    if (response.ok) {
        document.getElementById('quizModal').style.display = "none";
        loadDashboard(); // Refresh UI with new data
        alert('Assessment recorded! Your learning path has been updated.');
    }
}

function updateChart(analytics) {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    
    if (performanceChart) {
        performanceChart.destroy();
    }

    const subjects = Object.keys(analytics.subject_performance);
    const scores = Object.values(analytics.subject_performance);

    performanceChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: subjects,
            datasets: [{
                label: 'Subject Proficiency',
                data: scores,
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                borderColor: '#6366f1',
                pointBackgroundColor: '#6366f1',
                borderWidth: 2
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { stepSize: 20 }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function displayRecommendations(data) {
    const adaptiveGrid = document.getElementById('adaptiveRecs');
    const contentGrid = document.getElementById('contentRecs');
    
    if (adaptiveGrid) {
        adaptiveGrid.innerHTML = (data.adaptive && data.adaptive.length > 0)
            ? data.adaptive.map(item => createRecCard(item)).join('')
            : '<div class="empty-state">No adaptive recommendations available.</div>';
    }

    if (contentGrid) {
        contentGrid.innerHTML = (data.content_based && data.content_based.length > 0)
            ? data.content_based.map(item => createRecCard(item)).join('')
            : '<div class="empty-state">No content recommendations available.</div>';
    }
}

function createRecCard(item) {
    let actionHtml = `<button class="btn-learn" onclick="openQuiz('${item.content_id}', '${item.title}', '${item.subject}')">Take Quiz</button>`;
    
    if (item.type === 'Video' && item.url) {
        actionHtml = `
            <div class="video-container" style="margin-top: 10px;">
                <iframe width="100%" height="150" src="${item.url}" frameborder="0" allowfullscreen></iframe>
            </div>
            <button class="btn-learn" onclick="openQuiz('${item.content_id}', '${item.title}', '${item.subject}')">Mark as Watched</button>
        `;
    }

    return `
        <div class="rec-card">
            <h4>${item.title}</h4>
            <p><small>${item.subject}</small></p>
            <div class="tags">
                <span class="tag">${item.type}</span>
                <span class="tag">Diff: ${item.difficulty}</span>
            </div>
            ${actionHtml}
        </div>
    `;
}

function displayLibrary(items) {
    const searchValue = document.getElementById('librarySearch').value.toLowerCase();
    const filterSelect = document.getElementById('subjectFilter');
    const selectedSubject = filterSelect.value;
    const tbody = document.querySelector('#libraryTable tbody');
    if (!tbody) return;

    const subjects = Array.from(new Set(items.map(item => item.subject).filter(Boolean))).sort();
    const currentSelection = filterSelect.value;
    filterSelect.innerHTML = '<option value="">All Subjects</option>' + subjects.map(sub => `
        <option value="${sub}">${sub}</option>
    `).join('');
    filterSelect.value = subjects.includes(currentSelection) ? currentSelection : '';

    const filtered = items.filter(item => {
        const matchesSearch = [item.title, item.subject, item.type].join(' ').toLowerCase().includes(searchValue);
        const matchesSubject = filterSelect.value ? item.subject === filterSelect.value : true;
        return matchesSearch && matchesSubject;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No resources match your search.</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(item => `
        <tr>
            <td>${item.title}</td>
            <td>${item.subject}</td>
            <td>${item.type}</td>
            <td>${'⭐'.repeat(item.difficulty)}</td>
        </tr>
    `).join('');
}
