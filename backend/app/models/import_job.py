"""Import job tracking model for Excel import operations"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ImportStatus(str, enum.Enum):
    """Import status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportHistory(Base):
    """Import history model for tracking Excel import operations and progress"""
    __tablename__ = "import_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    filename = Column(String(255), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Job status tracking
    status = Column(String(50), nullable=False, default=ImportStatus.PENDING)
    progress_percent = Column(Integer, nullable=False, default=0)
    
    # Row statistics
    total_records = Column(Integer, nullable=False, default=0)
    successful_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    
    # Legacy fields (for backward compatibility)
    rows_total = Column(Integer, nullable=False, default=0)
    rows_processed = Column(Integer, nullable=False, default=0)
    rows_successful = Column(Integer, nullable=False, default=0)
    rows_failed = Column(Integer, nullable=False, default=0)
    
    # Errors tracking
    errors = Column(JSONB, nullable=False, default=[])  # List of error objects
    
    # Legacy field mapping
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=True)
    file_name = Column(String(255), nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Legacy timestamp
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="import_history")
    template = relationship("Template", back_populates="import_history")
    uploader = relationship("User", foreign_keys=[uploaded_by], back_populates="import_history")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Legacy relationships
    asset_type = relationship("AssetType")

    __table_args__ = (
        Index("idx_import_history_project_id", "project_id"),
        Index("idx_import_history_template_id", "template_id"),
        Index("idx_import_history_uploaded_by", "uploaded_by"),
        Index("idx_import_history_status", "status"),
        Index("idx_import_history_uploaded_at", "uploaded_at"),
        # Legacy indexes
        Index("idx_import_jobs_asset_type_id", "asset_type_id"),
        Index("idx_import_jobs_created_by", "created_by"),
        Index("idx_import_jobs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ImportHistory(id={self.id}, status={self.status}, progress={self.progress_percent}%)>"

    @property
    def rows_skipped(self) -> int:
        """Calculate number of skipped rows (legacy compatibility)"""
        return self.rows_processed - self.rows_successful - self.rows_failed

    @property
    def skipped_records(self) -> int:
        """Calculate number of skipped records"""
        return max(0, self.total_records - self.successful_records - self.failed_records)

    def add_error(self, row_number: int, field_name: str, error_message: str) -> None:
        """Add error to the errors list"""
        if self.errors is None:
            self.errors = []
        
        error_obj = {
            "row_number": row_number,
            "field_name": field_name,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.errors.append(error_obj)

    def update_progress(self, total: int, successful: int, failed: int) -> None:
        """Update progress statistics"""
        self.total_records = total
        self.successful_records = successful
        self.failed_records = failed
        
        # Update legacy fields for compatibility
        self.rows_total = total
        self.rows_successful = successful
        self.rows_failed = failed
        self.rows_processed = successful + failed
        
        # Calculate progress percentage
        if self.total_records > 0:
            processed = successful + failed
            self.progress_percent = int((processed / self.total_records) * 100)
        else:
            self.progress_percent = 0
        
        self.updated_at = datetime.utcnow()

    def mark_completed(self):
        """Mark import as completed"""
        self.status = ImportStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100

    def mark_failed(self, error_message: str = None):
        """Mark import as failed"""
        self.status = ImportStatus.FAILED
        self.completed_at = datetime.utcnow()
        if error_message:
            self.add_error(0, "general", error_message)
