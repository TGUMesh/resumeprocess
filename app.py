from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import requests
import pdfplumber
import os
import spacy
import google.generativeai as genai
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import re
import time
import random
import torch
import threading
from google.api_core import exceptions as google_exceptions
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Phase 2: Neo4j and Graph Queries
from database import db
from graph_queries import analyze_skill_gap, get_user_graph_data

dataset = pd.read_csv('postings.csv', dtype={
    'title': str,
    'company_name': str,
    'description': str,
    'job_posting_url': str
})

print(f"Loaded dataset shape: {dataset.shape}")
print("Sample titles from dataset:")
print(dataset['title'].head())

app = Flask(__name__)
CORS(app)

model = SentenceTransformer('all-MiniLM-L6-v2')

@app.route('/')
def index():
    return render_template('index.html')

# Configure Gemini API key
api_key = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
genai.configure(api_key=api_key)


# Load NLP model
nlp = spacy.load('en_core_web_sm')
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

# Path to store uploaded resumes
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

# Function to extract text from PDF resume
def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text


def normalize_title(title):
    # More robust title normalization
    if pd.isna(title):
        return ""
    return ' '.join(re.sub(r'[^\w\s]', '', title.lower()).split())


def clean_text(text):
    return ' '.join(re.sub(r'[#*]', '', text).split())

def extract_experience(resume_text):
    experience_pattern = re.compile(r'(\d+)\s*(?:years?|yrs?|year)', re.IGNORECASE)
    matches = experience_pattern.findall(resume_text)
    if matches:
        # Convert matches to integers and return the max experience found
        return max([int(exp) for exp in matches])
    return 0  # Default if no experience is specified

def calculate_recommendation_scores(resume_skills, job_required_skills, resume_experience, job_experience):
    # Calculate the skill match score
    common_skills = set(resume_skills) & set(job_required_skills)
    skill_score = len(common_skills) / len(job_required_skills) if job_required_skills else 0

    # Calculate experience match score
    if job_experience > 0:
        experience_match_score = min(resume_experience, job_experience) / max(resume_experience, job_experience)
    else:
        experience_match_score = 1  

    combined_score = (0.7 * skill_score) + (0.3 * experience_match_score)
    return combined_score



def identify_missing_skills(skills, job_requirements, model, threshold=0.7):
    if not skills or not job_requirements:
        return []

    # Encode both skills and job requirements using SBERT
    skills_embedding = sbert_model.encode(skills, convert_to_tensor=True)
    requirements_embedding = sbert_model.encode(job_requirements, convert_to_tensor=True)
    
    # Calculate cosine similarity between skills and job requirements
    similarity_scores = util.cos_sim(skills_embedding, requirements_embedding)
    
    threshold_dynamic = np.mean(similarity_scores.cpu().numpy())  
    missing_skills = []
    for idx, req in enumerate(job_requirements):
        score = similarity_scores[0][idx].item()  
        if score < threshold_dynamic:
            missing_skills.append((req, score))  

    return missing_skills


def recommend_courses(missing_skills):
    course_recommendations = []
    for skill in missing_skills:
        url = f"https://www.coursera.org/search?query={skill.replace(' ', '%20')}"
        try:
            response = requests.get(url, timeout=10)  
            response.raise_for_status() 
            soup = BeautifulSoup(response.text, 'html.parser')
            
            courses = soup.select('a.card-title')[:3]  
            
            for course in courses:
                course_name = course.get_text(strip=True)
                course_link = f"https://www.coursera.org{course['href']}"
                
                if course_name and course_link:
                    course_recommendations.append({'course_name': course_name, 'link': course_link})

        except requests.exceptions.RequestException as e:
            print(f"Error fetching courses for skill '{skill}': {e}")
        
    return course_recommendations


