import { useState, useEffect } from 'react';
import { Table, Card, Typography, Space, Tag, Select } from 'antd';
import { getAuditLog } from '../services/api';

const { Title } = Typography;

const ACTION_COLORS: Record<string, string> = {
  create: 'green',
  update: 'blue',
  deactivate: 'red',
  add_exception: 'orange',
  remove_exception: 'red',
  calculate_payroll: 'purple',
  finalize_payroll: 'cyan',
  add_compensation: 'gold',
};

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [entityFilter, setEntityFilter] = useState<string | undefined>();

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: any = { limit: 200 };
      if (entityFilter) params.entity_type = entityFilter;
      const res = await getAuditLog(params);
      setLogs(res.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchLogs(); }, [entityFilter]);

  const columns = [
    {
      title: 'Time', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: 'Action', dataIndex: 'action', key: 'action', width: 160,
      render: (v: string) => <Tag color={ACTION_COLORS[v] || 'default'}>{v.replace(/_/g, ' ').toUpperCase()}</Tag>,
    },
    {
      title: 'Entity', dataIndex: 'entity_type', key: 'entity_type', width: 140,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    { title: 'Entity ID', dataIndex: 'entity_id', key: 'entity_id', width: 80 },
    { title: 'Performed By', dataIndex: 'performed_by', key: 'performed_by', width: 200 },
    {
      title: 'Old Value', dataIndex: 'old_value', key: 'old_value', width: 250,
      render: (v: string) => v ? <code style={{ fontSize: 11 }}>{v.substring(0, 100)}</code> : '-',
    },
    {
      title: 'New Value', dataIndex: 'new_value', key: 'new_value', width: 250,
      render: (v: string) => v ? <code style={{ fontSize: 11 }}>{v.substring(0, 100)}</code> : '-',
    },
    { title: 'Reason', dataIndex: 'reason', key: 'reason', width: 200 },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>Audit Log</Title>
        <Select
          placeholder="Filter by entity"
          allowClear
          style={{ width: 200 }}
          onChange={setEntityFilter}
          options={[
            { value: 'employee', label: 'Employees' },
            { value: 'monthly_config', label: 'Monthly Config' },
            { value: 'monthly_exception', label: 'Exceptions' },
            { value: 'compensation_log', label: 'Compensation' },
          ]}
        />
      </div>

      <Card>
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          size="small"
          pagination={{ pageSize: 50 }}
        />
      </Card>
    </Space>
  );
}
