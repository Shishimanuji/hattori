"""Import job tracking model for Excel import operations"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ImportJobStatus(str, enum.Enum):
    """Import job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJob(Base):
    """Import job model for tracking Excel import operations and progress"""
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Job status tracking
    status = Column(String(50), nullable=False, default=ImportJobStatus.PENDING)
    progress_percent = Column(Integer, nullable=False, default=0)
    
    # Row statistics
    rows_total = Column(Integer, nullable=False, default=0)
    rows_processed = Column(Integer, nullable=False, default=0)
    rows_successful = Column(Integer, nullable=False, default=0)
    rows_failed = Column(Integer, nullable=False, default=0)
    
    # Errors tracking
    errors = Column(JSONB, nullable=False, default=[])  # List of error objects
    
    # File information
    file_name = Column(String(255), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="import_jobs")
    asset_type = relationship("AssetType", back_populates="import_jobs")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_import_jobs_project_id", "project_id"),
        Index("idx_import_jobs_asset_type_id", "asset_type_id"),
        Index("idx_import_jobs_created_by", "created_by"),
        Index("idx_import_jobs_status", "status"),
        Index("idx_import_jobs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ImportJob(id={self.id}, status={self.status}, progress={self.progress_percent}%)>"

    @property
    def rows_skipped(self) -> int:
        """Calculate number of skipped rows"""
        return self.rows_processed - self.rows_successful - self.rows_failed

    def add_error(self, row_number: int, field_name: str, error_message: str) -> None:
        """Add error to the errors list"""
        if self.errors is None:
            self.errors = []
        
        error_obj = {
            "row_number": row_number,
            "field_name": field_name,
            "message": error_message
        }
        self.errors.append(error_obj)

    def update_progress(self, rows_processed: int, rows_successful: int, rows_failed: int) -> None:
        """Update progress statistics"""
        self.rows_processed = rows_processed
        self.rows_successful = rows_successful
        self.rows_failed = rows_failed
        
        # Calculate progress percentage
        if self.rows_total > 0:
            self.progress_percent = int((rows_processed / self.rows_total) * 100)
        else:
            self.progress_percent = 0
        
        self.updated_at = datetime.utcnow()
