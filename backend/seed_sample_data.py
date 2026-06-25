#!/usr/bin/env python
"""
Seed database with sample data for PRMS dashboard
This script populates the database with realistic sample projects, resources, and asset types.

Usage:
    python seed_sample_data.py
    python seed_sample_data.py --excel sample_data/sample_resources.xlsx
    python seed_sample_data.py --clean  # Clean all sample data first
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import sessionmaker, Session
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.resource import Resource, ResourceStatus, Allocation
from app.models.asset_type import AssetType, CustomField, FieldType
from app.core.database import Base
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
import json
import argparse
import pandas as pd

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv('DATABASE_URL', 'sqlite:///./prms.db')

# Create engine and session
engine = create_engine(database_url, echo=False)
Session = sessionmaker(bind=engine)


def create_asset_types(session: Session) -> dict:
    """Create asset types with custom fields"""
    print("\n📋 Creating asset types...")
    
    asset_types = {}
    
    # Asset Type 1: Equipment
    equipment = session.query(AssetType).filter_by(name="Equipment").first()
    if not equipment:
        equipment = AssetType(
            id=uuid4(),
            name="Equipment",
            description="Physical computing and networking equipment",
            is_active=True
        )
        session.add(equipment)
        
        # Custom fields for Equipment
        custom_fields = [
            CustomField(
                id=uuid4(),
                asset_type_id=equipment.id,
                name="Warranty Period (months)",
                field_type=FieldType.NUMBER,
                is_required=False,
                display_order=1
            ),
            CustomField(
                id=uuid4(),
                asset_type_id=equipment.id,
                name="Serial Number",
                field_type=FieldType.TEXT,
                is_required=False,
                display_order=2
            ),
            CustomField(
                id=uuid4(),
                asset_type_id=equipment.id,
                name="Maintenance Required",
                field_type=FieldType.BOOLEAN,
                is_required=False,
                display_order=3
            ),
        ]
        session.add_all(custom_fields)
    asset_types['Equipment'] = equipment
    
    # Asset Type 2: Software
    software = session.query(AssetType).filter_by(name="Software").first()
    if not software:
        software = AssetType(
            id=uuid4(),
            name="Software",
            description="Software licenses and subscriptions",
            is_active=True
        )
        session.add(software)
        
        # Custom fields for Software
        custom_fields = [
            CustomField(
                id=uuid4(),
                asset_type_id=software.id,
                name="License Type",
                field_type=FieldType.DROPDOWN,
                is_required=False,
                options=["Perpetual", "Annual", "Monthly", "Trial"],
                display_order=1
            ),
            CustomField(
                id=uuid4(),
                asset_type_id=software.id,
                name="License Count",
                field_type=FieldType.NUMBER,
                is_required=False,
                display_order=2
            ),
            CustomField(
                id=uuid4(),
                asset_type_id=software.id,
                name="Renewal Date",
                field_type=FieldType.DATE,
                is_required=False,
                display_order=3
            ),
        ]
        session.add_all(custom_fields)
    asset_types['Software'] = software
    
    # Asset Type 3: Personnel
    personnel = session.query(AssetType).filter_by(name="Personnel").first()
    if not personnel:
        personnel = AssetType(
            id=uuid4(),
            name="Personnel",
            description="Human resources and team members",
            is_active=True
        )
        session.add(personnel)
        
        # Custom fields for Personnel
        custom_fields = [
            CustomField(
                id=uuid4(),
                asset_type_id=personnel.id,
                name="Department",
                field_type=FieldType.DROPDOWN,
                is_required=False,
                options=["Engineering", "Operations", "Sales", "Marketing", "Finance", "HR"],
                display_order=1
            ),
            CustomField(
                id=uuid4(),
                asset_type_id=personnel.id,
                name="Experience Level (years)",
                field_type=FieldType.NUMBER,
                is_required=False,
                display_order=2
            ),
            CustomField(
                id=uuid4(),
                asset_type_id=personnel.id,
                name="Employment Type",
                field_type=FieldType.DROPDOWN,
                is_required=False,
                options=["Full-time", "Part-time", "Contract", "Consultant"],
                display_order=3
            ),
            CustomField(
                id=uuid4(),
                asset_type_id=personnel.id,
                name="Availability Start Date",
                field_type=FieldType.DATE,
                is_required=False,
                display_order=4
            ),
        ]
        session.add_all(custom_fields)
    asset_types['Personnel'] = personnel
    
    session.commit()
    print(f"   ✅ Created {len(asset_types)} asset types with custom fields")
    return asset_types


def create_system_user(session: Session) -> User:
    """Get or create system user for seeding"""
    system_user = session.query(User).filter_by(username="system_seeder").first()
    if not system_user:
        system_user = User(
            id=uuid4(),
            username="system_seeder",
            email="system@prms.local",
            password_hash="seeder_temp_hash",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(system_user)
        session.commit()
        print(f"   ✅ Created system user")
    return system_user


def create_projects(session: Session, system_user: User) -> dict:
    """Create sample projects with different statuses and budget allocations"""
    print("\n🎯 Creating sample projects...")
    
    projects = {}
    base_date = datetime.now()
    
    project_specs = [
        {
            "name": "Enterprise Infrastructure",
            "budget": Decimal("250000.00"),
            "allocated": Decimal("212500.00"),  # 85% - High alert
            "status": ProjectStatus.ACTIVE,
            "start_date": (base_date - timedelta(days=180)).date(),
            "description": "Upgrade core IT infrastructure with new servers and networking equipment"
        },
        {
            "name": "Cloud Migration",
            "budget": Decimal("300000.00"),
            "allocated": Decimal("300000.00"),  # 100% - Critical
            "status": ProjectStatus.ACTIVE,
            "start_date": (base_date - timedelta(days=120)).date(),
            "description": "Migrate on-premises systems to cloud infrastructure"
        },
        {
            "name": "Digital Transformation",
            "budget": Decimal("200000.00"),
            "allocated": Decimal("120000.00"),  # 60%
            "status": ProjectStatus.ACTIVE,
            "start_date": (base_date - timedelta(days=150)).date(),
            "description": "Implement modern applications and digital tools"
        },
        {
            "name": "Data Analytics Platform",
            "budget": Decimal("280000.00"),
            "allocated": Decimal("196000.00"),  # 70%
            "status": ProjectStatus.ACTIVE,
            "start_date": (base_date - timedelta(days=90)).date(),
            "description": "Build comprehensive data analytics and reporting platform"
        },
        {
            "name": "Cybersecurity Initiative",
            "budget": Decimal("200000.00"),
            "allocated": Decimal("200000.00"),  # 100%
            "status": ProjectStatus.COMPLETED,
            "start_date": (base_date - timedelta(days=300)).date(),
            "description": "Comprehensive security audit and implementation of security controls"
        },
        {
            "name": "AI & Machine Learning Initiative",
            "budget": Decimal("400000.00"),
            "allocated": Decimal("0.00"),  # 0% - Not started
            "status": ProjectStatus.PENDING,
            "start_date": (base_date + timedelta(days=30)).date(),
            "description": "Develop AI-powered solutions for business optimization"
        },
        {
            "name": "Mobile Application Dev",
            "budget": Decimal("150000.00"),
            "allocated": Decimal("0.00"),  # 0% - Not started
            "status": ProjectStatus.PENDING,
            "start_date": (base_date + timedelta(days=45)).date(),
            "description": "Create mobile apps for iOS and Android platforms"
        },
        {
            "name": "Legacy System Modernization",
            "budget": Decimal("350000.00"),
            "allocated": Decimal("87500.00"),  # 25% - On hold
            "status": ProjectStatus.ON_HOLD,
            "start_date": (base_date - timedelta(days=60)).date(),
            "description": "Refactor legacy monolithic applications to microservices"
        },
        {
            "name": "Business Automation",
            "budget": Decimal("180000.00"),
            "allocated": Decimal("90000.00"),  # 50%
            "status": ProjectStatus.ACTIVE,
            "start_date": (base_date - timedelta(days=75)).date(),
            "description": "Automate routine business processes and workflows"
        },
        {
            "name": "Customer Portal Redesign",
            "budget": Decimal("220000.00"),
            "allocated": Decimal("0.00"),  # 0% - Not started
            "status": ProjectStatus.PENDING,
            "start_date": (base_date + timedelta(days=60)).date(),
            "description": "Redesign customer-facing portal with modern UX/UI"
        },
    ]
    
    for spec in project_specs:
        project = session.query(Project).filter_by(name=spec["name"]).first()
        if not project:
            project = Project(
                id=uuid4(),
                name=spec["name"],
                description=spec["description"],
                status=spec["status"],
                budget=spec["budget"],
                allocated_budget=spec["allocated"],
                start_date=spec["start_date"],
                end_date=None,
                owner_id=system_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(project)
            session.flush()
        projects[spec["name"]] = project
    
    session.commit()
    print(f"   ✅ Created {len(projects)} projects")
    return projects


def create_resources(session: Session, projects: dict, asset_types: dict, system_user: User) -> None:
    """Create sample resources and allocate them to projects"""
    print("\n📦 Creating sample resources...")
    
    base_date = datetime.now()
    resource_count = 0
    
    # Resources for Enterprise Infrastructure (85% budget utilization)
    enterprise_resources = [
        ("Dell Server DS-2024-01", Decimal("45000.00"), asset_types["Equipment"], {"Warranty Period (months)": 36, "Serial Number": "DELL-001", "Maintenance Required": False}),
        ("Cisco Network Switch CS-8K", Decimal("35000.00"), asset_types["Equipment"], {"Warranty Period (months)": 24, "Serial Number": "CISCO-001", "Maintenance Required": False}),
        ("UPS Backup System UPS-500KVA", Decimal("28000.00"), asset_types["Equipment"], {"Warranty Period (months)": 24, "Serial Number": "UPS-001", "Maintenance Required": True}),
        ("Server Rack Mount SR-42U", Decimal("12000.00"), asset_types["Equipment"], {"Warranty Period (months)": 12, "Serial Number": "RACK-001", "Maintenance Required": False}),
        ("Network Cables & Fiber", Decimal("8500.00"), asset_types["Equipment"], {"Warranty Period (months)": 0, "Serial Number": "NET-CABLES-001", "Maintenance Required": False}),
        ("Workstations for Dev Team", Decimal("32000.00"), asset_types["Equipment"], {"Warranty Period (months)": 36, "Serial Number": "WS-001", "Maintenance Required": False}),
        ("DevOps Engineer - Mike Chen", Decimal("140000.00"), asset_types["Personnel"], {"Department": "Engineering", "Experience Level (years)": 8, "Employment Type": "Full-time"}),
    ]
    
    project = projects["Enterprise Infrastructure"]
    for name, cost, asset_type, custom_values in enterprise_resources:
        resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name=name,
            cost=cost,
            allocation_date=base_date.date(),
            status=ResourceStatus.ACTIVE,
            custom_field_values=custom_values,
            created_by=system_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(resource)
        session.flush()
        
        # Create allocation record
        allocation = Allocation(
            id=uuid4(),
            resource_id=resource.id,
            project_id=project.id,
            cost_at_allocation=cost,
            allocated_at=datetime.utcnow(),
            deallocated_at=None,
            created_by=system_user.id
        )
        session.add(allocation)
        resource_count += 1
    
    # Resources for Cloud Migration (100% budget utilization)
    cloud_resources = [
        ("Senior Architect - John Smith", Decimal("180000.00"), asset_types["Personnel"], {"Department": "Engineering", "Experience Level (years)": 12, "Employment Type": "Full-time"}),
        ("Microsoft Office 365 Licenses", Decimal("15000.00"), asset_types["Software"], {"License Type": "Annual", "License Count": 250, "Renewal Date": (base_date + timedelta(days=180)).date()}),
        ("Cloud Infrastructure Credits", Decimal("75000.00"), asset_types["Software"], {"License Type": "Annual", "License Count": 1, "Renewal Date": (base_date + timedelta(days=90)).date()}),
        ("Project Manager - Sarah Wilson", Decimal("30000.00"), asset_types["Personnel"], {"Department": "Operations", "Experience Level (years)": 10, "Employment Type": "Contract"}),
    ]
    
    project = projects["Cloud Migration"]
    for name, cost, asset_type, custom_values in cloud_resources:
        resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name=name,
            cost=cost,
            allocation_date=base_date.date(),
            status=ResourceStatus.ACTIVE,
            custom_field_values=custom_values,
            created_by=system_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(resource)
        session.flush()
        
        allocation = Allocation(
            id=uuid4(),
            resource_id=resource.id,
            project_id=project.id,
            cost_at_allocation=cost,
            allocated_at=datetime.utcnow(),
            deallocated_at=None,
            created_by=system_user.id
        )
        session.add(allocation)
        resource_count += 1
    
    # Resources for Digital Transformation (60% budget utilization)
    digital_resources = [
        ("Adobe Creative Suite Annual", Decimal("22000.00"), asset_types["Software"], {"License Type": "Annual", "License Count": 50, "Renewal Date": (base_date + timedelta(days=180)).date()}),
        ("Frontend Developer - Lisa Anderson", Decimal("110000.00"), asset_types["Personnel"], {"Department": "Engineering", "Experience Level (years)": 6, "Employment Type": "Full-time"}),
    ]
    
    project = projects["Digital Transformation"]
    for name, cost, asset_type, custom_values in digital_resources:
        resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name=name,
            cost=cost,
            allocation_date=base_date.date(),
            status=ResourceStatus.ACTIVE,
            custom_field_values=custom_values,
            created_by=system_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(resource)
        session.flush()
        
        allocation = Allocation(
            id=uuid4(),
            resource_id=resource.id,
            project_id=project.id,
            cost_at_allocation=cost,
            allocated_at=datetime.utcnow(),
            deallocated_at=None,
            created_by=system_user.id
        )
        session.add(allocation)
        resource_count += 1
    
    # Resources for Data Analytics Platform (70% budget utilization)
    analytics_resources = [
        ("Database Enterprise Edition", Decimal("50000.00"), asset_types["Software"], {"License Type": "Annual", "License Count": 1, "Renewal Date": (base_date + timedelta(days=120)).date()}),
        ("Backup Storage Array", Decimal("55000.00"), asset_types["Equipment"], {"Warranty Period (months)": 36, "Serial Number": "STORAGE-001", "Maintenance Required": False}),
        ("Data Scientist - Emily Rodriguez", Decimal("150000.00"), asset_types["Personnel"], {"Department": "Engineering", "Experience Level (years)": 7, "Employment Type": "Full-time"}),
        ("Backend Developer - James Brown", Decimal("41000.00"), asset_types["Personnel"], {"Department": "Engineering", "Experience Level (years)": 5, "Employment Type": "Full-time"}),
    ]
    
    project = projects["Data Analytics Platform"]
    for name, cost, asset_type, custom_values in analytics_resources:
        resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name=name,
            cost=cost,
            allocation_date=base_date.date(),
            status=ResourceStatus.ACTIVE,
            custom_field_values=custom_values,
            created_by=system_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(resource)
        session.flush()
        
        allocation = Allocation(
            id=uuid4(),
            resource_id=resource.id,
            project_id=project.id,
            cost_at_allocation=cost,
            allocated_at=datetime.utcnow(),
            deallocated_at=None,
            created_by=system_user.id
        )
        session.add(allocation)
        resource_count += 1
    
    # Resources for Cybersecurity Initiative (100% budget utilization - completed)
    security_resources = [
        ("Security & Monitoring Tools", Decimal("35000.00"), asset_types["Software"], {"License Type": "Annual", "License Count": 10, "Renewal Date": (base_date + timedelta(days=150)).date()}),
        ("Security Lead - David Kumar", Decimal("165000.00"), asset_types["Personnel"], {"Department": "Engineering", "Experience Level (years)": 15, "Employment Type": "Full-time"}),
    ]
    
    project = projects["Cybersecurity Initiative"]
    for name, cost, asset_type, custom_values in security_resources:
        resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name=name,
            cost=cost,
            allocation_date=(base_date - timedelta(days=300)).date(),
            status=ResourceStatus.ACTIVE,
            custom_field_values=custom_values,
            created_by=system_user.id,
            created_at=datetime.utcnow() - timedelta(days=300),
            updated_at=datetime.utcnow() - timedelta(days=300)
        )
        session.add(resource)
        session.flush()
        
        allocation = Allocation(
            id=uuid4(),
            resource_id=resource.id,
            project_id=project.id,
            cost_at_allocation=cost,
            allocated_at=datetime.utcnow() - timedelta(days=300),
            deallocated_at=None,
            created_by=system_user.id
        )
        session.add(allocation)
        resource_count += 1
    
    # Resources for Business Automation (50% budget utilization)
    automation_resources = [
        ("Business Process RPA Tools", Decimal("45000.00"), asset_types["Software"], {"License Type": "Annual", "License Count": 5, "Renewal Date": (base_date + timedelta(days=200)).date()}),
        ("Process Automation Consultant", Decimal("45000.00"), asset_types["Personnel"], {"Department": "Operations", "Experience Level (years)": 8, "Employment Type": "Contract"}),
    ]
    
    project = projects["Business Automation"]
    for name, cost, asset_type, custom_values in automation_resources:
        resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name=name,
            cost=cost,
            allocation_date=base_date.date(),
            status=ResourceStatus.ACTIVE,
            custom_field_values=custom_values,
            created_by=system_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(resource)
        session.flush()
        
        allocation = Allocation(
            id=uuid4(),
            resource_id=resource.id,
            project_id=project.id,
            cost_at_allocation=cost,
            allocated_at=datetime.utcnow(),
            deallocated_at=None,
            created_by=system_user.id
        )
        session.add(allocation)
        resource_count += 1
    
    # Resources for Legacy System Modernization (25% budget utilization - on hold)
    legacy_resources = [
        ("Modernization Framework License", Decimal("50000.00"), asset_types["Software"], {"License Type": "Annual", "License Count": 1, "Renewal Date": (base_date + timedelta(days=180)).date()}),
        ("Architecture Consultant", Decimal("37500.00"), asset_types["Personnel"], {"Department": "Engineering", "Experience Level (years)": 20, "Employment Type": "Contract"}),
    ]
    
    project = projects["Legacy System Modernization"]
    for name, cost, asset_type, custom_values in legacy_resources:
        resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name=name,
            cost=cost,
            allocation_date=(base_date - timedelta(days=60)).date(),
            status=ResourceStatus.ACTIVE,
            custom_field_values=custom_values,
            created_by=system_user.id,
            created_at=datetime.utcnow() - timedelta(days=60),
            updated_at=datetime.utcnow() - timedelta(days=60)
        )
        session.add(resource)
        session.flush()
        
        allocation = Allocation(
            id=uuid4(),
            resource_id=resource.id,
            project_id=project.id,
            cost_at_allocation=cost,
            allocated_at=datetime.utcnow() - timedelta(days=60),
            deallocated_at=None,
            created_by=system_user.id
        )
        session.add(allocation)
        resource_count += 1
    
    session.commit()
    print(f"   ✅ Created {resource_count} resources with allocations")


def clean_sample_data(session: Session) -> None:
    """Remove all sample data (optional)"""
    print("\n🧹 Cleaning sample data...")
    
    try:
        # Delete allocations first (foreign key constraint)
        session.query(Allocation).delete()
        
        # Delete resources
        session.query(Resource).delete()
        
        # Delete projects
        session.query(Project).delete()
        
        # Delete custom fields
        session.query(CustomField).delete()
        
        # Delete asset types
        session.query(AssetType).delete()
        
        session.commit()
        print("   ✅ Sample data cleaned")
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error cleaning data: {e}")


def main():
    parser = argparse.ArgumentParser(description="Seed PRMS database with sample data")
    parser.add_argument("--clean", action="store_true", help="Clean sample data before seeding")
    parser.add_argument("--excel", type=str, help="Path to Excel file to import")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("PRMS Sample Data Seeder")
    print("="*60)
    
    # Create tables if they don't exist
    print("\n📊 Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("   ✅ Database tables ready")
    except Exception as e:
        print(f"   ⚠️  Database init message: {e}")
    
    session = Session()
    
    try:
        if args.clean:
            clean_sample_data(session)
        
        # Create asset types with custom fields
        asset_types = create_asset_types(session)
        
        # Create system user
        system_user = create_system_user(session)
        
        # Create projects
        projects = create_projects(session, system_user)
        
        # Create resources and allocations
        create_resources(session, projects, asset_types, system_user)
        
        print("\n" + "="*60)
        print("✅ Sample data seeding complete!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   • Asset Types: {len(asset_types)}")
        print(f"   • Projects: {len(projects)}")
        print(f"   • Projects with high budget utilization (80%+): 2")
        print(f"   • Projects at full budget utilization (100%): 2")
        print("\n🎯 Budget Utilization Summary:")
        
        for project_name, utilization_pct in [
            ("Enterprise Infrastructure", 85),
            ("Cloud Migration", 100),
            ("Digital Transformation", 60),
            ("Data Analytics Platform", 70),
            ("Cybersecurity Initiative", 100),
            ("Business Automation", 50),
            ("Legacy System Modernization", 25),
            ("AI & Machine Learning Initiative", 0),
            ("Mobile Application Dev", 0),
            ("Customer Portal Redesign", 0),
        ]:
            status = "🔴 CRITICAL" if utilization_pct == 100 else "🟠 WARNING" if utilization_pct >= 80 else "🟢 OK"
            print(f"   • {project_name}: {utilization_pct}% {status}")
        
        print("\n💡 Next steps:")
        print("   1. Start the backend: python -m uvicorn app.main:app --reload")
        print("   2. Start the frontend: npm start (in frontend directory)")
        print("   3. Open dashboard at http://localhost:3000")
        print("\n" + "="*60)
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
