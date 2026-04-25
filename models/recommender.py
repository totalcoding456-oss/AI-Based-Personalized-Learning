import pandas as pd
import numpy as np
from datetime import datetime

class RecommenderSystem:
    def __init__(self):
        self.load_data()

    def load_data(self):
        self.content = pd.read_csv('data/content.csv')
        self.interactions = pd.read_csv('data/interactions.csv')
        self.students = pd.read_csv('data/students.csv')

        # Normalize data types
        if 'difficulty' in self.content.columns:
            self.content['difficulty'] = pd.to_numeric(self.content['difficulty'], errors='coerce').fillna(0).astype(int)
        if 'score' in self.interactions.columns:
            self.interactions['score'] = pd.to_numeric(self.interactions['score'], errors='coerce')
        if 'time_spent' in self.interactions.columns:
            self.interactions['time_spent'] = pd.to_numeric(self.interactions['time_spent'], errors='coerce').fillna(0).astype(int)
        if 'timestamp' in self.interactions.columns:
            self.interactions['timestamp'] = pd.to_datetime(self.interactions['timestamp'], errors='coerce')

    def add_interaction(self, student_id, content_id, score=None, time_spent=0, rating=None):
        new_row = {
            'student_id': student_id,
            'content_id': content_id,
            'score': float(score) if score is not None else np.nan,
            'time_spent': int(time_spent or 0),
            'rating': rating if rating is not None else '',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.interactions = pd.concat([self.interactions, pd.DataFrame([new_row])], ignore_index=True)
        self.interactions['score'] = pd.to_numeric(self.interactions['score'], errors='coerce')
        self.interactions['time_spent'] = pd.to_numeric(self.interactions['time_spent'], errors='coerce').fillna(0).astype(int)
        self.interactions.to_csv('data/interactions.csv', index=False)

    def get_performance_analytics(self, student_id):
        student_interactions = self.interactions[self.interactions['student_id'] == student_id]
        if student_interactions.empty:
            return {
                'avg_score': 0,
                'total_time': 0,
                'completed_count': 0,
                'subject_performance': {},
                'history': pd.DataFrame(),
                'trend': 0,
                'predicted_next': 0
            }

        scored = student_interactions.dropna(subset=['score']).copy()
        avg_score = scored['score'].mean() if not scored.empty else 0
        total_time = int(student_interactions['time_spent'].sum())
        completed_count = int(len(scored))

        history = student_interactions.sort_values(by='timestamp', ascending=False).copy()
        history['score'] = history['score'].fillna(0)

        history = history.merge(
            self.content[['content_id', 'title', 'type', 'subject']],
            on='content_id', how='left'
        )

        merged = scored.merge(self.content[['content_id', 'subject']], on='content_id', how='left')
        subject_performance = merged.groupby('subject')['score'].mean().to_dict() if not merged.empty else {}

        trend = 0
        if len(scored) >= 2:
            recent = scored.sort_values('timestamp').tail(5)['score'].tolist()
            if len(recent) >= 2:
                trend = float(np.sign(np.diff(recent).mean()))

        predicted_next = float(avg_score + trend * 2) if not np.isnan(avg_score) else 0
        predicted_next = max(0.0, min(100.0, predicted_next))

        return {
            'avg_score': float(avg_score),
            'total_time': total_time,
            'completed_count': completed_count,
            'subject_performance': subject_performance,
            'history': history,
            'trend': trend,
            'predicted_next': predicted_next
        }

    def get_content_recommendations(self, student_id, top_n=3):
        interactions = self.interactions[self.interactions['student_id'] == student_id]
        if interactions.empty:
            return self.content.sort_values(by='difficulty', ascending=False).head(top_n).to_dict('records')

        interacted_ids = interactions['content_id'].tolist()
        interacted_subjects = self.content[self.content['content_id'].isin(interacted_ids)]['subject'].unique()

        recommendation_candidates = self.content[~self.content['content_id'].isin(interacted_ids)]
        if len(interacted_subjects):
            recommendation_candidates = recommendation_candidates[recommendation_candidates['subject'].isin(interacted_subjects)]

        if recommendation_candidates.empty:
            recommendation_candidates = self.content[~self.content['content_id'].isin(interacted_ids)]

        recommendation_candidates = recommendation_candidates.sort_values(by='difficulty', ascending=False)
        return recommendation_candidates.head(top_n).to_dict('records')

    def get_adaptive_recommendations(self, student_id, top_n=5):
        analytics = self.get_performance_analytics(student_id)
        interactions = self.interactions[self.interactions['student_id'] == student_id]
        interacted_ids = interactions['content_id'].tolist()

        if interactions.empty:
            return self.content.sort_values(by='difficulty', ascending=True).head(top_n).to_dict('records')

        avg_score = analytics['avg_score']
        interacted_subjects = self.content[self.content['content_id'].isin(interacted_ids)]['subject'].unique()

        candidates = self.content[~self.content['content_id'].isin(interacted_ids)]
        if len(interacted_subjects):
            candidates = candidates[candidates['subject'].isin(interacted_subjects)]

        if avg_score >= 80:
            candidates = candidates.sort_values(by='difficulty', ascending=False)
        elif avg_score >= 60:
            candidates = candidates.sort_values(by='difficulty', ascending=True)
        else:
            candidates = candidates.sort_values(by='difficulty', ascending=True)

        if candidates.empty:
            candidates = self.content[~self.content['content_id'].isin(interacted_ids)]

        return candidates.head(top_n).to_dict('records')

    def get_recommendations(self, student_id, top_n=5):
        return self.get_content_recommendations(student_id, top_n=top_n)
