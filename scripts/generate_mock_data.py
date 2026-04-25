import pandas as pd
import numpy as np
import random
import os

# Ensure data directory exists in the parent directory (project root)
data_dir = '../data'
os.makedirs(data_dir, exist_ok=True)

# 1. Generate Content Data
subjects = ['Mathematics', 'Physics', 'Computer Science', 'History', 'Biology']
content_types = ['Video', 'Lecture Notes', 'Practice Questions']

content_data = []
for i in range(1, 101):
    subject = random.choice(subjects)
    c_type = random.choice(content_types)
    difficulty = random.randint(1, 5)
    video_url = ""
    if c_type == 'Video':
        # Using a sample YouTube embed link
        video_url = "https://youtu.be/huQojf2tevI?si=hf--OBODKinS-Hej" 
    
    content_data.append({
        'content_id': f'C{i:03d}',
        'title': f'{subject} {c_type} {i}',
        'type': c_type,
        'subject': subject,
        'difficulty': difficulty,
        'tags': f'{subject.lower()}, {c_type.lower()}',
        'url': video_url
    })

content_df = pd.DataFrame(content_data)
content_df.to_csv(f'{data_dir}/content.csv', index=False)

# 2. Generate Student Data
student_names = ['Aryan', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Heidi', 'Ivan', 'Jack']
student_data = []
for i, name in enumerate(student_names, 1):
    student_data.append({
        'student_id': f'S{i:03d}',
        'name': name,
        'level': random.choice(['Beginner', 'Intermediate', 'Advanced']),
        'interests': ', '.join(random.sample(subjects, 2))
    })

student_df = pd.DataFrame(student_data)
student_df.to_csv(f'{data_dir}/students.csv', index=False)

# 3. Generate Interaction Data (History)
interaction_data = []
for s_id in student_df['student_id']:
    # Each student has interacted with 5-15 items
    num_interactions = random.randint(5, 15)
    interacted_items = random.sample(list(content_df['content_id']), num_interactions)
    
    for c_id in interacted_items:
        score = None
        c_type = content_df[content_df['content_id'] == c_id]['type'].values[0]
        if c_type == 'Practice Questions':
            score = random.randint(40, 100)
        
        interaction_data.append({
            'student_id': s_id,
            'content_id': c_id,
            'score': score,
            'time_spent': random.randint(5, 60), # minutes
            'rating': random.randint(1, 5),
            'timestamp': pd.Timestamp.now() - pd.Timedelta(days=random.randint(0, 30))
        })

interactions_df = pd.DataFrame(interaction_data)
interactions_df.to_csv(f'{data_dir}/interactions.csv', index=False)

print("Mock data generated successfully in ../data directory.")
