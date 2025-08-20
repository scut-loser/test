import React from 'react'
import ReactDOM from 'react-dom/client'
import { Layout, Menu, ConfigProvider } from 'antd'
import 'antd/dist/reset.css'
import Dashboard from './pages/Dashboard'
import Events from './pages/Events'
import Rules from './pages/Rules'
import System from './pages/System'

const { Header, Sider, Content } = Layout

function App() {
	const [menu, setMenu] = React.useState('dashboard')
	return (
		<ConfigProvider theme={{ token: { colorPrimary: '#1677ff' } }}>
			<Layout style={{ minHeight: '100vh' }}>
				<Sider collapsible>
					<div style={{ color: '#fff', padding: 16, fontWeight: 600 }}>风控监控</div>
					<Menu theme="dark" mode="inline" selectedKeys={[menu]} onSelect={(e) => setMenu(e.key)}
						items={[
							{ key: 'dashboard', label: '仪表盘' },
							{ key: 'events', label: '预警事件' },
							{ key: 'rules', label: '规则管理' },
							{ key: 'system', label: '系统状态' },
						]}
					/>
				</Sider>
				<Layout>
					<Header style={{ background: '#fff' }} />
					<Content style={{ margin: 16 }}>
						{menu === 'dashboard' && <Dashboard />}
						{menu === 'events' && <Events />}
						{menu === 'rules' && <Rules />}
						{menu === 'system' && <System />}
					</Content>
				</Layout>
			</Layout>
		</ConfigProvider>
	)
}

ReactDOM.createRoot(document.getElementById('root')!).render(
	<React.StrictMode>
		<App />
	</React.StrictMode>
)
