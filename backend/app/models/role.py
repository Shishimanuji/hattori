"""Role database model for RBAC"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Role(Base):
    """Role model for predefined user roles"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, role_name={self.role_name})>"

    @classmethod
    def get_role_hierarchy(cls):
        """Define role hierarchy for permission checking"""
        return {
            "Super Admin": 6,
            "Admin": 5,
            "Project Manager": 4,
            "Engineer": 3,
            "Auditor": 2,
            "Viewer": 1
        }

    def has_permission_level(self, required_level: int) -> bool:
        """Check if role has required permission level"""
        hierarchy = self.get_role_hierarchy()
        current_level = hierarchy.get(self.role_name, 0)
        return current_level >= required_level