from app import analyze_resume_and_get_jobs, dataset
from app import extract_text_from_pdf

print("Extracting text...")
text = extract_text_from_pdf("uploads/CV- John Doe - New.pdf")

print("Sending to Gemini for analysis...")
result = analyze_resume_and_get_jobs(text, dataset)

print("\n--- RESULTS ---")
print(result)
