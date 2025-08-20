import React from 'react'
import { Table, Card, message } from 'antd'
import axios from 'axios'

const API = (path: string) => `${window.location.protocol}//${window.location.hostname}:8080${path}`
const API_KEY = 'dev-key-please-change'

type Event = {
	id: number
	occurred_at: string
	symbol: string
	level: number
	score?: number
	confidence?: number
	label?: string
	action: string
	detail?: any
}

export default function Events() {
	const [data, setData] = React.useState<Event[]>([])
	const load = async () => {
		try {
			const res = await axios.get<Event[]>(API('/events'), { headers: { 'X-API-Key': API_KEY }, params: { limit: 200 } })
			setData(res.data)
		} catch (e: any) {
			message.error(`加载事件失败: ${e?.message || e}`)
		}
	}

	React.useEffect(() => {
		load()
		const t = setInterval(load, 5000)
		return () => clearInterval(t)
	}, [])

	return (
		<Card title="预警事件">
			<Table rowKey="id" dataSource={data} size="small"
				columns={[
					{ title: '时间', dataIndex: 'occurred_at' },
					{ title: '合约', dataIndex: 'symbol' },
					{ title: '等级', dataIndex: 'level' },
					{ title: '分数', dataIndex: 'score' },
					{ title: '置信度', dataIndex: 'confidence' },
					{ title: '标签', dataIndex: 'label' },
					{ title: '动作', dataIndex: 'action' },
				]}
			/>
		</Card>
	)
}
