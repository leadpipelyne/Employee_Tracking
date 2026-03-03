import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Typography, Space, Tag } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  DollarOutlined,
  AuditOutlined,
  LogoutOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { getMe } from '../services/api';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

export default function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    getMe().then((res) => setUser(res.data)).catch(() => {
      localStorage.removeItem('token');
      navigate('/login');
    });
  }, [navigate]);

  const menuItems: any[] = [
    { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/employees', icon: <TeamOutlined />, label: 'Employees' },
    { key: '/payroll', icon: <DollarOutlined />, label: 'Payroll' },
    { key: '/audit', icon: <AuditOutlined />, label: 'Audit Log' },
  ];

  // Admin-only: User Management
  if (user?.role === 'admin') {
    menuItems.push({ key: '/users', icon: <SettingOutlined />, label: 'User Management' });
  }

  const ROLE_COLORS: Record<string, string> = {
    admin: 'red', hr: 'blue', manager: 'orange', viewer: 'default',
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: '#001529' }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <Text strong style={{ color: '#fff', fontSize: collapsed ? 14 : 16 }}>
            {collapsed ? 'ET' : 'Employee Tracker'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        }}>
          <Text strong style={{ fontSize: 18, color: '#2F5496' }}>
            Employee Tracking & Payroll System
          </Text>
          <Space>
            <UserOutlined />
            <Text>{user?.name}</Text>
            <Tag color={ROLE_COLORS[user?.role] || 'default'}>{user?.role?.toUpperCase()}</Tag>
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={handleLogout}
            >
              Logout
            </Button>
          </Space>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#f5f5f5', minHeight: 360 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
