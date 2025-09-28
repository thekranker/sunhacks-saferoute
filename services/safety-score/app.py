from fastapi import FastAPI
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from fastapi.middleware.cors import CORSMiddleware
=======
>>>>>>> 166347e (feat(safety-score): add Chicago crime data ingest + safety scoring API)
=======
from fastapi.middleware.cors import CORSMiddleware
>>>>>>> b2f92c2 (Working Safety Score)
=======
from fastapi.middleware.cors import CORSMiddleware
>>>>>>> karan-dev
from pydantic import BaseModel
from typing import List
from scoring import score_route

app = FastAPI()

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b2f92c2 (Working Safety Score)
=======
>>>>>>> karan-dev
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 166347e (feat(safety-score): add Chicago crime data ingest + safety scoring API)
=======
>>>>>>> b2f92c2 (Working Safety Score)
=======
>>>>>>> karan-dev
class RoutePoint(BaseModel):
    lat: float
    lon: float

class ScoreRouteRequest(BaseModel):
    route_id: str
    points: List[RoutePoint]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/score-route")
def score_route_api(req: ScoreRouteRequest):
    points = [p.dict() for p in req.points]
    safety, breakdown = score_route(points)
    return {
        "route_id": req.route_id,
        "safety_score": safety,
        "breakdown": breakdown
    }
