import React, { useEffect, useState } from 'react';
import {
  Card, Table, Button, Upload, Space, Tag, Modal, message, Typography, Drawer,
  Descriptions, Progress, Popconfirm, Input,
} from 'antd';
import {
  UploadOutlined, DeleteOutlined, ReloadOutlined, EyeOutlined, SearchOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd';
import { useKnowledgeStore } from '../stores/knowledgeStore';
import { knowledgeApi } from '../api/knowledge';
import type { KnowledgeDocument, DocumentChunk } from '../types/knowledge';

const { Text, Title } = Typography;

const statusColors: Record<string, string> = {
  ready: 'success',
  processing: 'processing',
  pending: 'default',
  failed: 'error',
};

const statusText: Record<string, string> = {
  ready: '已完成',
  processing: '处理中',
  pending: '等待中',
  failed: '失败',
};

const KnowledgeBasePage: React.FC = () => {
  const { documents, loading, loadDocuments, deleteDocument } = useKnowledgeStore();
  const [uploading, setUploading] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [chunksVisible, setChunksVisible] = useState(false);
  const [currentDoc, setCurrentDoc] = useState<KnowledgeDocument | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<unknown[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => { loadDocuments(); }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await useKnowledgeStore.getState().uploadDocument(file);
      message.success('上传成功');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '上传失败';
      message.error(msg);
    } finally {
      setUploading(false);
    }
    return false; // prevent default upload
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteDocument(id);
      message.success('已删除');
    } catch {
      message.error('删除失败');
    }
  };

  const handleReprocess = async (id: number) => {
    try {
      await knowledgeApi.reprocessDocument(id);
      message.success('重新处理完成');
      loadDocuments();
    } catch {
      message.error('处理失败');
    }
  };

  const handleViewDetail = async (doc: KnowledgeDocument) => {
    setCurrentDoc(doc);
    setDetailVisible(true);
  };

  const handleViewChunks = async (doc: KnowledgeDocument) => {
    try {
      const res = await knowledgeApi.getChunks(doc.id);
      setChunks(res.data.items || []);
      setChunksVisible(true);
    } catch {
      message.error('加载分块失败');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await knowledgeApi.searchTest(searchQuery, 10);
      setSearchResults(res.data.results || []);
    } catch {
      message.error('搜索失败');
    } finally {
      setSearching(false);
    }
  };

  const fileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const columns = [
    { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true },
    { title: '类型', dataIndex: 'file_type', key: 'file_type', width: 80 },
    { title: '大小', dataIndex: 'file_size', key: 'file_size', width: 100, render: fileSize },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (s: string) => <Tag color={statusColors[s]}>{statusText[s]}</Tag>,
    },
    { title: '分块数', dataIndex: 'chunk_count', key: 'chunk_count', width: 80 },
    { title: '上传时间', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (v: string) => v ? new Date(v).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'actions', width: 240,
      render: (_: unknown, record: KnowledgeDocument) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>详情</Button>
          <Button size="small" onClick={() => handleViewChunks(record)}>分块</Button>
          <Button size="small" icon={<ReloadOutlined />} onClick={() => handleReprocess(record.id)}>重处理</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const chunkColumns = [
    { title: '#', dataIndex: 'chunk_index', key: 'chunk_index', width: 60 },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: 'Token数', dataIndex: 'token_count', key: 'token_count', width: 80 },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Upload area */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={4} style={{ margin: 0 }}>知识库文档管理</Title>
            <Upload
              beforeUpload={handleUpload}
              showUploadList={false}
              accept=".pdf,.csv,.md,.txt,.xlsx,.xls,.docx,.json"
            >
              <Button type="primary" icon={<UploadOutlined />} loading={uploading}>
                上传文档
              </Button>
            </Upload>
          </div>

          {/* Search test */}
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="测试检索效果，输入关键词..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onPressEnter={handleSearch}
              prefix={<SearchOutlined />}
            />
            <Button type="primary" onClick={handleSearch} loading={searching}>检索测试</Button>
          </Space.Compact>

          {searchResults.length > 0 && (
            <Card size="small" title="检索结果" extra={<Button size="small" onClick={() => setSearchResults([])}>清除</Button>}>
              {searchResults.map((r: unknown, i) => (
                <div key={i} style={{ marginBottom: 8, padding: 8, background: '#f6f8fa', borderRadius: 4 }}>
                  <Space>
                    <Tag color="blue">{(r as { score: number }).score.toFixed(4)}</Tag>
                    <Text strong>{(r as { document_name: string }).document_name}</Text>
                  </Space>
                  <Paragraph ellipsis={{ rows: 2 }} style={{ margin: '4px 0 0' }}>
                    {(r as { content: string }).content}
                  </Paragraph>
                </div>
              ))}
            </Card>
          )}

          {/* Document table */}
          <Table
            dataSource={documents}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 个文档` }}
            locale={{ emptyText: '暂无文档，点击上方按钮上传' }}
          />
        </Space>
      </Card>

      {/* Detail drawer */}
      <Drawer
        title="文档详情"
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
        width={500}
      >
        {currentDoc && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="文件名">{currentDoc.filename}</Descriptions.Item>
            <Descriptions.Item label="类型">{currentDoc.file_type}</Descriptions.Item>
            <Descriptions.Item label="大小">{fileSize(currentDoc.file_size)}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusColors[currentDoc.status]}>{statusText[currentDoc.status]}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="分块数">{currentDoc.chunk_count}</Descriptions.Item>
            <Descriptions.Item label="上传时间">
              {currentDoc.created_at ? new Date(currentDoc.created_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="错误信息">{currentDoc.error_message || '无'}</Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>

      {/* Chunks drawer */}
      <Drawer
        title="文档分块"
        open={chunksVisible}
        onClose={() => setChunksVisible(false)}
        width={600}
      >
        {currentDoc && (
          <>
            <Text strong>{currentDoc.filename}</Text>
            <Text style={{ marginLeft: 8 }}>- 共 {chunks.length} 个分块</Text>
            <Table
              dataSource={chunks}
              columns={chunkColumns}
              rowKey="id"
              size="small"
              style={{ marginTop: 16 }}
              pagination={{ pageSize: 20 }}
              expandable={{
                expandedRowRender: (record) => (
                  <Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{record.content}</Paragraph>
                ),
              }}
            />
          </>
        )}
      </Drawer>
    </div>
  );
};

export default KnowledgeBasePage;