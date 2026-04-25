from flask import Flask, render_template_string, request
import csv
import json
import numpy as np

app = Flask(__name__)

# Load data
def load_data():
    students = list(csv.DictReader(open('data/students.csv')))
    content = list(csv.DictReader(open('data/content.csv')))
    interactions = list(csv.DictReader(open('data/interactions.csv')))
    return students, content, interactions

students, content, interactions = load_data()

# Simple AI Recommender (without sklearn)
class SimpleAIRecommender:
    def __init__(self, content_list):
        self.content = content_list
    
    def get_recommendations(self, student_id, top_n=5):
        student_interactions = [i for i in interactions if i['student_id'] == student_id]
        
        if not student_interactions:
            return sorted(self.content, key=lambda x: float(x.get('difficulty', 0)), reverse=True)[:top_n]
        
        # Get subjects student has interacted with
        interacted_content_ids = [i['content_id'] for i in student_interactions]
        interacted_subjects = set()
        for cid in interacted_content_ids:
            for c in self.content:
                if c['content_id'] == cid:
                    interacted_subjects.add(c.get('subject', ''))
        
        # Recommend similar content
        recommendations = []
        for c in self.content:
            if c['content_id'] not in interacted_content_ids:
                if c.get('subject', '') in interacted_subjects:
                    recommendations.append(c)
        
        return recommendations[:top_n] if recommendations else self.content[:top_n]

ai_recommender = SimpleAIRecommender(content)

# Adaptive Learning Path
def generate_adaptive_path(student_id):
    student_interactions = [i for i in interactions if i['student_id'] == student_id]
    
    if not student_interactions:
        return sorted(content, key=lambda x: float(x.get('difficulty', 0)))[:5]
    
    scores = [float(i.get('score', 0)) for i in student_interactions if i.get('score')]
    avg_score = np.mean(scores) if scores else 0
    
    if avg_score >= 85:
        path = sorted(content, key=lambda x: float(x.get('difficulty', 0)), reverse=True)[:5]
    elif avg_score >= 70:
        path = [c for c in content if 2 <= float(c.get('difficulty', 0)) <= 3][:5]
    else:
        path = sorted(content, key=lambda x: float(x.get('difficulty', 0)))[:5]
    
    return path

