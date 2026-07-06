from pydantic import BaseModel
from typing import Optional, List, Any


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int = 0
    uploaded_by: Optional[int] = None
    description: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    chunks: List["ChunkResponse"] = []


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: str = "文档上传成功，正在处理中"


class ChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    content_full: Optional[str] = None
    token_count: int = 0
    embedding_id: Optional[str] = None
    metadata: Any = {}
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    document_name: str
    content: str
    score: float
    metadata: Any = {}


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]