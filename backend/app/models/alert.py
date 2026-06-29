"""Alert management models"""
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class AlertType(str, enum.Enum):
    """Alert type enumeration"""
    WARRANTY_EXPIRY = "Warranty Expiry"
    AUDIT_DUE = "Audit Due"
    MAINTENANCE_DUE = "Maintenance Due"
    COMPLIANCE = "Compliance"
    BUDGET = "Budget"
    OTHER = "Other"


class AlertSeverity(str, enum.Enum):
    """Alert severity enumeration"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration"""
    ACTIVE = "Active"
    ACKNOWLEDGED = "Acknowledged"
    RESOLVED = "Resolved"
    DISMISSED = "Dismissed"


class Alert(Base):
    """Alert model for dashboard notifications"""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default=AlertStatus.ACTIVE)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="alerts")
    asset = relationship("Asset", back_populates="alerts")
    resolver = relationship("User", back_populates="resolved_alerts")

    __table_args__ = (
        Index("idx_alerts_project_id", "project_id"),
        Index("idx_alerts_asset_id", "asset_id"),
        Index("idx_alerts_type", "alert_type"),
        Index("idx_alerts_severity", "severity"),
        Index("idx_alerts_status", "status"),
        Index("idx_alerts_due_date", "due_date"),
        CheckConstraint("alert_type IN ('Warranty Expiry', 'Audit Due', 'Maintenance Due', 'Compliance', 'Budget', 'Other')", 
                       name="ck_alerts_alert_type"),
        CheckConstraint("severity IN ('Low', 'Medium', 'High', 'Critical')", 
                       name="ck_alerts_severity"),
        CheckConstraint("status IN ('Active', 'Acknowledged', 'Resolved', 'Dismissed')", 
                       name="ck_alerts_status"),
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity})>"

    @property
    def is_overdue(self) -> bool:
        """Check if alert is overdue"""
        if not self.due_date:
            return False
        return datetime.now().date() > self.due_date

    @property
    def days_until_due(self) -> int:
        """Get days until due date"""
        if not self.due_date:
            return 0
        delta = self.due_date - datetime.now().date()
        return delta.days

    def resolve(self, user_id: UUID):
        """Mark alert as resolved"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id

    def acknowledge(self):
        """Mark alert as acknowledged"""
        if self.status == AlertStatus.ACTIVE:
            self.status = AlertStatus.ACKNOWLEDGED

    def dismiss(self):
        """Dismiss the alert"""
        self.status = AlertStatus.DISMISSED