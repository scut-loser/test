# 项目解读：
https://zread.ai/scut-loser/test
https://deepwiki.com/scut-loser/test

# 实时期货交易风险监测与预警系统（工程骨架）

本仓库提供期货交易风险控制的时间序列异常检测系统的可运行骨架（不包含具体模型算法）。
- 组件：数据接入、实时特征处理、模型服务（REST stub）、预警规则引擎、API 网关（FastAPI）、基础设施（Kafka、PostgreSQL、InfluxDB）。
- 目标：满足模块化、可观测、可扩展的工程化需求，便于后续替换/接入真实模型与数据源。

## 快速开始（本地 Docker）

1) 安装 Docker 与 Docker Compose。
2) 复制环境变量样例：
```bash
cp env.example .env
```
3) 启动：
```bash
docker compose up -d --build
```
4) 健康检查：
- API 网关: http://localhost:8080/health
- 文档: http://localhost:8080/docs
- Kafka: `localhost:29092`
- PostgreSQL: `localhost:5432`（凭据见 `.env`）
- InfluxDB: `http://localhost:8086`（初始凭据见 `.env`）

## 目录结构

```text
services/
  api_gateway/        # REST API、规则管理、事件查询
  ingestion/          # 数据接入（模拟/CSV）→ Kafka
  model_service/      # 模型推理服务（占位实现，支持版本）
  rule_engine/        # 预警规则引擎，联动处置动作
  streaming/          # 实时特征计算与推理编排
  common/schemas/     # 主题消息 JSON Schema
infrastructure/
  db/schema.sql       # PostgreSQL 表结构
.env.example
docker-compose.yml
README.md
```

## 核心 Kafka 主题（JSON）
- `market_ticks`: 基础行情（ts, symbol, price, volume, open_interest）
- `features`: 特征向量（窗口统计、差分、VWAP 等）
- `anomaly_results`: 模型输出（score、confidence、label、model_version）

## 安全与权限
- API-Key 鉴权（示例），通过 `X-API-Key` 头部，值来自 `.env` 的 `API_GATEWAY_API_KEY`
- 生产环境请接入 TLS、细粒度 RBAC、审计追踪、IP 白名单等

## 配置
- 规则：通过 API 管理并存储于 PostgreSQL `rules` 表，`rule_engine` 定期拉取
- 数据源：`services/ingestion` 支持模拟与 CSV

## 说明
- 本骨架以 Python 为主，便于快速迭代与验证。后续可替换 `streaming` 为 Flink/Spark 作业，`model_service` 为实际算法服务。
- 生产部署建议使用 Kubernetes（可在 `infrastructure/k8s/` 扩展）。