def generate_with_retry(model, prompt, max_retries=3):
    """Fallback handler for Gemini API rate limits (15 RPM free tier)."""
    delay = 2
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except google_exceptions.ResourceExhausted:
            print(f"API Rate Limit Hit! Sleeping for {delay} seconds (Attempt {attempt+1}/{max_retries})...")
            time.sleep(delay)
            delay *= 2 # Exponential backoff
        except Exception as e:
            print(f"Gemini API Error: {e}")
            break
            
    # Fallback empty string if all retries fail
    class DummyResponse:
        text = ""
    return DummyResponse()

# AI-powered resume analysis and job recommendations
def analyze_resume_and_get_jobs(resume_text, dataset):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        # extract skills
        skills_response = generate_with_retry(model, 
            f"Extract just the technical skills as a list (don't include anything else): {resume_text}")
        skills_raw = skills_response.text.splitlines()
        skills = [clean_text(skill) for skill in skills_raw if skill.strip()]

        # extract experience
        experience_response = generate_with_retry(model,
            f"Extract years of relevant experience: {resume_text}")
        resume_experience = float(experience_response.text.strip()) if experience_response.text.strip().isdigit() else 0
        
        # Phase 2: Save to Graph Database (Using a dummy user 'current_user' for now)
        db.add_user("current_user", "Guest User")
        for skill in skills:
            db.add_skill(skill)
            db.user_has_skill("current_user", skill, "Extracted")
            
    except Exception as e:
        print(f"Error fetching skills or experience: {e}")
        skills = []
        resume_experience = 0
    
    try:
        optimization_tips_response = generate_with_retry(model,
            f"Provide 5 major optimization tips to improve this resume based on the following content as a list(dont include introduction lines): {resume_text}")
        optimization_tips = optimization_tips_response.text.splitlines()
        print(optimization_tips)
    except Exception as e:
        print(f"Error fetching resume optimization tips: {e}")
        optimization_tips = ["No optimization tips available."]

    job_recommendations = []

    # get recommended job titles
    try:
        job_titles_response = generate_with_retry(model,
            f"List the top 5 recommended job titles for these skills (just the job titles without numbering or markdown): {', '.join(skills)}")
        
        # clean titles
        recommended_titles = [
            title.strip().replace('**', '').replace('#', '').strip() 
            for title in job_titles_response.text.splitlines() 
            if title.strip() and not title.startswith('Here') and not title.isspace()
        ]
        print("Cleaned Recommended Titles:", recommended_titles)
    except Exception as e:
        print(f"Error fetching recommended job titles: {e}")
        recommended_titles = []

    recommended_titles_normalized = [normalize_title(title) for title in recommended_titles]

    for title in recommended_titles_normalized:
        matching_jobs = dataset[dataset['title'].str.contains(title, case=False, na=False, regex=False)].head(3)
        print("Matching jobs: ",matching_jobs)


        for _, job in matching_jobs.iterrows():
            job_title = job['title'] if pd.notna(job['title']) else 'Position Available'
            company = job['company_name'] if pd.notna(job['company_name']) else 'Company Not Listed'
            description = job['description'] if pd.notna(job['description']) else 'No description available'
            link = job['job_posting_url'] if pd.notna(job['job_posting_url']) else '#'

            # Extract required skills and experience from job description
            try:
                job_skills_response = generate_with_retry(model, f"Extract just the specific technical skills(like programming languages) required as a list(include no extra text and separate each skill): {description}")
                job_skills = [clean_text(skill) for skill in job_skills_response.text.splitlines() if skill.strip()]

                experience_response = generate_with_retry(model, f"Extract minimum years of experience required: {description}")
                required_experience = float(experience_response.text.strip()) if experience_response.text.strip().isdigit() else 0

                recommendation_score = calculate_recommendation_scores(skills, job_skills, resume_experience, required_experience)

                missing_skills = identify_missing_skills(skills, job_skills,sbert_model)
                
                try:
                    course_recommendations = recommend_courses(missing_skills)
                except Exception as e:
                    print(f"Error fetching courses: {e}")
                    course_recommendations = [{"course_name": "Course Not Available", "link": "#"}]

                job_recommendations.append({
                    'title': job_title,
                    'company': company,
                    'description': description[:500] + '...' if len(description) > 500 else description,
                    'link': link,
                    'score': recommendation_score,
                    'missing_skills': missing_skills if missing_skills else ["No missing skills identified"],
                    'recommended_courses': course_recommendations
                })

                # Phase 2: Save Job and Requirements to Graph Database
                db.add_job_role(job_title, company)
                for req_skill in job_skills:
                    db.add_skill(req_skill)
                    db.job_requires_skill(job_title, req_skill)

            except Exception as e:
                print(f"Error processing job {job_title}: {e}")
                continue
                
    # Phase 2: Real-time Data Ingestion
    # Fire off a background thread to scrape the top recommended job title and update the Neo4j graph silently
    if recommended_titles:
        top_title = recommended_titles[0]
        def scrape_and_update_graph(title):
            print(f"Background: Scraping live jobs for '{title}'...")
            live_jobs = scrape_individual_jobs(title)
            for j in live_jobs:
                try:
                    db.add_job_role(j['title'], "Live Scraped Company")
                    # Use Gemini to extract skills from live scraped description
                    job_skills_response = generate_with_retry(model, f"Extract just the specific technical skills required as a list(include no extra text and separate each skill): {j['description']}")
                    live_job_skills = [clean_text(skill) for skill in job_skills_response.text.splitlines() if skill.strip()]
                    
                    for req_skill in live_job_skills:
                        db.add_skill(req_skill)
                        db.job_requires_skill(j['title'], req_skill)
                except Exception as e:
                    print(f"Background scrape parsing error: {e}")
            print(f"Background: Successfully updated Knowledge Graph with live jobs for '{title}'")
            
        threading.Thread(target=scrape_and_update_graph, args=(top_title,)).start()

    print(job_recommendations)
    return {'skills': skills, 'experience': resume_experience, 'job_recommendations': job_recommendations, 'optimization_tips': optimization_tips}


