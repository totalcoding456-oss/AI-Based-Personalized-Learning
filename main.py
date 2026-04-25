import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models.recommender import RecommenderSystem
import pandas as pd
import json

 

app = Flask(__name__, static_folder='frontend')
CORS(app)

# Initialize Recommender
recommender = RecommenderSystem()

# Serve Frontend
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

@app.route('/api/students', methods=['GET'])
def get_students():
    students = recommender.students.to_dict(orient='records')
    return jsonify(students)

@app.route('/api/student/<student_id>', methods=['GET'])
def get_student_details(student_id):
    student = recommender.students[recommender.students['student_id'] == student_id]
    if student.empty:
        return jsonify({"error": "Student not found"}), 404
    
    recommender.load_data() # Refresh data
    analytics = recommender.get_performance_analytics(student_id)
    
    # Process analytics for JSON serialization
    processed_analytics = None
    if analytics:
        history = analytics['history'].head(10).to_dict(orient='records')
        for record in history:
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
                elif hasattr(value, 'item'):
                    record[key] = value.item()
                elif pd.isna(value):
                    record[key] = None

        trend_value = analytics['trend']
        trend_label = 'Stable'
        if isinstance(trend_value, (int, float)):
            if trend_value > 0:
                trend_label = 'Improving'
            elif trend_value < 0:
                trend_label = 'Declining'

        processed_analytics = {
            'avg_score': float(analytics['avg_score']) if not pd.isna(analytics['avg_score']) else 0,
            'total_time': int(analytics['total_time']),
            'completed_count': int(analytics['completed_count']),
            'subject_performance': {k: (float(v) if not pd.isna(v) else 0) for k, v in analytics['subject_performance'].items()},
            'history': history,
            'trend': trend_label,
            'predicted_next': float(analytics['predicted_next'])
        }
    
    return jsonify({
        "profile": student.iloc[0].to_dict(),
        "analytics": processed_analytics
    })

@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    data = request.json
    student_id = data.get('student_id')
    content_id = data.get('content_id')
    score = data.get('score')
    
    if not all([student_id, content_id, score]):
        return jsonify({"error": "Missing parameters"}), 400
        
    recommender.add_interaction(student_id, content_id, score=score)
    return jsonify({"success": True, "message": "Quiz submitted successfully"})

def safe_serialize(data):
    if isinstance(data, pd.DataFrame):
        records = data.to_dict(orient='records')
    elif isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = [data]
    else:
        return data

    for record in records:
        for key, value in list(record.items()):
            if hasattr(value, 'item'):
                record[key] = value.item()
            elif pd.isna(value):
                record[key] = None
    return records

@app.route('/api/recommendations/<student_id>', methods=['GET'])
def get_recommendations(student_id):
    adaptive_recs = recommender.get_adaptive_recommendations(student_id)
    content_recs = recommender.get_content_recommendations(student_id, top_n=3)
    
    return jsonify({
        "adaptive": safe_serialize(adaptive_recs),
        "content_based": safe_serialize(content_recs)
    })

@app.route('/api/content', methods=['GET'])
def get_all_content():
    content = safe_serialize(recommender.content)
    return jsonify(content)

if __name__ == '__main__':
    app.run(debug=False, port=5000)
