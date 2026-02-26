import sys
try:
    import pdfplumber
    with pdfplumber.open(r"c:\Users\shank\Downloads\Intelligent Job Recommendation System\vitish_2024_Pathfinders.pdf") as pdf:
        text = ""
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        print(text)
except Exception as e:
    print(f"Error: {e}")
