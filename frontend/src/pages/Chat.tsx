import React, { useEffect, useRef, useCallback, useState } from 'react';
import {
  Layout, List, Typography, Input, Button, Space, Card, Tag, message, theme,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, SendOutlined, RobotOutlined, UserOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useChatStore } from '../stores/chatStore';
import type { Message, CitationItem } from '../types/chat';

const { Sider, Content } = Layout;
const { Text, Paragraph } = Typography;
const { TextArea } = Input;

const CitationCard: React.FC<{ citation: CitationItem }> = ({ citation }) => (
  <Card
    size="small"
    style={{ marginBottom: 4, background: '#f6f8fa' }}
    styles={{ body: { padding: '8px 12px' } }}
  >
    <Space direction="vertical" size={2} style={{ width: '100%' }}>
      <Space>
        <FileTextOutlined />
        <Text type="secondary" style={{ fontSize: 12 }}>{citation.document_name}</Text>
        <Tag color="blue" style={{ fontSize: 10 }}>{(citation.score * 100).toFixed(0)}%</Tag>
      </Space>
      <Text style={{ fontSize: 12 }}>{citation.content.slice(0, 150)}...</Text>
    </Space>
  </Card>
);

const MessageItem: React.FC<{ msg: Message }> = ({ msg }) => (
  <div style={{
    display: 'flex',
    gap: 12,
    marginBottom: 20,
    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
  }}>
    <div style={{
      width: 36, height: 36, borderRadius: '50%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: msg.role === 'user' ? '#1677ff' : '#52c41a',
      color: '#fff', flexShrink: 0,
    }}>
      {msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
    </div>
    <div style={{
      maxWidth: '80%',
      background: msg.role === 'user' ? '#e6f4ff' : '#f6f8fa',
      borderRadius: 12,
      padding: '10px 16px',
      borderTopLeftRadius: msg.role === 'user' ? 12 : 2,
      borderTopRightRadius: msg.role === 'user' ? 2 : 12,
    }}>
      <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</Paragraph>
      {msg.citations && msg.citations.length > 0 && (
        <div style={{ marginTop: 12, borderTop: '1px solid #e8e8e8', paddingTop: 8 }}>
          <Text type="secondary" style={{ fontSize: 12, fontWeight: 'bold' }}>引用来源：</Text>
          {msg.citations.map((c, i) => (
            <CitationCard key={i} citation={c} />
          ))}
        </div>
      )}
    </div>
  </div>
);

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const { sessionId: urlSessionId } = useParams<{ sessionId: string }>();
  const {
    sessions, messages, isStreaming, streamingText,
    loadSessions, createSession, deleteSession, loadMessages, sendMessage,
  } = useChatStore();
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { token: themeToken } = theme.useToken();

  // 当前选中的会话 ID（从 URL 解析）
  const activeSessionId = urlSessionId ? parseInt(urlSessionId) : null;

  // 初始化加载会话列表
  useEffect(() => {
    loadSessions();
  }, []);

  // URL 中 sessionId 变化时，加载对应消息
  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId);
    } else {
      // 没有选中会话，清空消息
      useChatStore.setState({ messages: [], streamingText: '' });
    }
  }, [urlSessionId]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const handleSend = useCallback(async () => {
    if (!inputText.trim() || sending) return;
    let sid = activeSessionId;
    if (!sid) {
      // 如果没有会话，先创建再发送
      const session = await createSession();
      sid = session.id;
      navigate(`/chat/${sid}`, { replace: true });
    }
    setSending(true);
    const msg = inputText.trim();
    setInputText('');
    try {
      await sendMessage(sid, msg);
      // 发完后刷新会话列表（更新标题和消息数）
      loadSessions();
    } catch {
      message.error('发送失败');
    } finally {
      setSending(false);
    }
  }, [inputText, sending, activeSessionId, createSession, sendMessage, navigate, loadSessions]);

  const handleNewSession = async () => {
    const session = await createSession();
    navigate(`/chat/${session.id}`, { replace: true });
  };

  const handleSelectSession = (id: number) => {
    navigate(`/chat/${id}`, { replace: true });
  };

  const handleDeleteSession = async (id: number) => {
    await deleteSession(id);
    if (activeSessionId === id) {
      navigate('/chat', { replace: true });
    }
  };

  return (
    <Layout style={{ height: 'calc(100vh - 56px)' }}>
      {/* 会话侧边栏 */}
      <Sider
        width={280}
        theme="light"
        style={{
          borderRight: `1px solid ${themeToken.colorBorderSecondary}`,
          overflow: 'auto',
        }}
      >
        <div style={{ padding: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={handleNewSession}
          >
            新会话
          </Button>
        </div>
        <List
          dataSource={sessions}
          renderItem={(session) => (
            <List.Item
              key={session.id}
              onClick={() => handleSelectSession(session.id)}
              style={{
                cursor: 'pointer',
                padding: '10px 16px',
                background: session.id === activeSessionId ? '#e6f4ff' : 'transparent',
              }}
              actions={[
                <Button
                  key="del"
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={(e) => { e.stopPropagation(); handleDeleteSession(session.id); }}
                />,
              ]}
            >
              <List.Item.Meta
                title={<Text style={{ fontSize: 14 }}>{session.title}</Text>}
                description={
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {session.message_count} 条消息
                  </Text>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无会话，点击上方按钮创建' }}
        />
      </Sider>

      {/* 聊天内容区 */}
      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        {activeSessionId ? (
          <>
            <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
              {messages.map((msg) => (
                <MessageItem key={msg.id} msg={msg} />
              ))}
              {isStreaming && streamingText && (
                <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: '#52c41a', color: '#fff',
                  }}>
                    <RobotOutlined />
                  </div>
                  <div style={{
                    maxWidth: '80%', background: '#f6f8fa',
                    borderRadius: 12, padding: '10px 16px',
                    borderTopLeftRadius: 2,
                  }}>
                    <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{streamingText}</Paragraph>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div style={{
              padding: '16px 24px',
              borderTop: `1px solid ${themeToken.colorBorderSecondary}`,
              background: themeToken.colorBgContainer,
            }}>
              <Space.Compact style={{ width: '100%' }}>
                <TextArea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }}
                  placeholder="输入您的问题，按 Enter 发送..."
                  rows={2}
                  disabled={isStreaming}
                  style={{ resize: 'none' }}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  loading={isStreaming}
                  style={{ height: 'auto' }}
                >
                  发送
                </Button>
              </Space.Compact>
            </div>
          </>
        ) : (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column',
            justifyContent: 'center', alignItems: 'center', color: '#999',
          }}>
            <RobotOutlined style={{ fontSize: 64, marginBottom: 16 }} />
            <Text type="secondary" style={{ fontSize: 18 }}>选择或创建会话开始提问</Text>
          </div>
        )}
      </Content>
    </Layout>
  );
};

export default ChatPage;