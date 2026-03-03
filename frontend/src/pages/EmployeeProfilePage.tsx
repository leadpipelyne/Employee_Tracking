import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Typography, Tag, Space, Descriptions, Table, Tabs, Button,
  Spin, Empty, Statistic, Row, Col, message, Badge, Timeline,
} from 'antd';
import {
  ArrowLeftOutlined, UserOutlined, DollarOutlined, ClockCircleOutlined,
  CalendarOutlined, FileTextOutlined, HistoryOutlined,
} from '@ant-design/icons';
import { getEmployeeProfile } from '../services/api';

const { Title, Text } = Typography;

const STATUS_COLORS: Record<string, string> = {
  DEDUCT: '#ff4d4f',
  OK: '#faad14',
  ADDITION: '#52c41a',
  FIXED: '#1890ff',
  FULL_ABSENT: '#8c8c8c',
};

const STATUS_LABELS: Record<string, string> = {
  DEDUCT: 'Deduction',
  OK: 'OK',
  ADDITION: 'Overtime',
  FIXED: 'Fixed Salary',
  FULL_ABSENT: 'Full Absent',
};

const MONTH_NAMES = [
  '', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export default function EmployeeProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getEmployeeProfile(parseInt(id))
      .then((res) => setProfile(res.data))
      .catch(() => message.error('Failed to load employee profile'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!profile) {
    return <Empty description="Employee not found" />;
  }

  const { employee, payroll_history, exceptions, compensation_logs, leave_balances, leave_requests } = profile;

  const payrollColumns = [
    {
      title: 'Month',
      key: 'month',
      render: (_: any, r: any) => `${MONTH_NAMES[r.month]} ${r.year}`,
      width: 140,
    },
    {
      title: 'Actual Hours',
      dataIndex: 'actual_hours',
      render: (v: number) => v?.toFixed(1),
    },
    {
      title: 'Billable Hours',
      dataIndex: 'total_billable_hours',
      render: (v: number) => v?.toFixed(1),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (v: string) => (
        <Tag color={STATUS_COLORS[v] || 'default'}>{STATUS_LABELS[v] || v}</Tag>
      ),
    },
    {
      title: 'Deduction',
      dataIndex: 'deduction',
      render: (v: number) => v > 0 ? <Text type="danger">-{v.toLocaleString()}</Text> : '-',
    },
    {
      title: 'Addition',
      dataIndex: 'addition',
      render: (v: number) => v > 0 ? <Text type="success">+{v.toLocaleString()}</Text> : '-',
    },
    {
      title: 'Final Salary',
      dataIndex: 'final_salary',
      render: (v: number) => <Text strong>{employee.currency} {v?.toLocaleString()}</Text>,
    },
    {
      title: 'Total Pay',
      dataIndex: 'total_pay',
      render: (v: number) => `${employee.currency} ${v?.toLocaleString()}`,
    },
  ];

  const exceptionColumns = [
    {
      title: 'Type',
      dataIndex: 'exception_type',
      render: (v: string) => <Tag>{v?.replace(/_/g, ' ').toUpperCase()}</Tag>,
    },
    { title: 'Value', dataIndex: 'value', render: (v: string) => v || '-' },
    { title: 'Reason', dataIndex: 'reason', render: (v: string) => v || '-' },
    { title: 'Created By', dataIndex: 'created_by', render: (v: string) => v || '-' },
    { title: 'Date', dataIndex: 'created_at', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
  ];

  const compensationColumns = [
    {
      title: 'Month',
      key: 'month',
      render: (_: any, r: any) => `${MONTH_NAMES[r.month]} ${r.year}`,
    },
    { title: 'Hours', dataIndex: 'hours', render: (v: number) => v?.toFixed(1) },
    { title: 'Reason', dataIndex: 'reason' },
    { title: 'Submitted By', dataIndex: 'submitted_by', render: (v: string) => v || '-' },
    { title: 'Date', dataIndex: 'created_at', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
  ];

  const leaveColumns = [
    { title: 'Type', dataIndex: 'leave_type', render: (v: string) => v || 'General' },
    { title: 'Start', dataIndex: 'start_date' },
    { title: 'End', dataIndex: 'end_date' },
    { title: 'Days', dataIndex: 'num_days' },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (v: string) => (
        <Tag color={v === 'approved' ? 'green' : v === 'rejected' ? 'red' : 'gold'}>
          {v?.toUpperCase()}
        </Tag>
      ),
    },
    { title: 'Reason', dataIndex: 'reason', render: (v: string) => v || '-' },
  ];

  // Calculate stats from payroll history
  const totalDeductions = payroll_history.reduce((sum: number, p: any) => sum + (p.deduction || 0), 0);
  const totalAdditions = payroll_history.reduce((sum: number, p: any) => sum + (p.addition || 0), 0);
  const avgHours = payroll_history.length > 0
    ? payroll_history.reduce((sum: number, p: any) => sum + (p.actual_hours || 0), 0) / payroll_history.length
    : 0;

  const tabItems = [
    {
      key: 'payroll',
      label: (
        <span><DollarOutlined /> Payroll History ({payroll_history.length})</span>
      ),
      children: payroll_history.length > 0 ? (
        <Table
          dataSource={payroll_history}
          columns={payrollColumns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 12 }}
          scroll={{ x: 800 }}
        />
      ) : (
        <Empty description="No payroll history yet" />
      ),
    },
    {
      key: 'exceptions',
      label: (
        <span><FileTextOutlined /> Exceptions ({exceptions.length})</span>
      ),
      children: exceptions.length > 0 ? (
        <Table
          dataSource={exceptions}
          columns={exceptionColumns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 10 }}
        />
      ) : (
        <Empty description="No exceptions" />
      ),
    },
    {
      key: 'compensation',
      label: (
        <span><ClockCircleOutlined /> Manual Hours ({compensation_logs.length})</span>
      ),
      children: compensation_logs.length > 0 ? (
        <Table
          dataSource={compensation_logs}
          columns={compensationColumns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 10 }}
        />
      ) : (
        <Empty description="No manual hour adjustments" />
      ),
    },
    {
      key: 'leave',
      label: (
        <span><CalendarOutlined /> Leave ({leave_requests.length})</span>
      ),
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {leave_balances.length > 0 && (
            <Row gutter={16}>
              {leave_balances.map((lb: any) => (
                <Col key={lb.id} xs={24} sm={8}>
                  <Card size="small" title={`Year ${lb.year}`}>
                    <Row gutter={8}>
                      <Col span={8}>
                        <Statistic title="Accrued" value={lb.accrued_days} suffix="days" valueStyle={{ fontSize: 16 }} />
                      </Col>
                      <Col span={8}>
                        <Statistic title="Used" value={lb.used_days} suffix="days" valueStyle={{ fontSize: 16, color: '#ff4d4f' }} />
                      </Col>
                      <Col span={8}>
                        <Statistic title="Remaining" value={lb.remaining_days} suffix="days" valueStyle={{ fontSize: 16, color: '#52c41a' }} />
                      </Col>
                    </Row>
                  </Card>
                </Col>
              ))}
            </Row>
          )}
          {leave_requests.length > 0 ? (
            <Table
              dataSource={leave_requests}
              columns={leaveColumns}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 10 }}
            />
          ) : (
            <Empty description="No leave requests" />
          )}
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/employees')}>
        Back to Employees
      </Button>

      {/* Employee Header Card */}
      <Card>
        <Row gutter={[24, 16]} align="middle">
          <Col xs={24} md={12}>
            <Space direction="vertical" size={4}>
              <Space align="center">
                <Title level={3} style={{ margin: 0 }}>{employee.name}</Title>
                <Tag color={employee.is_active ? 'green' : 'red'}>
                  {employee.is_active ? 'Active' : 'Inactive'}
                </Tag>
                {employee.exception_type && (
                  <Tag color="orange">
                    {employee.exception_type.replace(/_/g, ' ').toUpperCase()}
                  </Tag>
                )}
              </Space>
              {employee.email && <Text type="secondary">{employee.email}</Text>}
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Descriptions size="small" column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="Monthly Salary">
                <Text strong>{employee.currency} {employee.salary?.toLocaleString()}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Currency">
                <Tag color="blue">{employee.currency}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Start Date">
                {employee.start_date || 'Not set'}
              </Descriptions.Item>
              <Descriptions.Item label="Insightful Name">
                {employee.insightful_name || <Text type="secondary">Same as name</Text>}
              </Descriptions.Item>
            </Descriptions>
          </Col>
        </Row>
      </Card>

      {/* Quick Stats */}
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Payroll Runs"
              value={payroll_history.length}
              prefix={<HistoryOutlined />}
              valueStyle={{ color: '#2F5496' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Avg Hours/Month"
              value={avgHours}
              precision={1}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total Deductions"
              value={totalDeductions}
              precision={0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total Overtime"
              value={totalAdditions}
              precision={0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Detailed Tabs */}
      <Card>
        <Tabs items={tabItems} defaultActiveKey="payroll" />
      </Card>
    </Space>
  );
}
