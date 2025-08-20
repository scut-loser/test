import os
import json
import time
from datetime import datetime, timezone
from typing import List
from kafka import KafkaProducer
import pandas as pd
from influxdb_client import InfluxDBClient, Point

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = "market_ticks"
MODE = os.getenv("INGESTION_MODE", "sim")
SYMBOLS = [s.strip() for s in os.getenv("INGESTION_SYMBOLS", "IF2409").split(",")]
CSV_PATH = os.getenv("INGESTION_CSV_PATH", "/data/history.csv")
TICK_INTERVAL_MS = int(os.getenv("TICK_INTERVAL_MS", "200"))

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "market")

producer = KafkaProducer(
	bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
	value_serializer=lambda v: json.dumps(v).encode("utf-8"),
	key_serializer=lambda v: v.encode("utf-8"),
)

influx = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = influx.write_api()

def send_tick(symbol: str, price: float, volume: float, oi: float):
	ts = datetime.now(timezone.utc).isoformat()
	msg = {"ts": ts, "symbol": symbol, "price": price, "volume": volume, "open_interest": oi}
	producer.send(TOPIC, key=symbol, value=msg)
	pt = Point("tick").tag("symbol", symbol).field("price", price).field("volume", volume).field("open_interest", oi).time(ts)
	write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=pt)


def run_sim():
	import math
	base = {s: 100.0 + 10.0 * i for i, s in enumerate(SYMBOLS)}
	step = 0
	while True:
		for s in SYMBOLS:
			price = base[s] + 0.5 * math.sin(step / 10.0)
			volume = 100 + (step % 50)
			oi = 1000 + (step % 200)
			send_tick(s, price, volume, oi)
		step += 1
		time.sleep(TICK_INTERVAL_MS / 1000.0)


def run_csv():
	if not os.path.exists(CSV_PATH):
		raise FileNotFoundError(CSV_PATH)
	df = pd.read_csv(CSV_PATH)
	# expected columns: ts, symbol, price, volume, open_interest
	for _, row in df.iterrows():
		send_tick(str(row["symbol"]), float(row["price"]), float(row["volume"]), float(row["open_interest"]))
		time.sleep(TICK_INTERVAL_MS / 1000.0)

if __name__ == "__main__":
	if MODE == "csv":
		run_csv()
	else:
		run_sim()
