import os
import random
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_NAME = os.getenv("MODEL_NAME", "baseline")
MODEL_VERSION = os.getenv("MODEL_VERSION", "0.0.1")

app = FastAPI(title="Model Service", version=MODEL_VERSION)

class InferenceRequest(BaseModel):
	symbol: str
	features: dict
	ts: str

class InferenceResponse(BaseModel):
	score: float
	confidence: float
	label: str
	model_version: str

@app.get("/health")
def health():
	return {"status": "ok", "model": MODEL_NAME, "version": MODEL_VERSION}

@app.post("/infer", response_model=InferenceResponse)
def infer(req: InferenceRequest):
	# Stub logic: random score with deterministic seed per symbol
	rnd = random.Random(req.symbol)
	score = rnd.random()
	confidence = 0.5 + 0.5 * rnd.random()
	label = "anomaly" if score > 0.8 else ("warning" if score > 0.6 else "normal")
	return {
		"score": score,
		"confidence": confidence,
		"label": label,
		"model_version": MODEL_VERSION,
	}
