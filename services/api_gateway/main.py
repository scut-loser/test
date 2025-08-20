import os
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import create_engine, text
import httpx
from influxdb_client import InfluxDBClient

API_KEY = os.getenv("API_GATEWAY_API_KEY", "dev-key-please-change")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://finuser:finpass@postgres:5432/finrisk")
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "market")

MODEL_HEALTH_URL = os.getenv("MODEL_HEALTH_URL", "http://model_service:8081/health")

def get_engine():
	return create_engine(DATABASE_URL, pool_pre_ping=True)


def get_influx():
	return InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

app = FastAPI(title="Futures Risk Monitor API", version="0.1.0")
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

def verify_api_key(x_api_key: Optional[str] = Header(default=None)):
	if x_api_key != API_KEY:
		raise HTTPException(status_code=401, detail="Unauthorized")

class RuleIn(BaseModel):
	name: str = Field(..., max_length=128)
	level: int = Field(..., ge=1, le=3)
	condition_json: dict
	is_active: bool = True

class RuleOut(RuleIn):
	id: int

@app.get("/health")
async def health():
	return {"status": "ok"}

@app.get("/system/health")
async def system_health(_: None = Depends(verify_api_key)):
	results = {"api_gateway": "ok"}
	async with httpx.AsyncClient(timeout=2.0) as client:
		try:
			resp = await client.get(MODEL_HEALTH_URL)
			results["model_service"] = "ok" if resp.status_code == 200 else f"err:{resp.status_code}"
		except Exception:
			results["model_service"] = "down"
	return results

@app.get("/rules", response_model=List[RuleOut])
async def list_rules(_: None = Depends(verify_api_key)):
	engine = get_engine()
	with engine.begin() as conn:
		rows = conn.execute(text("SELECT id, name, level, condition_json, is_active FROM rules ORDER BY id"))
		return [
			{"id": r.id, "name": r.name, "level": r.level, "condition_json": r.condition_json, "is_active": r.is_active}
			for r in rows
		]

@app.post("/rules", response_model=RuleOut)
async def create_rule(rule: RuleIn, _: None = Depends(verify_api_key)):
	engine = get_engine()
	with engine.begin() as conn:
		res = conn.execute(
			text("INSERT INTO rules(name, level, condition_json, is_active) VALUES (:name, :level, :cj, :act) RETURNING id"),
			{"name": rule.name, "level": rule.level, "cj": rule.condition_json, "act": rule.is_active},
		)
		rule_id = res.scalar_one()
		return {"id": rule_id, **rule.model_dump()}

@app.put("/rules/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: int, rule: RuleIn, _: None = Depends(verify_api_key)):
	engine = get_engine()
	with engine.begin() as conn:
		conn.execute(
			text("UPDATE rules SET name=:name, level=:level, condition_json=:cj, is_active=:act, updated_at=NOW() WHERE id=:id"),
			{"name": rule.name, "level": rule.level, "cj": rule.condition_json, "act": rule.is_active, "id": rule_id},
		)
		return {"id": rule_id, **rule.model_dump()}

@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int, _: None = Depends(verify_api_key)):
	engine = get_engine()
	with engine.begin() as conn:
		conn.execute(text("DELETE FROM rules WHERE id=:id"), {"id": rule_id})
	return {"deleted": rule_id}

class EventOut(BaseModel):
	id: int
	occurred_at: str
	symbol: str
	level: int
	score: Optional[float]
	confidence: Optional[float]
	label: Optional[str]
	action: str
	detail: Optional[dict]

@app.get("/events", response_model=List[EventOut])
async def list_events(symbol: Optional[str] = None, limit: int = 100, _: None = Depends(verify_api_key)):
	limit = min(max(limit, 1), 1000)
	engine = get_engine()
	with engine.begin() as conn:
		if symbol:
			rows = conn.execute(
				text("SELECT id, occurred_at, symbol, level, score, confidence, label, action, detail FROM events WHERE symbol=:s ORDER BY occurred_at DESC LIMIT :l"),
				{"s": symbol, "l": limit},
			)
		else:
			rows = conn.execute(text("SELECT id, occurred_at, symbol, level, score, confidence, label, action, detail FROM events ORDER BY occurred_at DESC LIMIT :l"), {"l": limit})
		return [dict(r._mapping) for r in rows]

class TickPoint(BaseModel):
	ts: str
	price: float
	volume: float

@app.get("/timeseries/ticks", response_model=List[TickPoint])
async def ticks_timeseries(symbol: str = Query(...), range: str = Query("15m"), limit: int = Query(500), _: None = Depends(verify_api_key)):
	limit = min(max(limit, 1), 5000)
	client = get_influx()
	query = f"""
	from(bucket: "{INFLUXDB_BUCKET}")
	|> range(start: -{range})
	|> filter(fn: (r) => r._measurement == "tick" and r.symbol == "{symbol}" and (r._field == "price" or r._field == "volume"))
	|> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
	|> keep(columns:["_time","price","volume"]) 
	|> sort(columns:["_time"]) 
	|> limit(n:{limit})
	"""
	records = client.query_api().query(query=query, org=INFLUXDB_ORG)
	points: List[TickPoint] = []
	for table in records:
		for rec in table.records:
			points.append(TickPoint(ts=rec.get_time().isoformat(), price=float(rec.values.get("price", 0.0)), volume=float(rec.values.get("volume", 0.0))))
	return points
