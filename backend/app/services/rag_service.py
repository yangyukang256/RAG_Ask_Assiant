"""RAG 核心服务：检索 + 增强 + 生成 + 引用"""
import json
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session
from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import (
    TextLoader, CSVLoader, PyPDFLoader, UnstructuredMarkdownLoader
)
from app.config import settings
from app.services.llm_service import llm_service
from app.services.chat_service import ChatService
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.core.cache import cache, cached

# RAG System Prompt
SYSTEM_PROMPT = """你是一个专业的电商平台客服助手。请基于以下知识库内容回答用户问题。

## 回答要求
1. 仅基于提供的知识库内容回答，不要编造信息
2. 如果知识库内容不足以回答问题，明确告知用户
3. 用简洁清晰的语言回答
4. 在回答中标注引用来源，使用 [1]、[2] 等标记
5. 引用必须精确对应到知识库片段

## 知识库内容
{context}

## 对话历史
{history}

## 用户问题
{question}

请用中文回答。"""


class RAGService:
    """RAG 问答核心服务"""

    def __init__(self):
        self._vector_store = None

    @property
    def vector_store(self) -> Chroma:
        """获取 ChromaDB 向量存储实例（懒加载）"""
        if self._vector_store is None:
            self._vector_store = Chroma(
                collection_name="kb_docs",
                embedding_function=llm_service.get_embeddings(),
                persist_directory=settings.CHROMA_PERSIST_DIR,
            )
        return self._vector_store

    def get_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """获取文本分割器（中文优化）"""
        return RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=128,
            separators=["\n\n", "\n", "。", ".", "！", "？", "；", "，", " ", ""],
            length_function=len,
        )

    def load_document(self, file_path: str, file_type: str) -> list[LCDocument]:
        """根据文件类型加载文档"""
        if file_type == "txt":
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_type == "csv":
            loader = CSVLoader(file_path)
        elif file_type == "pdf":
            loader = PyPDFLoader(file_path)
        elif file_type in ("md", "markdown"):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            # 默认用文本加载
            loader = TextLoader(file_path, encoding="utf-8")

        return loader.load()

    def process_document(self, db: Session, doc_id: int):
        """处理文档：加载 → 分块 → 嵌入 → 存储"""
        from app.config import settings as cfg
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise ValueError(f"文档 {doc_id} 不存在")

        try:
            # 更新状态为处理中
            doc.status = "processing"
            db.commit()

            # 1. 加载文档
            documents = self.load_document(doc.file_path, doc.file_type)

            # 2. 文本分割
            splitter = self.get_text_splitter()
            chunks = splitter.split_documents(documents)

            # 3. 为每个 chunk 添加元数据
            total_tokens = 0
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "doc_id": doc_id,
                    "filename": doc.filename,
                    "chunk_index": i,
                })
                total_tokens += len(chunk.page_content)

            # 4. 生成向量并存入 ChromaDB
            if chunks:
                texts = [c.page_content for c in chunks]
                metadatas = [c.metadata for c in chunks]

                # 批量嵌入并存储
                chunk_ids = self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                )

                # 5. 存入数据库（元数据）
                for i, (chunk_text, cid) in enumerate(zip(texts, chunk_ids)):
                    db_chunk = DocumentChunk(
                        document_id=doc_id,
                        chunk_index=i,
                        content=chunk_text,
                        token_count=len(chunk_text),
                        embedding_id=cid,
                        metadata=json.dumps(metadatas[i], ensure_ascii=False),
                    )
                    db.add(db_chunk)

                # 6. 持久化 ChromaDB
                self.vector_store.persist()

            # 7. 更新文档状态
            doc.status = "ready"
            doc.chunk_count = len(chunks)
            db.commit()

        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            raise

    def delete_document_vectors(self, doc_id: int):
        """从向量库删除文档的所有向量"""
        try:
            # ChromaDB 按 metadata 过滤删除
            self.vector_store.delete(filter={"doc_id": str(doc_id)})
            self.vector_store.persist()
        except Exception as e:
            print(f"删除向量时出错: {e}")

    async def generate_answer(
        self, db: Session, session_id: int, question: str, user_id: int
    ) -> AsyncGenerator[dict, None]:
        """生成 RAG 回答（流式）"""
        # 1. 获取会话历史（最近 10 轮）
        history_data = ChatService.get_messages(db, session_id, user_id, page=1, page_size=10)
        history_messages = history_data["messages"]

        # 2. 构建历史文本
        history_text = ""
        for msg in history_messages[-6:]:  # 最近 3 轮对话
            role = "用户" if msg["role"] == "user" else "助手"
            history_text += f"{role}: {msg['content']}\n"

        # 3. 混合检索
        chunks = self._hybrid_retrieve(question, top_k=5)

        # 4. 构建上下文
        context_parts = []
        for i, chunk in enumerate(chunks):
            doc_name = chunk.metadata.get("filename", "未知文档")
            context_parts.append(f"[{i + 1}] 来源: {doc_name}\n{chunk.page_content}")
        context = "\n\n".join(context_parts)

        # 5. 构建 Prompt
        prompt_text = SYSTEM_PROMPT.format(
            context=context,
            history=history_text or "无历史对话",
            question=question,
        )

        # 6. 流式生成
        response_text = ""
        try:
            async for token in llm_service.stream_generate([
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": question},
            ]):
                response_text += token
                yield {"type": "text", "content": token}

            # 7. 生成完毕，返回引用信息
            citations_list = []
            for i, chunk in enumerate(chunks):
                citations_list.append({
                    "chunk_id": chunk.metadata.get("chunk_index", i),
                    "content": chunk.page_content[:300] + "..." if len(chunk.page_content) > 300 else chunk.page_content,
                    "document_name": chunk.metadata.get("filename", "未知文档"),
                    "score": float(chunk.metadata.get("score", 0)),
                })

            yield {
                "type": "end",
                "citations": citations_list,
                "token_count": len(response_text),
            }

            # 8. 保存到数据库
            ChatService.save_message(
                db, session_id, "user", question, None, len(question)
            )
            ChatService.save_message(
                db, session_id, "assistant", response_text,
                json.dumps(citations_list, ensure_ascii=False),
                len(response_text),
            )

        except Exception as e:
            yield {"type": "error", "content": f"生成回答时出错: {str(e)}"}

    def _hybrid_retrieve(self, query: str, top_k: int = 5) -> list[LCDocument]:
        """混合检索：向量检索 + 关键词检索 + RRF 融合"""
        # 1. 向量检索（取 2 倍数量用于融合）
        try:
            vector_docs = self.vector_store.similarity_search_with_score(
                query, k=top_k * 2
            )
        except Exception as e:
            print(f"向量检索出错: {e}")
            vector_docs = []

        # 2. 为向量结果添加 score 并转换为 Document
        vector_results = []
        for i, (doc, score) in enumerate(vector_docs):
            doc.metadata["score"] = float(score)
            doc.metadata["_retriever"] = "vector"
            vector_results.append(doc)

        # 3. RRF 融合（目前仅向量检索，后续可加 BM25）
        # 如果只有向量检索结果，直接按 score 排序返回
        vector_results.sort(key=lambda d: d.metadata.get("score", 0), reverse=True)

        return vector_results[:top_k]

    @cached(ttl_seconds=60)
    def search_test(self, query: str, top_k: int = 5) -> list[dict]:
        """测试检索效果（供管理员调试用）"""
        docs = self._hybrid_retrieve(query, top_k=top_k)
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content[:300],
                "document_name": doc.metadata.get("filename", "未知"),
                "score": doc.metadata.get("score", 0),
                "metadata": doc.metadata,
            })
        return results


# 全局单例
rag_service = RAGService()