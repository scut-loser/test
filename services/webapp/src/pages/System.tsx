import React from 'react'
import { Card, Descriptions, message } from 'antd'
import axios from 'axios'

const API = (path: string) => `${window.location.protocol}//${window.location.hostname}:8080${path}`
const API_KEY = 'dev-key-please-change'

export default function System() {
	const [data, setData] = React.useState<any>({})
	const load = async () => {
		try {
			const res = await axios.get(API('/system/health'), { headers: { 'X-API-Key': API_KEY } })
			setData(res.data)
		} catch (e: any) { message.error(e?.message || e) }
	}
	React.useEffect(() => { load(); const t=setInterval(load, 5000); return () => clearInterval(t) }, [])
	return (
		<Card title="系统状态">
			<Descriptions bordered column={1} size="small">
				{Object.entries(data).map(([k, v]) => (
					<Descriptions.Item key={k} label={k}>{String(v)}</Descriptions.Item>
				))}
			</Descriptions>
		</Card>
	)
}
