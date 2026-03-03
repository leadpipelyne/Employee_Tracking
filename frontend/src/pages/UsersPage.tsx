import { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Space, Typography,
  Tag, message, Card, Popconfirm,
} from 'antd';
import {
  PlusOutlined, EditOutlined, LockOutlined, UserOutlined,
} from '@ant-design/icons';
import { getUsers, createUser, updateUser, resetUserPassword } from '../services/api';

const { Title, Text } = Typography;

const ROLES = [
  { value: 'admin', label: 'Admin', color: 'red' },
  { value: 'hr', label: 'HR', color: 'blue' },
  { value: 'manager', label: 'Manager', color: 'orange' },
  { value: 'viewer', label: 'Viewer', color: 'default' },
];

const ROLE_COLOR: Record<string, string> = {
  admin: 'red',
  hr: 'blue',
  manager: 'orange',
  viewer: 'default',
};

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await getUsers();
      setUsers(res.data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        message.error('Admin access required');
      } else {
        message.error('Failed to load users');
      }
    }
    setLoading(false);
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreateUser = async (values: any) => {
    try {
      await createUser(values);
      message.success('User created successfully');
      setModalOpen(false);
      form.resetFields();
      fetchUsers();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await updateUser(userId, { role: newRole });
      message.success('Role updated');
      fetchUsers();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleToggleActive = async (userId: number, currentActive: boolean) => {
    try {
      await updateUser(userId, { is_active: !currentActive });
      message.success(currentActive ? 'User deactivated' : 'User activated');
      fetchUsers();
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleResetPassword = async (values: any) => {
    if (!selectedUser) return;
    try {
      await resetUserPassword(selectedUser.id, values.password);
      message.success(`Password reset for ${selectedUser.email}`);
      setPasswordModalOpen(false);
      passwordForm.resetFields();
      setSelectedUser(null);
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Failed to reset password');
    }
  };

  const columns = [
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      sorter: (a: any, b: any) => a.name.localeCompare(b.name),
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: 'Email', dataIndex: 'email', key: 'email',
    },
    {
      title: 'Role', dataIndex: 'role', key: 'role',
      render: (role: string, record: any) => (
        <Select
          value={role}
          size="small"
          style={{ width: 120 }}
          onChange={(val) => handleRoleChange(record.id, val)}
          options={ROLES.map(r => ({
            value: r.value,
            label: <Tag color={r.color}>{r.label}</Tag>,
          }))}
        />
      ),
    },
    {
      title: 'Status', dataIndex: 'is_active', key: 'is_active',
      render: (val: boolean) => val
        ? <Tag color="green">Active</Tag>
        : <Tag color="red">Inactive</Tag>,
    },
    {
      title: 'Actions', key: 'actions', width: 250,
      render: (_: any, record: any) => (
        <Space>
          <Button
            size="small"
            icon={<LockOutlined />}
            onClick={() => {
              setSelectedUser(record);
              passwordForm.resetFields();
              setPasswordModalOpen(true);
            }}
          >
            Reset Password
          </Button>
          <Popconfirm
            title={record.is_active ? 'Deactivate this user?' : 'Activate this user?'}
            onConfirm={() => handleToggleActive(record.id, record.is_active)}
          >
            <Button size="small" danger={record.is_active}>
              {record.is_active ? 'Deactivate' : 'Activate'}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>User Management</Title>
          <Text type="secondary">Manage system users and their access roles</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields();
            setModalOpen(true);
          }}
        >
          Add User
        </Button>
      </div>

      <Card>
        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="middle"
        />
      </Card>

      {/* Create User Modal */}
      <Modal
        title="Create New User"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        onOk={() => form.submit()}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateUser}>
          <Form.Item name="name" label="Full Name" rules={[{ required: true }]}>
            <Input prefix={<UserOutlined />} placeholder="John Smith" />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="user@company.com" />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, min: 6 }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Minimum 6 characters" />
          </Form.Item>
          <Form.Item name="role" label="Role" initialValue="viewer">
            <Select options={ROLES} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Reset Password Modal */}
      <Modal
        title={`Reset Password for ${selectedUser?.name || ''}`}
        open={passwordModalOpen}
        onCancel={() => { setPasswordModalOpen(false); setSelectedUser(null); }}
        onOk={() => passwordForm.submit()}
      >
        <Form form={passwordForm} layout="vertical" onFinish={handleResetPassword}>
          <Form.Item name="password" label="New Password" rules={[{ required: true, min: 6 }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Enter new password" />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
