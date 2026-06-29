"""Database models for PRMS"""
# New models
from app.models.role import Role
from app.models.user import User, UserStatus
from app.models.template import Template, TemplateResourceType, SheetMapping
from app.models.resource_type import ResourceType, ResourceField, FieldType
from app.models.project import Project, ProjectSummary
from app.models.asset import Asset, AssetFieldValue, AssetStatus, AuditStatus
from app.models.document import Document, DocumentType
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.models.import_job import ImportHistory, ImportStatus
from app.models.report_template import ReportTemplate
from app.models.session import Session as SessionModel
from app.models.audit_log import AuditLog, AuditOperation, AuditLogStatus
from app.models.password_reset_token import PasswordResetToken

# Legacy models (kept for backward compatibility)
from app.models.asset_type import AssetType, CustomField
from app.models.resource import Resource, ResourceStatus, Allocation

__all__ = [
    # New models
    "Role",
    "User",
    "UserStatus",
    "Template",
    "TemplateResourceType",
    "SheetMapping",
    "ResourceType",
    "ResourceField",
    "FieldType",
    "Project",
    "ProjectSummary",
    "Asset",
    "AssetFieldValue",
    "AssetStatus",
    "AuditStatus",
    "Document",
    "DocumentType",
    "Alert",
    "AlertType",
    "AlertSeverity",
    "AlertStatus",
    "ImportHistory",
    "ImportStatus",
    "ReportTemplate",
    "SessionModel",
    "AuditLog",
    "AuditOperation",
    "AuditLogStatus",
    "PasswordResetToken",
    # Legacy models (deprecated)
    "AssetType",
    "CustomField",
    "Resource",
    "ResourceStatus",
    "Allocation",
]
