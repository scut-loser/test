import React from 'react'
import { Card, Space, Select, Typography, message } from 'antd'
import axios from 'axios'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'

const API = (path: string) => `${window.location.protocol}//${window.location.hostname}:8080${path}`
const API_KEY = 'dev-key-please-change'

type TickPoint = { ts: string; price: number; volume: number }

export default function Dashboard() {
	const [symbol, setSymbol] = React.useState('IF2409')
	const [points, setPoints] = React.useState<TickPoint[]>([])

	const load = async (sym: string) => {
		try {
			const res = await axios.get<TickPoint[]>(API(`/timeseries/ticks`), {
				headers: { 'X-API-Key': API_KEY },
				params: { symbol: sym, range: '30m', limit: 1000 },
			})
			setPoints(res.data)
		} catch (e: any) {
			message.error(`加载数据失败: ${e?.message || e}`)
		}
	}

	React.useEffect(() => {
		load(symbol)
		const t = setInterval(() => load(symbol), 5000)
		return () => clearInterval(t)
	}, [symbol])

	const option = React.useMemo(() => {
		return {
			title: { text: `${symbol} 价格/成交量` },
			tooltip: { trigger: 'axis' },
			legend: { data: ['price', 'volume'] },
			xAxis: { type: 'time' },
			yAxis: [
				{ type: 'value', name: 'price', scale: true },
				{ type: 'value', name: 'volume', scale: true },
			],
			series: [
				{ name: 'price', type: 'line', showSymbol: false, data: points.map(p => [p.ts, p.price]) },
				{ name: 'volume', type: 'bar', yAxisIndex: 1, data: points.map(p => [p.ts, p.volume]) },
			],
		}
	}, [points, symbol])

	return (
		<Space direction="vertical" style={{ width: '100%' }} size="large">
			<Space>
				<Typography.Text>合约</Typography.Text>
				<Select value={symbol} onChange={setSymbol} options={[
					{ value: 'IF2409', label: 'IF2409' },
					{ value: 'AG2412', label: 'AG2412' },
					{ value: 'CU2409', label: 'CU2409' },
				]} />
			</Space>
			<Card>
				<ReactECharts option={option} style={{ height: 420 }} />
			</Card>
		</Space>
	)
}
