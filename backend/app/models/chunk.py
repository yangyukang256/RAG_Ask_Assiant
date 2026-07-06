from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    embedding_id = Column(String(100), nullable=True)  # ChromaDB 中对应 ID
    metadata_json = Column("metadata", Text, default="{}")  # JSON 格式
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "content_full": self.content,
            "token_count": self.token_count,
            "embedding_id": self.embedding_id,
            "metadata": json.loads(self.metadata_json) if self.metadata_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }