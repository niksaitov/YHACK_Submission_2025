#run: python create_table.py to populate table

import os, pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

username = 'demo'
password = 'demo'
hostname = os.getenv('IRIS_HOSTNAME', 'localhost')
port = '1972' 
namespace = 'USER'
CONNECTION_STRING = f"iris://{username}:{password}@{hostname}:{port}/{namespace}"
engine = create_engine(CONNECTION_STRING)

# Load your model (for generating description vectors)
model = SentenceTransformer('all-MiniLM-L6-v2') 

df = pd.read_csv('cleaned_courses.csv')

# Generate embeddings for the descriptions
df['description_vector'] = model.encode(df['description'].tolist(), normalize_embeddings=True).tolist()

def create_courses_table(df, engine):
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("DROP TABLE IF EXISTS courses"))

            # Create the courses table with the new format if it doesn't already exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS courses (
                    courseNumber VARCHAR(4),
                    courseTitle VARCHAR(255),
                    crn BIGINT,
                    department VARCHAR(4),
                    description VARCHAR(1024),
                    distDesg VARCHAR(255),
                    meetingPattern VARCHAR(255),
                    prerequisites VARCHAR(1024),
                    description_vector VECTOR(DOUBLE, 384) 
                )
            """))
            
            # Insert course data into the table
            for index, row in df.iterrows():
                sql = text("""
                    INSERT INTO courses
                    (courseNumber, courseTitle, crn, department, description, distDesg, meetingPattern, prerequisites, description_vector) 
                    VALUES (:courseNumber, :courseTitle, :crn, :department, :description, :distDesg, :meetingPattern, :prerequisites, TO_VECTOR(:description_vector))
                """)
                conn.execute(sql, {
                'courseNumber': row['courseNumber'], 
                'courseTitle': row['courseTitle'], 
                'crn': row['crn'], 
                'department': row['department'], 
                'description': row['description'], 
                'distDesg': row['distDesg'], 
                'meetingPattern': row['meetingPattern'], 
                'prerequisites': row['prerequisites'], 
                'description_vector': str(row['description_vector'])
    
                })


# Run the function to create the table and insert data
create_courses_table(df, engine)
