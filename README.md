# Cognify Career Navigator

An AI-Enhanced Career Guidance System for Personalized Career Pathways

## Features
* **AI Resume Parsing**: Extracts skills and experience using Google Gemini.
* **Job Matching**: Recommends the top 5 targeted career paths.
* **Skill Gap Analysis**: Compares your resume against real job descriptions using `SentenceTransformers`.
* **Adaptive Knowledge Graph**: Stores users, skills, and job requirements in a Neo4j Graph Database.
* **Career Roadmap**: Interactive D3.js visualization showing the path from your current skills to your dream job.

## Setup Instructions

### 1. Database (postings.csv)
Due to GitHub file size limits, the core dataset (`postings.csv`) is not included in this repository. 
**To run this project, you must:**
1. Download the dataset from kaggle.
2. Place the `postings.csv` file directly into the `nlp/` root directory.

### 2. Environment Variables
You must provide your own Google Gemini API key.
* Windows: `$env:GEMINI_API_KEY="your_api_key_here"`
* Mac/Linux: `export GEMINI_API_KEY="your_api_key_here"`

### 3. Running the App
1. Install dependencies: `pip install -r requirements.txt`
2. Start the Neo4j database (requires Docker): `docker-compose up -d`
3. Run the Flask server: `python app.py`
4. Visit `http://127.0.0.1:5000` in your browser!
