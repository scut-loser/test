import os
import json
from typing import List, Dict, Any
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://finuser:finpass@postgres:5432/finrisk")

def get_engine():
	return create_engine(DATABASE_URL, pool_pre_ping=True)

consumer = KafkaConsumer(
	"anomaly_results",
	bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
	auto_offset_reset="latest",
	enable_auto_commit=True,
	value_deserializer=lambda v: json.loads(v.decode("utf-8")),
	key_deserializer=lambda v: v.decode("utf-8") if v else None,
	group_id="rule-engine"
)


def load_active_rules(conn) -> List[Dict[str, Any]]:
	rows = conn.execute(text("SELECT id, name, level, condition_json FROM rules WHERE is_active = TRUE ORDER BY level DESC"))
	return [dict(r._mapping) for r in rows]


def evaluate(rule: Dict[str, Any], result: Dict[str, Any]) -> bool:
	# simple evaluator: supports threshold on score and label match
	cond = rule["condition_json"]
	ok = True
	if "score_gte" in cond:
		ok = ok and (result.get("score", 0) >= cond["score_gte"])
	if "label_in" in cond:
		ok = ok and (result.get("label") in cond["label_in"])
	return ok


def action_for_level(level: int) -> str:
	return {1: "LOG", 2: "NOTIFY", 3: "HALT"}.get(level, "LOG")

if __name__ == "__main__":
	engine = get_engine()
	with engine.begin() as conn:
		for msg in consumer:
			res = msg.value
			symbol = res.get("symbol")
			rules = load_active_rules(conn)
			for r in rules:
				if evaluate(r, res):
					action = action_for_level(r["level"])
					conn.execute(
						text("""
						INSERT INTO events(symbol, level, score, confidence, label, action, detail)
						VALUES (:symbol, :level, :score, :conf, :label, :action, :detail)
						"""),
						{
							"symbol": symbol,
							"level": r["level"],
							"score": res.get("score"),
							"confidence": res.get("confidence"),
							"label": res.get("label"),
							"action": action,
							"detail": json.dumps({"rule": r["name"], "features": res.get("features", {})}),
						},
					)
					print(f"{action} triggered for {symbol} by rule {r['name']}")
