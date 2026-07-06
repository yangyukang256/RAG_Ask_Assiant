import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore } from './stores/authStore';
import AuthGuard from './components/common/AuthGuard';
import AppLayout from './components/layout/AppLayout';
import LoginPage from './pages/Login';
import ChatPage from './pages/Chat';
import KnowledgeBasePage from './pages/KnowledgeBase';
import ChangePasswordPage from './pages/ChangePassword';

const App: React.FC = () => {
  const { isAuthenticated, loadUser } = useAuthStore();

  // 应用启动时，如果有 token 则加载用户信息
  useEffect(() => {
    const token = localStorage.getItem('kb_access_token');
    if (token) {
      loadUser();
    }
  }, []);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <Routes>
            <Route
              path="/login"
              element={isAuthenticated ? <Navigate to="/chat" replace /> : <LoginPage />}
            />
            <Route
              path="/change-password"
              element={<ChangePasswordPage />}
            />
            <Route
              element={
                <AuthGuard>
                  <AppLayout />
                </AuthGuard>
              }
            >
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/chat/:sessionId" element={<ChatPage />} />
              <Route
                path="/admin/knowledge"
                element={
                  <AuthGuard requireAdmin>
                    <KnowledgeBasePage />
                  </AuthGuard>
                }
              />
            </Route>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="*" element={<Navigate to="/chat" replace />} />
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
};

export default App;