@app.route('/')
def index():
    selected_student_id = request.args.get('student', 'S001')
    student = next((s for s in students if s['student_id'] == selected_student_id), students[0])
    
    recommendations = ai_recommender.get_recommendations(selected_student_id, 5)
    adaptive_path = generate_adaptive_path(selected_student_id)
    
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Personalized Learning System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; width: 100vw; height: 100vh; overflow-x: hidden; }
        .container { display: flex; flex-direction: column; height: 100vh; }
        header { text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .content { display: flex; flex: 1; }
        .sidebar { width: 300px; flex-shrink: 0; background: white; padding: 20px; box-shadow: 2px 0 10px rgba(0,0,0,0.1); overflow-y: auto; }
        .main { flex: 1; padding: 20px; overflow-y: auto; background: white; }
        .tabs { display: flex; border-bottom: 1px solid #ddd; }
        .tab { padding: 10px; cursor: pointer; background: #eee; border-radius: 5px 5px 0 0; transition: all 0.3s; }
        .tab:hover { background: #ddd; }
        .tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .tab-content { display: none; padding: 20px; }
        .tab-content.active { display: block; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 8px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .ai-badge { display: inline-block; background: #ff6b6b; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.8em; margin-left: 10px; }
        .chart { margin: 20px 0; }
        .expander { margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: #f8f9fa; transition: all 0.3s; }
        .expander:hover { background: #e9ecef; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .expander-content { display: none; }
        .expander.active .expander-content { display: block; }
        .button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 10px 15px; cursor: pointer; border-radius: 5px; margin: 5px; transition: all 0.3s; }
        .button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .columns { display: flex; flex-wrap: wrap; }
        .column { flex: 1; min-width: 200px; margin: 5px; }
        footer { text-align: center; padding: 20px; background: white; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); }
        .ai-section { background: #f0f7ff; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎓 AI-Based Personalized Learning System <span class="ai-badge">🤖 AI POWERED</span></h1>
            <p>Intelligent adaptive learning recommendations powered by machine learning.</p>
        </header>
        
        <div class="content">
            <div class="sidebar">
                <h3>👤 Student Profile</h3>
                <form method="get">
                    <select name="student" onchange="this.form.submit()">
                        {% for s in students %}
                        <option value="{{ s.student_id }}" {% if s.student_id == selected_student_id %}selected{% endif %}>{{ s.name }}</option>
                        {% endfor %}
                    </select>
                </form>
                <div id="studentInfo">
                    <p><strong>Name:</strong> {{ student.name }}</p>
                    <p><strong>Level:</strong> {{ student.level }}</p>
                    <p><strong>Interests:</strong> {{ student.interests }}</p>
                </div>
                
                <div class="ai-section">
                    <h4>🧠 AI Analysis</h4>
                    <p><small>The AI recommender analyzes your learning patterns and suggests the best resources for your learning style.</small></p>
                </div>
            </div>
            
            <div class="main">
                <div class="tabs">
                    <div class="tab active" onclick="showTab(0)">📊 Performance Dashboard</div>
                    <div class="tab" onclick="showTab(1)">🤖 AI Recommendations</div>
                    <div class="tab" onclick="showTab(2)">📈 Adaptive Learning Path</div>
                    <div class="tab" onclick="showTab(3)">📚 All Materials</div>
                </div>
                
                <div id="tab0" class="tab-content active">
                    <h2>Performance Overview</h2>
                    <div class="columns">
                        <div class="column"><div class="metric" id="avgScore">Avg Score: 85%</div></div>
                        <div class="column"><div class="metric" id="totalTime">Time Spent: 120 mins</div></div>
                        <div class="column"><div class="metric" id="completed">Completed: 10</div></div>
                    </div>
                    <div class="chart">
                        <h3>Subject-wise Performance</h3>
                        <canvas id="performanceChart"></canvas>
                    </div>
                    <h3>Recent Activity</h3>
                    <table>
                        <thead>
                            <tr><th>Title</th><th>Type</th><th>Score</th><th>Time</th><th>Date</th></tr>
                        </thead>
                        <tbody id="activityTable"></tbody>
                    </table>
                </div>
                
                <div id="tab1" class="tab-content">
                    <h2>🤖 AI-Generated Recommendations <span class="ai-badge">ML Powered</span></h2>
                    <div class="ai-section">
                        <p><strong>Based on:</strong> Subject Similarity + Learning History</p>
                    </div>
                    <div id="recommendations"></div>
                </div>
                
                <div id="tab2" class="tab-content">
                    <h2>📈 Your Adaptive Learning Path</h2>
                    <div class="ai-section">
                        <p><strong>💡 AI Insight:</strong> Your learning path adjusts based on your performance scores.</p>
                    </div>
                    <div id="adaptivePath"></div>
                </div>
                
                <div id="tab3" class="tab-content">
                    <h2>📚 All Learning Materials</h2>
                    <input type="text" id="search" placeholder="Search resources..." onkeyup="filterMaterials()">
                    <select id="subjectFilter" multiple onchange="filterMaterials()">
                        <option>Mathematics</option>
                        <option>Physics</option>
                    </select>
                    <table>
                        <thead>
                            <tr><th>ID</th><th>Title</th><th>Type</th><th>Subject</th><th>Difficulty</th><th>URL</th></tr>
                        </thead>
                        <tbody id="materialsTable"></tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <footer>
            <p>🤖 AI-Based Personalized Learning System © 2026 | Powered by Smart Algorithms</p>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const students = {{ students|tojson }};
        const content = {{ content|tojson }};
        const interactions = {{ interactions|tojson }};
        const recommendations = {{ recs|tojson }};
        const adaptivePath = {{ adaptive|tojson }};
        let selectedStudentId = '{{ selected_student_id }}';

        function showTab(index) {
            const tabs = document.querySelectorAll('.tab');
            const contents = document.querySelectorAll('.tab-content');
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            tabs[index].classList.add('active');
            contents[index].classList.add('active');
        }

        function updateDashboard() {
            const studentInts = interactions.filter(i => i.student_id === selectedStudentId);
            const avgScore = studentInts.length ? (studentInts.reduce((sum, i) => sum + (parseFloat(i.score) || 0), 0) / studentInts.length).toFixed(1) : 0;
            const totalTime = studentInts.reduce((sum, i) => sum + parseInt(i.time_spent), 0);
            document.getElementById('avgScore').textContent = `Avg Score: ${avgScore}%`;
            document.getElementById('totalTime').textContent = `Time Spent: ${totalTime} mins`;
            document.getElementById('completed').textContent = `Completed: ${studentInts.length}`;

            const subjectPerf = {};
            studentInts.forEach(i => {
                const subj = content.find(c => c.content_id === i.content_id)?.subject;
                if (subj) subjectPerf[subj] = (subjectPerf[subj] || []).concat(parseFloat(i.score) || 0);
            });
            const labels = Object.keys(subjectPerf);
            const data = labels.map(s => subjectPerf[s].reduce((a, b) => a + b, 0) / subjectPerf[s].length);
            new Chart(document.getElementById('performanceChart').getContext('2d'), {
                type: 'bar',
                data: { labels, datasets: [{ label: 'Avg Score', data, backgroundColor: 'rgba(102, 126, 234, 0.6)' }] }
            });

            const table = document.getElementById('activityTable');
            table.innerHTML = studentInts.slice(-10).map(i => `<tr><td>${i.title}</td><td>${i.type}</td><td>${i.score || 'N/A'}</td><td>${i.time_spent}</td><td>${i.timestamp}</td></tr>`).join('');
        }

        function updateRecommendations() {
            const recDiv = document.getElementById('recommendations');
            recDiv.innerHTML = recommendations.map(rec => {
                let actionHtml = `<button class="button">Start Learning</button>`;
                
                if (rec.type === 'Video' && rec.url) {
                    actionHtml = `
                        <div style="margin-top: 10px;">
                            <iframe width="100%" height="200" src="${rec.url}" frameborder="0" allowfullscreen></iframe>
                        </div>
                        <button class="button">Mark as Watched</button>
                    `;
                }
                
                return `
                    <div class="expander" onclick="toggleExpander(this)">
                        <strong>⭐ ${rec.title}</strong> - ${rec.type}
                        <div class="expander-content">
                            <p><strong>Subject:</strong> ${rec.subject}</p>
                            <p><strong>Difficulty:</strong> ${'⭐'.repeat(parseInt(rec.difficulty))}</p>
                            ${actionHtml}
                        </div>
                    </div>
                `;
            }).join('');
        }

        function updateAdaptivePath() {
            const pathDiv = document.getElementById('adaptivePath');
            pathDiv.innerHTML = adaptivePath.map((rec, idx) => `
                <div class="expander">
                    <strong>Step ${idx + 1}: ${rec.title}</strong>
                    <p>Difficulty: ${'⭐'.repeat(parseInt(rec.difficulty))}</p>
                </div>
            `).join('');
        }

        function toggleExpander(el) {
            el.classList.toggle('active');
        }

        function filterMaterials() {
            const search = document.getElementById('search').value.toLowerCase();
            const filtered = content.filter(c => c.title.toLowerCase().includes(search));
            const table = document.getElementById('materialsTable');
            table.innerHTML = filtered.map(c => `<tr><td>${c.content_id}</td><td>${c.title}</td><td>${c.type}</td><td>${c.subject}</td><td>${c.difficulty}</td><td>${c.url ? `<a href="${c.url}" target="_blank">Watch</a>` : ''}</td></tr>`).join('');
        }

        document.addEventListener('DOMContentLoaded', () => {
            updateDashboard();
            updateRecommendations();
            updateAdaptivePath();
            filterMaterials();
        });
    </script>
</body>
</html>
    """
    return render_template_string(html, students=students, selected_student_id=selected_student_id, student=student, content=content, interactions=[i for i in interactions if i['student_id'] == selected_student_id], recs=recommendations, adaptive=adaptive_path)

if __name__ == '__main__':
    app.run(debug=True)