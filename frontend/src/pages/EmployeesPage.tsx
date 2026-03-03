import { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, InputNumber,
  Space, Typography, Tag, message, Popconfirm, Card, DatePicker,
  Upload, Row, Col, Alert, Tooltip, Statistic,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, UploadOutlined,
  SearchOutlined, DownloadOutlined, EyeOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getEmployees, createEmployee, updateEmployee, deactivateEmployee, bulkUploadEmployees } from '../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;

const CURRENCIES = ['INR', 'GBP', 'AED', 'USD'];
const EXCEPTION_TYPES = [
  { value: '', label: 'None' },
  { value: 'fixed_salary', label: 'Fixed Salary' },
  { value: 'full_month_absent', label: 'Full Month Absent' },
];

const STATUS_FILTERS = [
  { text: 'Active', value: true },
  { text: 'Inactive', value: false },
];

const CURRENCY_FILTERS = CURRENCIES.map(c => ({ text: c, value: c }));

export default function EmployeesPage() {
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<any>(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploading, setUploading] = useState(false);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const res = await getEmployees(false);
      setEmployees(res.data);
    } catch {
      message.error('Failed to load employees');
    }
    setLoading(false);
  };

  useEffect(() => { fetchEmployees(); }, []);

  const filteredEmployees = employees.filter(emp => {
    if (!searchText) return true;
    const s = searchText.toLowerCase();
    return (
      emp.name?.toLowerCase().includes(s) ||
      emp.email?.toLowerCase().includes(s) ||
      emp.insightful_name?.toLowerCase().includes(s) ||
      emp.currency?.toLowerCase().includes(s)
    );
  });

  const handleSave = async (values: any) => {
    try {
      const data = {
        ...values,
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : null,
        exception_type: values.exception_type || null,
      };

      if (editingEmployee) {
        await updateEmployee(editingEmployee.id, data);
        message.success('Employee updated');
      } else {
        await createEmployee(data);
        message.success('Employee added');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingEmployee(null);
      fetchEmployees();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to save');
    }
  };

  const handleEdit = (record: any) => {
    setEditingEmployee(record);
    form.setFieldsValue({
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : null,
      exception_type: record.exception_type || '',
    });
    setModalOpen(true);
  };

  const handleDeactivate = async (id: number) => {
    try {
      await deactivateEmployee(id);
      message.success('Employee deactivated');
      fetchEmployees();
    } catch {
      message.error('Failed to deactivate');
    }
  };

  const handleBulkUpload = async (file: File) => {
    setUploading(true);
    setUploadResult(null);
    try {
      const res = await bulkUploadEmployees(file);
      setUploadResult(res.data);
      if (res.data.created > 0) {
        message.success(`${res.data.created} employees uploaded successfully`);
        fetchEmployees();
      }
      if (res.data.errors > 0) {
        message.warning(`${res.data.errors} rows had errors`);
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Upload failed');
    }
    setUploading(false);
  };

  const downloadTemplate = () => {
    const csvContent = 'name,email,salary,currency,start_date,exception_type,insightful_name\nJohn Smith,john@example.com,50000,INR,2024-01-15,,\nJane Doe,jane@example.com,4500,GBP,2024-03-01,fixed_salary,Jane D';
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'employee_upload_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const activeCount = employees.filter(e => e.is_active).length;
  const inactiveCount = employees.filter(e => !e.is_active).length;

  const columns = [
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      sorter: (a: any, b: any) => a.name.localeCompare(b.name),
      render: (name: string, record: any) => (
        <a onClick={() => navigate(`/employees/${record.id}`)} style={{ fontWeight: 500 }}>
          {name}
        </a>
      ),
    },
    {
      title: 'Email', dataIndex: 'email', key: 'email',
      render: (val: string) => val || <Text type="secondary">-</Text>,
      responsive: ['lg' as const],
    },
    {
      title: 'Salary', dataIndex: 'salary', key: 'salary',
      render: (val: number, rec: any) => `${rec.currency} ${val.toLocaleString()}`,
      sorter: (a: any, b: any) => a.salary - b.salary,
    },
    {
      title: 'Currency', dataIndex: 'currency', key: 'currency',
      render: (val: string) => <Tag color="blue">{val}</Tag>,
      filters: CURRENCY_FILTERS,
      onFilter: (value: any, record: any) => record.currency === value,
    },
    {
      title: 'Exception', dataIndex: 'exception_type', key: 'exception_type',
      render: (val: string) => val ? (
        <Tag color={val === 'fixed_salary' ? 'geekblue' : val === 'full_month_absent' ? 'red' : 'orange'}>
          {val.replace(/_/g, ' ').toUpperCase()}
        </Tag>
      ) : <Tag color="default">Standard</Tag>,
      filters: [
        { text: 'Standard', value: 'standard' },
        { text: 'Fixed Salary', value: 'fixed_salary' },
        { text: 'Full Month Absent', value: 'full_month_absent' },
      ],
      onFilter: (value: any, record: any) => {
        if (value === 'standard') return !record.exception_type;
        return record.exception_type === value;
      },
    },
    {
      title: 'Status', dataIndex: 'is_active', key: 'is_active',
      render: (val: boolean) => val
        ? <Tag color="green">Active</Tag>
        : <Tag color="red">Inactive</Tag>,
      filters: STATUS_FILTERS,
      onFilter: (value: any, record: any) => record.is_active === value,
    },
    {
      title: 'Insightful Name', dataIndex: 'insightful_name', key: 'insightful_name',
      render: (val: string) => val || <Text type="secondary">-</Text>,
      responsive: ['xl' as const],
    },
    {
      title: 'Actions', key: 'actions', width: 220,
      render: (_: any, record: any) => (
        <Space>
          <Tooltip title="View Profile">
            <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/employees/${record.id}`)} />
          </Tooltip>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            Edit
          </Button>
          {record.is_active && (
            <Popconfirm
              title="Deactivate this employee?"
              description="They will no longer appear in payroll calculations."
              onConfirm={() => handleDeactivate(record.id)}
            >
              <Button size="small" danger icon={<DeleteOutlined />}>
                Deactivate
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Employees</Title>
          <Text type="secondary">
            {activeCount} active, {inactiveCount} inactive — {employees.length} total
          </Text>
        </div>
        <Space wrap>
          <Button
            icon={<UploadOutlined />}
            onClick={() => { setUploadResult(null); setUploadModalOpen(true); }}
          >
            Bulk Upload
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingEmployee(null);
              form.resetFields();
              setModalOpen(true);
            }}
          >
            Add Employee
          </Button>
        </Space>
      </div>

      <Card>
        <div style={{ marginBottom: 16 }}>
          <Search
            placeholder="Search by name, email, or Insightful name..."
            allowClear
            enterButton={<SearchOutlined />}
            size="middle"
            style={{ maxWidth: 400 }}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={(value) => setSearchText(value)}
          />
        </div>
        <Table
          dataSource={filteredEmployees}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (total) => `${total} employees`, showSizeChanger: true, pageSizeOptions: ['10', '20', '50', '100'] }}
          size="middle"
          scroll={{ x: 900 }}
        />
      </Card>

      {/* Add/Edit Employee Modal */}
      <Modal
        title={editingEmployee ? 'Edit Employee' : 'Add New Employee'}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); setEditingEmployee(null); form.resetFields(); }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="name" label="Full Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. John Smith" />
          </Form.Item>
          <Form.Item name="email" label="Email">
            <Input placeholder="email@example.com" />
          </Form.Item>
          <Space size="large">
            <Form.Item name="salary" label="Monthly Salary" rules={[{ required: true }]}>
              <InputNumber min={0} style={{ width: 200 }} placeholder="50000" />
            </Form.Item>
            <Form.Item name="currency" label="Currency" initialValue="INR">
              <Select style={{ width: 120 }} options={CURRENCIES.map(c => ({ value: c, label: c }))} />
            </Form.Item>
          </Space>
          <Form.Item name="start_date" label="Start Date">
            <DatePicker style={{ width: 200 }} />
          </Form.Item>
          <Form.Item name="exception_type" label="Exception Type" initialValue="">
            <Select options={EXCEPTION_TYPES} />
          </Form.Item>
          <Form.Item name="insightful_name" label="Insightful Name (if different from Full Name)">
            <Input placeholder="Name as it appears in Insightful" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Bulk Upload Modal */}
      <Modal
        title="Bulk Upload Employees"
        open={uploadModalOpen}
        onCancel={() => { setUploadModalOpen(false); setUploadResult(null); }}
        footer={[
          <Button key="close" onClick={() => { setUploadModalOpen(false); setUploadResult(null); }}>
            Close
          </Button>,
        ]}
        width={700}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert
            message="Upload Format"
            description={
              <div>
                <p>Upload a <strong>CSV</strong> or <strong>JSON</strong> file with employee data.</p>
                <p><strong>Required columns:</strong> name, salary</p>
                <p><strong>Optional columns:</strong> email, currency (INR/GBP/AED/USD), start_date (YYYY-MM-DD), exception_type (fixed_salary/full_month_absent), insightful_name</p>
              </div>
            }
            type="info"
            showIcon
          />

          <Button icon={<DownloadOutlined />} onClick={downloadTemplate}>
            Download CSV Template
          </Button>

          <Upload.Dragger
            accept=".csv,.json"
            maxCount={1}
            beforeUpload={(file) => {
              handleBulkUpload(file);
              return false;
            }}
            showUploadList={false}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined style={{ fontSize: 48, color: '#2F5496' }} />
            </p>
            <p className="ant-upload-text">Click or drag a CSV/JSON file here</p>
            <p className="ant-upload-hint">Supports .csv and .json formats</p>
          </Upload.Dragger>

          {uploading && <Alert message="Uploading..." type="info" showIcon />}

          {uploadResult && (
            <div>
              <Row gutter={16}>
                <Col span={12}>
                  <Card size="small">
                    <Statistic title="Created" value={uploadResult.created} valueStyle={{ color: '#52c41a' }} />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <Statistic title="Errors" value={uploadResult.errors} valueStyle={{ color: uploadResult.errors > 0 ? '#ff4d4f' : '#8c8c8c' }} />
                  </Card>
                </Col>
              </Row>
              {uploadResult.error_details?.length > 0 && (
                <Alert
                  message="Upload Errors"
                  description={
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {uploadResult.error_details.map((err: string, i: number) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  }
                  type="error"
                  showIcon
                  style={{ marginTop: 12 }}
                />
              )}
              {uploadResult.created_employees?.length > 0 && (
                <Alert
                  message={`Successfully added ${uploadResult.created} employees`}
                  description={uploadResult.created_employees.map((e: any) => e.name).join(', ')}
                  type="success"
                  showIcon
                  style={{ marginTop: 12 }}
                />
              )}
            </div>
          )}
        </Space>
      </Modal>
    </Space>
  );
}

