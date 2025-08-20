-- Schema for rules, events, and simple users/audit tables
CREATE TABLE IF NOT EXISTS rules (
	id SERIAL PRIMARY KEY,
	name VARCHAR(128) NOT NULL,
	level INT NOT NULL CHECK (level BETWEEN 1 AND 3),
	condition_json JSONB NOT NULL,
	is_active BOOLEAN NOT NULL DEFAULT TRUE,
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
	id SERIAL PRIMARY KEY,
	occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	symbol VARCHAR(32) NOT NULL,
	level INT NOT NULL,
	score DOUBLE PRECISION,
	confidence DOUBLE PRECISION,
	label VARCHAR(64),
	action VARCHAR(64) NOT NULL,
	detail JSONB
);

CREATE INDEX IF NOT EXISTS idx_events_symbol_time ON events(symbol, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_level ON events(level);

CREATE TABLE IF NOT EXISTS users (
	id SERIAL PRIMARY KEY,
	username VARCHAR(64) UNIQUE NOT NULL,
	role VARCHAR(32) NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
	id SERIAL PRIMARY KEY,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	username VARCHAR(64),
	action VARCHAR(128) NOT NULL,
	detail JSONB
);

-- Seed default rules if missing
INSERT INTO rules(name, level, condition_json, is_active)
SELECT 'Score>=0.8_HALT', 3, '{"score_gte": 0.8}', TRUE
WHERE NOT EXISTS (SELECT 1 FROM rules WHERE name='Score>=0.8_HALT');

INSERT INTO rules(name, level, condition_json, is_active)
SELECT 'Score>=0.6_NOTIFY', 2, '{"score_gte": 0.6}', TRUE
WHERE NOT EXISTS (SELECT 1 FROM rules WHERE name='Score>=0.6_NOTIFY');
