from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, computed_field
from typing import Literal, Annotated, List
import pandas as pd
import numpy as np
import joblib,json
import os

#creating an instance of the FastAPI application
app = FastAPI(title="Nepal Course Recommender Pro", version="1.0")

# SERVE FRONTEND
app.mount("/static", StaticFiles(directory="static"), name="static")

# HOME ROUTE
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hard Filter Database
COURSES_DB = {
    "mbbs": {"stream": ["Science (Bio)"], "min_gpa": 2.4},
    "bpharmacy": {"stream": ["Science (Bio)", "Science (Physical)"], "min_gpa": 2.4},
    "civil engineering": {"stream": ["Science (Physical)", "Technical"], "min_gpa": 2.0},
    "computer engineering": {"stream": ["Science (Physical)", "Technical"], "min_gpa": 2.0},
    "electrical engineering": {"stream": ["Science (Physical)", "Technical"], "min_gpa": 2.0},
    "bsc csit": {"stream": ["Science (Physical)", "Science (Bio)"], "min_gpa": 2.0},
    "bit": {"stream": ["Science (Bio)", "Science (Physical)", "Management", "Humanities", "Law", "Education"], "min_gpa": 2.0},
    "bca": {"stream": ["Science (Bio)", "Science (Physical)", "Management", "Humanities", "Law", "Education", "Technical"], "min_gpa": 2.0},
    "bba": {"stream": ["Management", "Science (Bio)", "Science (Physical)"], "min_gpa": 1.8},
    "bbm": {"stream": ["Management", "Science (Bio)", "Science (Physical)"], "min_gpa": 1.8},
    "bhm": {"stream": ["Management", "Humanities", "Science (Bio)", "Science (Physical)"], "min_gpa": 1.8},
    "bbs": {"stream": ["Management", "Humanities", "Science (Bio)", "Science (Physical)", "Education"], "min_gpa": 1.6}
}

# Loading saved Ml model
try:

    pipeline = joblib.load('Model_Training/course_recommender_Rf.pkl')
    le = joblib.load('Model_Training/label_encoder.pkl')
    model_loaded = True
except FileNotFoundError:
    model_loaded = False
    print("Warning: ML models not found in root. Check file names!")

#Creating pydantic model

class StudentRequest(BaseModel):
    stream: Annotated[Literal
    ['Science (Bio)', 'Science (Physical)', 'Management', 
    'Humanities', 'Law', 'Education', 'Technical'
    ], Field(..., description="The +2 stream completed by the student")]
    
    gpa: Annotated[float, Field(..., ge=0.8, le=4.0, description="Overall GPA")]
    interest: str
    career_goal: str
    skills: str
    budget_amount: int

    @computed_field
    @property
    def eligible_courses(self) -> List[str]:
        eligible = []
        for course, criteria in COURSES_DB.items():
            if self.stream in criteria["stream"] and self.gpa >= criteria["min_gpa"]:
                eligible.append(course)
        return eligible

    @computed_field
    @property
    def ml_budget_tier(self) -> str:
        if self.budget_amount >= 1000000: return "High"
        elif self.budget_amount >= 500000: return "Mid"
        else: return "Low"


@app.post("/predict")
def predict_course(data: StudentRequest):
    eligible_list = data.eligible_courses
    if not eligible_list:
        raise HTTPException(status_code=400, detail="You do not meet the minimum requirements for the listed courses.")

    combined_text = f"{data.interest} {data.career_goal} {data.skills}".lower().strip()
    input_df = pd.DataFrame([{'combined_text': combined_text, 'Budget': data.ml_budget_tier}])

    raw_scores = {}
    if model_loaded:
        probs = pipeline.predict_proba(input_df)[0]
        for i, probability in enumerate(probs):
            course_name = le.inverse_transform([i])[0].lower()
            raw_scores[course_name] = probability
    else:
        raw_scores = {course: 0.5 for course in COURSES_DB.keys()}

    final_recommendations = []
    for course in eligible_list:
        score = raw_scores.get(course, 0)
        final_recommendations.append({"course": course.upper(), "confidence": round(score * 100, 2)})

    final_recommendations = sorted(final_recommendations, key=lambda x: x["confidence"], reverse=True)

    return {"student_stream": data.stream, "recommendations": final_recommendations[:3]}

# Serving Json File 

@app.get("/suggestions")
async def get_suggestions():
    try:
        with open('Model_Training/suggestions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError: 
        return {"error": "Suggestions file not found. Run your export script."}