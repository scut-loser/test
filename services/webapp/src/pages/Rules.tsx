import React from 'react'
import { Card, Table, Button, Modal, Form, Input, InputNumber, Switch, message } from 'antd'
import axios from 'axios'

const API = (path: string) => `${window.location.protocol}//${window.location.hostname}:8080${path}`
const API_KEY = 'dev-key-please-change'

interface Rule {
	id: number
	name: string
	level: number
	condition_json: any
	is_active: boolean
}

export default function Rules() {
	const [data, setData] = React.useState<Rule[]>([])
	const [open, setOpen] = React.useState(false)
	const [form] = Form.useForm()

	const load = async () => {
		try {
			const res = await axios.get<Rule[]>(API('/rules'), { headers: { 'X-API-Key': API_KEY } })
			setData(res.data)
		} catch (e: any) {
			message.error(`加载失败: ${e?.message || e}`)
		}
	}
	React.useEffect(() => { load() }, [])

	const onCreate = async () => {
		const v = await form.validateFields()
		try {
			const payload = {
				name: v.name,
				level: v.level,
				is_active: v.is_active,
				condition_json: typeof v.condition_json === 'string' ? JSON.parse(v.condition_json) : v.condition_json,
			}
			await axios.post(API('/rules'), payload, { headers: { 'X-API-Key': API_KEY } })
			setOpen(false)
			form.resetFields()
			load()
		} catch (e: any) { message.error(e?.message || e) }
	}

	return (
		<Card title="规则管理" extra={<Button type="primary" onClick={() => setOpen(true)}>新增规则</Button>}>
			<Table rowKey="id" dataSource={data}
				columns={[
					{ title: '名称', dataIndex: 'name' },
					{ title: '等级', dataIndex: 'level' },
					{ title: '条件', dataIndex: 'condition_json', render: (v) => <code>{JSON.stringify(v)}</code> },
					{ title: '启用', dataIndex: 'is_active', render: (v) => v ? '是' : '否' },
				]}
			/>
			<Modal title="新增规则" open={open} onOk={onCreate} onCancel={() => setOpen(false)}>
				<Form form={form} layout="vertical" initialValues={{ level: 1, is_active: true, condition_json: JSON.stringify({ score_gte: 0.8 }, null, 2) }}>
					<Form.Item name="name" label="名称" rules={[{ required: true }]}>
						<Input />
					</Form.Item>
					<Form.Item name="level" label="等级" rules={[{ required: true }]}>
						<InputNumber min={1} max={3} />
					</Form.Item>
					<Form.Item name="condition_json" label="条件(JSON)">
						<Input.TextArea rows={6} />
					</Form.Item>
					<Form.Item name="is_active" label="启用" valuePropName="checked">
						<Switch />
					</Form.Item>
				</Form>
			</Modal>
		</Card>
	)
}
