import os
import json
import time
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Deque, Dict, Tuple
from kafka import KafkaConsumer, KafkaProducer
import httpx

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "http://model_service:8081/infer")
WINDOW_SECONDS = int(os.getenv("WINDOW_SECONDS", "300"))

consumer = KafkaConsumer(
	"market_ticks",
	bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
	auto_offset_reset="latest",
	enable_auto_commit=True,
	value_deserializer=lambda v: json.loads(v.decode("utf-8")),
	key_deserializer=lambda v: v.decode("utf-8") if v else None,
	group_id="streaming-feature"
)
producer = KafkaProducer(
	bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
	value_serializer=lambda v: json.dumps(v).encode("utf-8"),
	key_serializer=lambda v: v.encode("utf-8"),
)

# Simple in-memory rolling window per symbol: price and volume
Windows: Dict[str, Deque[Tuple[float, float, float]]] = defaultdict(lambda: deque(maxlen=1000))


def compute_features(symbol: str):
	win = Windows[symbol]
	if not win:
		return {"mean_price": 0.0, "std_price": 0.0, "vwap": 0.0, "d_price": 0.0}
	prices = [p for (_, p, _) in win]
	vols = [v for (_, _, v) in win]
	mean_price = sum(prices) / len(prices)
	std_price = (sum((p - mean_price) ** 2 for p in prices) / max(1, len(prices) - 1)) ** 0.5
	vwap_num = sum(p * v for p, v in zip(prices, vols))
	vwap_den = sum(vols) or 1.0
	vwap = vwap_num / vwap_den
	d_price = (prices[-1] - prices[0]) if len(prices) > 1 else 0.0
	return {"mean_price": mean_price, "std_price": std_price, "vwap": vwap, "d_price": d_price}


def call_model(symbol: str, features: dict, ts: str):
	with httpx.Client(timeout=2.0) as client:
		resp = client.post(MODEL_ENDPOINT, json={"symbol": symbol, "features": features, "ts": ts})
		resp.raise_for_status()
		return resp.json()

if __name__ == "__main__":
	for msg in consumer:
		data = msg.value
		symbol = data["symbol"]
		ts = data["ts"]
		price = float(data["price"])
		volume = float(data["volume"])
		# maintain window (size bounded by maxlen, approximate time window)
		Windows[symbol].append((time.time(), price, volume))
		features = compute_features(symbol)
		try:
			res = call_model(symbol, features, ts)
			out = {
				"ts": ts,
				"symbol": symbol,
				"score": res["score"],
				"confidence": res["confidence"],
				"label": res["label"],
				"model_version": res["model_version"],
				"features": features,
			}
			producer.send("anomaly_results", key=symbol, value=out)
		except Exception as e:
			# swallow error but continue
			pass
