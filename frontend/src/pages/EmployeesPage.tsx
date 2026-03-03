import { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, InputNumber,
  Space, Typography, Tag, message, Popconfirm, Card, DatePicker,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getEmployees, createEmployee, updateEmployee, deactivateEmployee } from '../services/api';
import dayjs from 'dayjs';

const { Title } = Typography;

const CURRENCIES = ['INR', 'GBP', 'AED', 'USD'];
const EXCEPTION_TYPES = [
  { value: '', label: 'None' },
  { value: 'fixed_salary', label: 'Fixed Salary' },
  { value: 'full_month_absent', label: 'Full Month Absent' },
];

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<any>(null);
  const [form] = Form.useForm();

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

  const columns = [
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      sorter: (a: any, b: any) => a.name.localeCompare(b.name),
    },
    {
      title: 'Salary', dataIndex: 'salary', key: 'salary',
      render: (val: number, rec: any) => `${rec.currency} ${val.toLocaleString()}`,
      sorter: (a: any, b: any) => a.salary - b.salary,
    },
    {
      title: 'Currency', dataIndex: 'currency', key: 'currency',
      render: (val: string) => <Tag color="blue">{val}</Tag>,
    },
    {
      title: 'Exception', dataIndex: 'exception_type', key: 'exception_type',
      render: (val: string) => val ? (
        <Tag color={val === 'fixed_salary' ? 'geekblue' : val === 'full_month_absent' ? 'red' : 'orange'}>
          {val.replace(/_/g, ' ').toUpperCase()}
        </Tag>
      ) : <Tag color="default">Standard</Tag>,
    },
    {
      title: 'Status', dataIndex: 'is_active', key: 'is_active',
      render: (val: boolean) => val
        ? <Tag color="green">Active</Tag>
        : <Tag color="red">Inactive</Tag>,
    },
    {
      title: 'Insightful Name', dataIndex: 'insightful_name', key: 'insightful_name',
      render: (val: string) => val || '-',
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, record: any) => (
        <Space>
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0 }}>Employees</Title>
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
      </div>

      <Card>
        <Table
          dataSource={employees}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (total) => `${total} employees` }}
          size="middle"
        />
      </Card>

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
    </Space>
  );
}
