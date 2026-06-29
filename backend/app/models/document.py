"""Document management models"""
from sqlalchemy import Column, String, Text, BigInteger, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    INVOICE = "Invoice"
    WARRANTY = "Warranty"
    CONFIGURATION = "Configuration"
    DRAWING = "Drawing"
    MANUAL = "Manual"
    CERTIFICATE = "Certificate"
    OTHER = "Other"


class Document(Base):
    """Document model for file attachments"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    document_type = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="documents")
    asset = relationship("Asset", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")

    __table_args__ = (
        Index("idx_documents_project_id", "project_id"),
        Index("idx_documents_asset_id", "asset_id"),
        Index("idx_documents_type", "document_type"),
        Index("idx_documents_uploaded_by", "uploaded_by"),
        CheckConstraint("document_type IN ('Invoice', 'Warranty', 'Configuration', 'Drawing', 'Manual', 'Certificate', 'Other')", 
                       name="ck_documents_document_type"),
        CheckConstraint("(project_id IS NOT NULL) OR (asset_id IS NOT NULL)", 
                       name="ck_documents_has_parent"),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.file_name}, type={self.document_type})>"

    @property
    def file_size_formatted(self) -> str:
        """Get formatted file size"""
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def is_image(self) -> bool:
        """Check if document is an image"""
        image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
        return self.mime_type in image_types if self.mime_type else False

    @property
    def is_pdf(self) -> bool:
        """Check if document is a PDF"""
        return self.mime_type == 'application/pdf' if self.mime_type else False