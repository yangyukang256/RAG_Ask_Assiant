import os
import json
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.document import (
    DocumentResponse, DocumentDetailResponse, DocumentUploadResponse,
    ChunkResponse, SearchRequest, SearchResponse, SearchResult,
)
from app.services.document_service import DocumentService
from app.services.rag_service import rag_service
from app.core.security import get_current_user
from app.core.permissions import require_admin
from app.models.user import User
from app.models.document import Document

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识库管理"])


@router.get("/documents", summary="获取文档列表（Admin）")
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return DocumentService.list_documents(db, page, page_size, status)


@router.post("/documents/upload", summary="上传文档（Admin）")
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # 验证文件
    file_data = await file.read()
    ext = DocumentService.validate_file(file.filename, len(file_data))

    # 保存文件
    file_path = DocumentService.save_uploaded_file(file_data, file.filename)

    # 创建记录
    doc = DocumentService.create_document_record(
        db, file.filename, ext.lstrip("."), len(file_data), file_path, admin.id
    )

    # 异步处理文档（使用 FastAPI 后台任务）
    from fastapi.concurrency import run_in_threadpool
    try:
        await run_in_threadpool(rag_service.process_document, db, doc.id)
    except Exception as e:
        return DocumentUploadResponse(
            id=doc.id,
            filename=doc.filename,
            status="failed",
            message=f"文档处理失败: {str(e)}",
        )

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        status="ready",
        message=f"文档处理完成，共 {doc.chunk_count} 个分块",
    )


@router.get("/documents/{doc_id}", summary="获取文档详情（Admin）")
def get_document(
    doc_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc, chunks = DocumentService.get_document_with_chunks(db, doc_id)
    result = doc.to_dict()
    result["chunks"] = [c.to_dict() for c in chunks]
    return result


@router.delete("/documents/{doc_id}", summary="删除文档（Admin）")
def delete_document(
    doc_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # 删除向量
    rag_service.delete_document_vectors(doc_id)
    # 删除数据库记录
    DocumentService.delete_document(db, doc_id)
    return {"message": "文档已删除"}


@router.get("/documents/{doc_id}/chunks", summary="查看文档分块（Admin）")
def get_chunks(
    doc_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return DocumentService.get_chunks_by_document(db, doc_id, page, page_size)


@router.post("/documents/{doc_id}/reprocess", summary="重新处理文档（Admin）")
async def reprocess_document(
    doc_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc = DocumentService.get_document(db, doc_id)
    # 删除旧向量
    rag_service.delete_document_vectors(doc_id)
    # 删除旧分块
    from app.models.chunk import DocumentChunk
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    doc.chunk_count = 0
    db.commit()

    from fastapi.concurrency import run_in_threadpool
    try:
        await run_in_threadpool(rag_service.process_document, db, doc_id)
        return {"message": "文档重新处理完成", "status": "ready", "chunk_count": doc.chunk_count}
    except Exception as e:
        return {"message": f"处理失败: {str(e)}", "status": "failed"}


@router.post("/search", summary="测试检索效果（Admin）")
def search_test(
    req: SearchRequest,
    admin: User = Depends(require_admin),
):
    results = rag_service.search_test(req.query, req.top_k)
    return SearchResponse(
        query=req.query,
        results=[SearchResult(**r) for r in results],
    )