"""Report template models for reusable reporting configurations"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class ReportTemplate(Base):
    """Report template model for reusable report configurations"""
    __tablename__ = "report_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filters_json = Column(JSONB, nullable=False, default={})
    columns_config = Column(JSONB, nullable=False, default={})
    is_public = Column(Boolean, nullable=False, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="report_templates")

    __table_args__ = (
        Index("idx_report_templates_created_by", "created_by"),
        Index("idx_report_templates_is_public", "is_public"),
    )

    def __repr__(self) -> str:
        return f"<ReportTemplate(id={self.id}, name={self.report_name})>"

    @property
    def filter_summary(self) -> str:
        """Get a summary of applied filters"""
        if not self.filters_json:
            return "No filters applied"
        
        filters = []
        for key, value in self.filters_json.items():
            if isinstance(value, dict) and 'operator' in value:
                filters.append(f"{key} {value['operator']} {value.get('value', '')}")
            else:
                filters.append(f"{key}: {value}")
        
        return "; ".join(filters) if filters else "No filters applied"

    def can_access(self, user_id: UUID) -> bool:
        """Check if user can access this report template"""
        return self.is_public or self.created_by == user_id