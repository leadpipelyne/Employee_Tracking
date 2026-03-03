import { useState, useEffect } from 'react';
import {
  Card, Button, Select, InputNumber, Space, Typography, Table, Tag,
  message, Statistic, Row, Col, Form, Modal, Alert, Descriptions, Spin,
} from 'antd';
import {
  CalculatorOutlined, CheckCircleOutlined, PlayCircleOutlined,
} from '@ant-design/icons';
import { getConfig, createConfig, runPayroll, getPayrollResults, finalizePayroll } from '../services/api';

const { Title, Text } = Typography;

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const STATUS_COLORS: Record<string, string> = {
  DEDUCT: 'red',
  OK: 'gold',
  ADDITION: 'green',
  FIXED: 'blue',
  FULL_ABSENT: 'default',
};

const STATUS_ROW_COLORS: Record<string, string> = {
  DEDUCT: '#fff1f0',
  OK: '#fffbe6',
  ADDITION: '#f6ffed',
  FIXED: '#e6f4ff',
  FULL_ABSENT: '#f5f5f5',
};

export default function PayrollPage() {
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [config, setConfig] = useState<any>(null);
  const [payrollData, setPayrollData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [setupOpen, setSetupOpen] = useState(false);
  const [setupForm] = Form.useForm();

  const loadData = async () => {
    setLoading(true);
    try {
      const configRes = await getConfig(selectedYear, selectedMonth);
      setConfig(configRes.data);
      try {
        const payrollRes = await getPayrollResults(selectedYear, selectedMonth);
        setPayrollData(payrollRes.data);
      } catch {
        setPayrollData(null);
      }
    } catch {
      setConfig(null);
      setPayrollData(null);
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, [selectedMonth, selectedYear]);

  const handleSetup = async (values: any) => {
    try {
      await createConfig({
        month: selectedMonth,
        year: selectedYear,
        working_days: values.working_days,
        full_day_hours: values.full_day_hours || 9,
        threshold_hours_per_day: values.threshold_hours_per_day || 8.25,
      });
      message.success('Month configured successfully');
      setSetupOpen(false);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to create configuration');
    }
  };

  const handleRunPayroll = async () => {
    setCalculating(true);
    try {
      const res = await runPayroll(selectedYear, selectedMonth);
      setPayrollData(res.data);
      message.success(`Payroll calculated for ${res.data.summary.total_employees} employees`);
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Payroll calculation failed');
    }
    setCalculating(false);
  };

  const handleFinalize = async () => {
    try {
      await finalizePayroll(selectedYear, selectedMonth);
      message.success('Payroll finalized!');
      loadData();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Finalization failed');
    }
  };

  const columns = [
    {
      title: 'Employee', dataIndex: 'employee_name', key: 'employee_name',
      fixed: 'left' as const, width: 180,
      sorter: (a: any, b: any) => a.employee_name.localeCompare(b.employee_name),
    },
    {
      title: 'Currency', dataIndex: 'currency', key: 'currency', width: 80,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: 'Salary', dataIndex: 'salary', key: 'salary', width: 120,
      render: (v: number) => v.toLocaleString(undefined, { minimumFractionDigits: 2 }),
      align: 'right' as const,
    },
    {
      title: 'Actual Hours', dataIndex: 'actual_hours', key: 'actual_hours', width: 110,
      render: (v: number) => v.toFixed(2),
      align: 'right' as const,
    },
    {
      title: 'Leave Hours', dataIndex: 'leave_hours', key: 'leave_hours', width: 110,
      render: (v: number) => v.toFixed(2),
      align: 'right' as const,
    },
    {
      title: 'Manual Hrs', dataIndex: 'manual_hours', key: 'manual_hours', width: 100,
      render: (v: number) => v > 0 ? <Text type="warning">{v.toFixed(2)}</Text> : '0.00',
      align: 'right' as const,
    },
    {
      title: 'Total Billable', dataIndex: 'total_billable_hours', key: 'total_billable_hours', width: 120,
      render: (v: number) => <Text strong>{v.toFixed(2)}</Text>,
      align: 'right' as const,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 120,
      render: (v: string) => <Tag color={STATUS_COLORS[v] || 'default'}>{v}</Tag>,
    },
    {
      title: 'Deduction', dataIndex: 'deduction', key: 'deduction', width: 120,
      render: (v: number) => v > 0
        ? <Text type="danger" strong>{v.toLocaleString(undefined, { minimumFractionDigits: 2 })}</Text>
        : '0.00',
      align: 'right' as const,
    },
    {
      title: 'Addition', dataIndex: 'addition', key: 'addition', width: 120,
      render: (v: number) => v > 0
        ? <Text type="success" strong>{v.toLocaleString(undefined, { minimumFractionDigits: 2 })}</Text>
        : '0.00',
      align: 'right' as const,
    },
    {
      title: 'Final Salary', dataIndex: 'final_salary', key: 'final_salary', width: 130,
      render: (v: number) => <Text strong>{v.toLocaleString(undefined, { minimumFractionDigits: 2 })}</Text>,
      align: 'right' as const,
    },
    {
      title: 'Total Pay', dataIndex: 'total_pay', key: 'total_pay', width: 130,
      render: (v: number) => <Text strong>{v.toLocaleString(undefined, { minimumFractionDigits: 2 })}</Text>,
      align: 'right' as const,
    },
    {
      title: 'Match', dataIndex: 'insightful_match', key: 'insightful_match', width: 140,
      render: (v: string) => v?.startsWith('Yes') ? <Tag color="green">{v}</Tag> : <Tag color="red">{v}</Tag>,
    },
    {
      title: 'Notes', dataIndex: 'notes', key: 'notes', width: 250,
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>Payroll</Title>
        <Space>
          <Select
            value={selectedMonth}
            onChange={setSelectedMonth}
            style={{ width: 140 }}
            options={MONTHS.map((m, i) => ({ value: i + 1, label: m }))}
          />
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 100 }}
            options={[2025, 2026, 2027].map(y => ({ value: y, label: String(y) }))}
          />
        </Space>
      </div>

      {loading ? (
        <Card><Spin tip="Loading..." /></Card>
      ) : !config ? (
        <Card>
          <Alert
            message={`No configuration for ${MONTHS[selectedMonth - 1]} ${selectedYear}`}
            description="Set up this month to begin payroll processing."
            type="info"
            showIcon
            action={
              <Button type="primary" onClick={() => {
                setupForm.setFieldsValue({ working_days: 20, full_day_hours: 9, threshold_hours_per_day: 8.25 });
                setSetupOpen(true);
              }}>
                Set Up Month
              </Button>
            }
          />
        </Card>
      ) : (
        <>
          {/* Config Summary */}
          <Card size="small">
            <Descriptions size="small" column={6}>
              <Descriptions.Item label="Month">{MONTHS[config.month - 1]} {config.year}</Descriptions.Item>
              <Descriptions.Item label="Working Days">{config.working_days}</Descriptions.Item>
              <Descriptions.Item label="Threshold">{config.monthly_threshold} hrs</Descriptions.Item>
              <Descriptions.Item label="Expected">{config.monthly_expected} hrs</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={config.status === 'finalized' ? 'green' : config.status === 'calculated' ? 'blue' : 'orange'}>
                  {config.status.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Actions">
                <Space>
                  {config.status !== 'finalized' && (
                    <Button
                      type="primary"
                      icon={<CalculatorOutlined />}
                      onClick={handleRunPayroll}
                      loading={calculating}
                    >
                      Run Calculation
                    </Button>
                  )}
                  {config.status === 'calculated' && (
                    <Button
                      type="primary"
                      icon={<CheckCircleOutlined />}
                      onClick={handleFinalize}
                      style={{ background: '#52c41a' }}
                    >
                      Finalize
                    </Button>
                  )}
                </Space>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Summary Stats */}
          {payrollData?.summary && (
            <Row gutter={[16, 16]}>
              <Col xs={12} lg={4}>
                <Card size="small">
                  <Statistic title="Total Employees" value={payrollData.summary.total_employees} />
                </Card>
              </Col>
              <Col xs={12} lg={4}>
                <Card size="small">
                  <Statistic title="Deductions" value={payrollData.summary.deductions_count}
                    valueStyle={{ color: '#cf1322' }} suffix={`(${payrollData.summary.total_deductions.toLocaleString()})`} />
                </Card>
              </Col>
              <Col xs={12} lg={4}>
                <Card size="small">
                  <Statistic title="Additions" value={payrollData.summary.additions_count}
                    valueStyle={{ color: '#3f8600' }} suffix={`(${payrollData.summary.total_additions.toLocaleString()})`} />
                </Card>
              </Col>
              <Col xs={12} lg={4}>
                <Card size="small">
                  <Statistic title="OK" value={payrollData.summary.ok_count} valueStyle={{ color: '#d48806' }} />
                </Card>
              </Col>
              <Col xs={12} lg={4}>
                <Card size="small">
                  <Statistic title="Fixed" value={payrollData.summary.fixed_count} valueStyle={{ color: '#1890ff' }} />
                </Card>
              </Col>
              <Col xs={12} lg={4}>
                <Card size="small">
                  <Statistic title="Gross Payroll" value={payrollData.summary.total_gross_salary}
                    precision={0} valueStyle={{ color: '#2F5496' }} />
                </Card>
              </Col>
            </Row>
          )}

          {/* Results Table */}
          {payrollData?.results && (
            <Card title="Calculation Results" size="small">
              <Table
                dataSource={payrollData.results}
                columns={columns}
                rowKey="id"
                scroll={{ x: 1800 }}
                size="small"
                pagination={false}
                rowClassName={(record) => ''}
                onRow={(record) => ({
                  style: { backgroundColor: STATUS_ROW_COLORS[record.status] || '#fff' },
                })}
              />
            </Card>
          )}
        </>
      )}

      {/* Setup Modal */}
      <Modal
        title={`Set Up ${MONTHS[selectedMonth - 1]} ${selectedYear}`}
        open={setupOpen}
        onCancel={() => setSetupOpen(false)}
        onOk={() => setupForm.submit()}
      >
        <Form form={setupForm} layout="vertical" onFinish={handleSetup}>
          <Form.Item name="working_days" label="Working Days" rules={[{ required: true }]}>
            <InputNumber min={1} max={31} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="full_day_hours" label="Full Day Hours">
            <InputNumber min={1} max={24} step={0.25} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="threshold_hours_per_day" label="Threshold Hours Per Day (lunch grace)">
            <InputNumber min={1} max={24} step={0.25} style={{ width: '100%' }} />
          </Form.Item>
          <Alert
            message="Formula Reminder"
            description={
              <div>
                <p>Threshold = Working Days x {setupForm.getFieldValue('threshold_hours_per_day') || 8.25}</p>
                <p>Expected = Working Days x {setupForm.getFieldValue('full_day_hours') || 9}</p>
                <p>Below threshold = Deduction from full 9-hour day</p>
                <p>Between threshold and expected = OK (no change)</p>
                <p>Above expected = Overtime addition</p>
              </div>
            }
            type="info"
            style={{ marginBottom: 0 }}
          />
        </Form>
      </Modal>
    </Space>
  );
}
