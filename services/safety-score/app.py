from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from scoring import score_route

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
