import React from 'react';
import { Layout, Menu, Dropdown, Avatar, Typography, theme } from 'antd';
import {
  MessageOutlined, BookOutlined, UserOutlined,
  LogoutOutlined, KeyOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const { Header, Content } = Layout;
const { Text } = Typography;

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAdmin, logout } = useAuthStore();
  const { token: themeToken } = theme.useToken();

  const menuItems = [
    { key: '/chat', icon: <MessageOutlined />, label: 'AI 问答' },
    ...(isAdmin
      ? [{ key: '/admin/knowledge', icon: <BookOutlined />, label: '知识库管理' }]
      : []),
  ];

  const currentPath = '/' + location.pathname.split('/')[1];

  const userMenuItems = [
    { key: 'password', icon: <KeyOutlined />, label: '修改密码' },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          padding: '0 24px',
          background: themeToken.colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: `1px solid ${themeToken.colorBorderSecondary}`,
          height: 56,
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        {/* 左侧：Logo + 导航菜单 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <Text strong style={{ fontSize: 18, color: themeToken.colorPrimary, whiteSpace: 'nowrap' }}>
            RAG 知识库
          </Text>
          <Menu
            mode="horizontal"
            selectedKeys={[currentPath]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ border: 'none', background: 'transparent', flex: 1, minWidth: 0 }}
          />
        </div>

        {/* 右侧：用户信息 */}
        <Dropdown
          menu={{
            items: userMenuItems,
            onClick: ({ key }) => {
              if (key === 'logout') { logout(); navigate('/login'); }
              if (key === 'password') navigate('/change-password');
            },
          }}
        >
          <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <Avatar icon={<UserOutlined />} size="small" />
            <Text>{user?.username}</Text>
          </div>
        </Dropdown>
      </Header>
      <Content style={{ overflow: 'auto' }}>
        <Outlet />
      </Content>
    </Layout>
  );
};

export default AppLayout;