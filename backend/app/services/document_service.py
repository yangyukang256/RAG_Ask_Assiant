import os
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.config import settings
from app.core.exceptions import not_found, bad_request


ALLOWED_EXTENSIONS = {".pdf", ".csv", ".md", ".txt", ".xlsx", ".xls", ".docx", ".json"}


class DocumentService:
    """文档管理服务"""

    @staticmethod
    def list_documents(db: Session, page: int = 1, page_size: int = 20, status: Optional[str] = None):
        """获取文档列表"""
        query = db.query(Document).order_by(desc(Document.created_at))
        if status:
            query = query.filter(Document.status == status)

        total = query.count()
        docs = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [d.to_dict() for d in docs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def get_document(db: Session, doc_id: int) -> Document:
        """获取文档详情"""
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise not_found("文档不存在")
        return doc

    @staticmethod
    def get_document_with_chunks(db: Session, doc_id: int) -> tuple[Document, list]:
        """获取文档及所有分块"""
        doc = DocumentService.get_document(db, doc_id)
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_id
        ).order_by(DocumentChunk.chunk_index).all()
        return doc, chunks

    @staticmethod
    def validate_file(filename: str, file_size: int) -> str:
        """验证文件"""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise bad_request(f"不支持的文件类型: {ext}，允许的类型: {', '.join(ALLOWED_EXTENSIONS)}")
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise bad_request(f"文件过大，最大允许 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB")
        return ext

    @staticmethod
    def save_uploaded_file(file_data: bytes, filename: str) -> str:
        """保存上传文件到磁盘"""
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_data)

        return file_path

    @staticmethod
    def create_document_record(
        db: Session, filename: str, file_type: str, file_size: int,
        file_path: str, uploaded_by: int
    ) -> Document:
        """创建文档记录"""
        doc = Document(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            status="pending",
            uploaded_by=uploaded_by,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def update_status(db: Session, doc_id: int, status: str, error_message: Optional[str] = None):
        """更新文档状态"""
        doc = DocumentService.get_document(db, doc_id)
        doc.status = status
        if error_message:
            doc.error_message = error_message
        db.commit()

    @staticmethod
    def delete_document(db: Session, doc_id: int):
        """删除文档及其所有 chunk"""
        doc = DocumentService.get_document(db, doc_id)
        # 删除物理文件
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass
        db.delete(doc)
        db.commit()

    @staticmethod
    def get_chunks_by_document(db: Session, doc_id: int, page: int = 1, page_size: int = 50):
        """分页获取文档分块"""
        query = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_id
        ).order_by(DocumentChunk.chunk_index)

        total = query.count()
        chunks = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [c.to_dict() for c in chunks],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }