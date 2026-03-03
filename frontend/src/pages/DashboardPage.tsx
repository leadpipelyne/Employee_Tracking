import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Tag, Space, Alert } from 'antd';
import {
  TeamOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { getEmployees, healthCheck } from '../services/api';

const { Title, Text } = Typography;

export default function DashboardPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [apiStatus, setApiStatus] = useState<string>('checking');

  useEffect(() => {
    getEmployees().then((res) => setEmployees(res.data)).catch(() => {});
    healthCheck().then(() => setApiStatus('healthy')).catch(() => setApiStatus('error'));
  }, []);

  const currencyCounts: Record<string, number> = {};
  employees.forEach((e) => {
    currencyCounts[e.currency] = (currencyCounts[e.currency] || 0) + 1;
  });

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3}>Dashboard</Title>
        <Text type="secondary">Employee Tracking & Payroll System — Overview</Text>
      </div>

      {apiStatus === 'healthy' && (
        <Alert
          message="System Status: All Systems Operational"
          type="success"
          showIcon
          icon={<CheckCircleOutlined />}
        />
      )}

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Employees"
              value={employees.length}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#2F5496' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Monthly Payroll"
              value={employees.reduce((sum, e) => sum + e.salary, 0)}
              prefix={<DollarOutlined />}
              precision={0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Currencies"
              value={Object.keys(currencyCounts).length}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              {Object.entries(currencyCounts).map(([currency, count]) => (
                <Tag key={currency} color="blue">{currency}: {count}</Tag>
              ))}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="System Status"
              value={apiStatus === 'healthy' ? 'Online' : 'Checking...'}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: apiStatus === 'healthy' ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="Quick Guide — How This System Works" size="small">
        <Space direction="vertical">
          <Text><strong>Step 1:</strong> Go to <strong>Employees</strong> to add or manage your team.</Text>
          <Text><strong>Step 2:</strong> Go to <strong>Payroll</strong> to set up a month, configure exceptions, and run calculations.</Text>
          <Text><strong>Step 3:</strong> Review the color-coded results table — Red (Deduction), Green (Overtime), Yellow (OK).</Text>
          <Text><strong>Step 4:</strong> Finalize the payroll and download the Excel report.</Text>
          <Text><strong>Step 5:</strong> Check the <strong>Audit Log</strong> for a full history of every action.</Text>
        </Space>
      </Card>
    </Space>
  );
}