def scrape_individual_jobs(job_title):
    url = f"https://in.indeed.com/jobs?q={job_title.replace(' ', '+')}&l=Chennai"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1" 
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to retrieve jobs for {job_title}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    job_cards = soup.find_all(class_='job_seen_beacon', limit=3)

    for job_card in job_cards:
        job_title = job_card.find('h2', class_='jobTitle').text.strip()
        job_link = "https://www.indeed.com" + job_card.find('a')['href']
        job_description_text = ""

        time.sleep(random.uniform(1.5, 3.5))

        # Fetch job description
        try:
            headers["User-Agent"] = random.choice(USER_AGENTS)
            job_response = requests.get(job_link, headers=headers)
            job_response.raise_for_status()
            job_soup = BeautifulSoup(job_response.text, 'html.parser')
            job_description_element = job_soup.find(id='jobDescriptionText')
            if job_description_element:
                job_description_text = job_description_element.text.strip()
        except requests.RequestException as e:
            print(f"Failed to retrieve job description for {job_title} at {job_link}: {e}")
        
        if job_description_text:
            jobs.append({
                'title': job_title,
                'link': job_link,
                'description': job_description_text
            })

    return jobs


@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})

    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        resume_text = extract_text_from_pdf(file_path)
        
        analysis_results = analyze_resume_and_get_jobs(resume_text, dataset)
        
        return jsonify(analysis_results)
    
    return jsonify({'error': 'Invalid file format, please upload a PDF resume.'})

@app.route('/api/graph-data', methods=['GET'])
def get_graph():
    user_id = request.args.get('user_id', 'current_user')
    target_job = request.args.get('target_job')
    
    # Needs a connected Neo4j database to work fully
    data = get_user_graph_data(user_id, target_job)
    return jsonify(data)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
