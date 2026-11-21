
from pathlib import Path

# Main materials directory
BASE_DIR = Path("materials")

# Initial university courses
courses = [
    "Numerical_Analysis",
    "Statistics",
    "ODE",
    "Biology",
    "Cultural_Anthropology"
]

# Types of academic materials
categories = [
    "Syllabus",
    "Midterms",
    "Finals",
    "Lectures",
    "Homework"
]

for course in courses:
    for category in categories:
        folder = BASE_DIR / course / category
        folder.mkdir(parents=True, exist_ok=True)

print("University materials folders created successfully!")
