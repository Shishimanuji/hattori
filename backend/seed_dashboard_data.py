"""
Seed database with sample data for dashboard testing
Creates projects and resources from infrastructure data
"""
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Add backend to path
sys.path.insert(0, 'd:\\Anugya_PRMS\\backend')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.project import Project, ProjectStatus
from app.models.resource import Resource, ResourceStatus
from app.models.asset_type import AssetType
from app.models.user import User, UserRole
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    """Seed the database with sample infrastructure data"""
    db = SessionLocal()
    
    try:
        # Create or get admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                id=uuid4(),
                username="admin",
                email="admin@prms.local",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUmGEJiq",  # password123
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Created admin user: {admin_user.username}")
        
        # Create asset types
        asset_types_data = [
            ("Server", "Computing servers (physical/virtual)"),
            ("Storage", "Storage systems and arrays"),
            ("Firewall", "Network security appliances"),
            ("Switch", "Network switches (L2/L3)"),
            ("KVM Switch", "Keyboard-Video-Mouse switches"),
            ("Workstation", "Desktop/workstation computers"),
        ]
        
        asset_types = {}
        for name, description in asset_types_data:
            asset_type = db.query(AssetType).filter(AssetType.name == name).first()
            if not asset_type:
                asset_type = AssetType(
                    id=uuid4(),
                    name=name,
                    description=description,
                    is_active=True
                )
                db.add(asset_type)
                db.commit()
                logger.info(f"Created asset type: {name}")
            asset_types[name] = asset_type
        
        # Create Seaweb project
        seaweb_project = db.query(Project).filter(Project.name == "Seaweb").first()
        if not seaweb_project:
            seaweb_project = Project(
                id=uuid4(),
                name="Seaweb",
                description="Seaweb Compute Infrastructure - Data Centre Resources",
                status=ProjectStatus.ACTIVE,
                budget=Decimal("5000000"),  # 50 lakh
                allocated_budget=Decimal("0"),
                owner_id=admin_user.id,
                start_date=date(2023, 3, 9),
                end_date=date(2028, 8, 25)
            )
            db.add(seaweb_project)
            db.commit()
            logger.info(f"Created project: Seaweb")
        
        # Create Baaz project
        baaz_project = db.query(Project).filter(Project.name == "Baaz").first()
        if not baaz_project:
            baaz_project = Project(
                id=uuid4(),
                name="Baaz",
                description="Baaz Project Infrastructure",
                status=ProjectStatus.ACTIVE,
                budget=Decimal("2000000"),  # 20 lakh
                allocated_budget=Decimal("0"),
                owner_id=admin_user.id,
                start_date=date(2023, 8, 28),
                end_date=date(2028, 8, 25)
            )
            db.add(baaz_project)
            db.commit()
            logger.info(f"Created project: Baaz")
        
        # Servers data from your Excel
        servers_data = [
            {
                "name": "Seaw Server 1 (Tyrone SDI100A3V)",
                "model": "Tyrone Systems SDI100A3V-212",
                "serial": "2X23492303",
                "cost": 1800000,
                "project": seaweb_project,
                "warranty_end": date(2028, 3, 9),
            },
            {
                "name": "Seaw Server 2 (Dell R740XD #1)",
                "model": "Dell Power edge R740XD",
                "serial": "58SL5Y3",
                "cost": 900000,
                "project": seaweb_project,
                "warranty_end": date(2028, 7, 13),
            },
            {
                "name": "Seaw Server 3 (Dell R740XD #2)",
                "model": "Dell Power edge R740XD",
                "serial": "68SL5Y3",
                "cost": 900000,
                "project": seaweb_project,
                "warranty_end": date(2028, 7, 13),
            },
            {
                "name": "Seaw Server 4 (Dell R740XD #3)",
                "model": "Dell Power edge R740XD",
                "serial": "78SL5Y3",
                "cost": 900000,
                "project": seaweb_project,
                "warranty_end": date(2028, 7, 13),
            },
            {
                "name": "Seaw Server 5 (Dell R740XD #4)",
                "model": "Dell Power edge R740XD",
                "serial": "88SL5Y3",
                "cost": 900000,
                "project": seaweb_project,
                "warranty_end": date(2028, 7, 13),
            },
            {
                "name": "Seaw Server 6 (Dell R740XD #5)",
                "model": "Dell Power edge R740XD",
                "serial": "98SL5Y3",
                "cost": 900000,
                "project": seaweb_project,
                "warranty_end": date(2028, 7, 13),
            },
            {
                "name": "Baaz Server 7 (Dell R740XD Gold)",
                "model": "Dell Power edge R740XD",
                "serial": "6NJ1VX3",
                "cost": 1200000,
                "project": baaz_project,
                "warranty_end": date(2028, 8, 25),
            },
        ]
        
        # Add servers
        created_servers = 0
        for server_data in servers_data:
            existing = db.query(Resource).filter(
                Resource.name == server_data["name"]
            ).first()
            if not existing:
                server = Resource(
                    id=uuid4(),
                    project_id=server_data["project"].id,
                    asset_type_id=asset_types["Server"].id,
                    name=server_data["name"],
                    cost=Decimal(str(server_data["cost"])),
                    allocation_date=date.today(),
                    status=ResourceStatus.ACTIVE,
                    created_by=admin_user.id,
                    custom_field_values={
                        "model": server_data["model"],
                        "serial_number": server_data["serial"],
                        "warranty_end": server_data["warranty_end"].isoformat(),
                    }
                )
                db.add(server)
                created_servers += 1
        
        if created_servers > 0:
            db.commit()
            logger.info(f"Created {created_servers} servers")
        
        # Storage data
        storage_data = [
            {
                "name": "Seaweb Storage 1 (Dell Unity 380 - 80TB)",
                "model": "Dell Unity 380",
                "serial": "D2R26V3",
                "cost": 2000000,
                "project": seaweb_project,
                "warranty_end": date(2028, 7, 13),
            },
            {
                "name": "Baaz Storage (Dell Unity 380 - 80TB)",
                "model": "Dell Unity 380",
                "serial": "HGQ26V3",
                "cost": 2000000,
                "project": baaz_project,
                "warranty_end": date(2028, 8, 25),
            },
        ]
        
        created_storage = 0
        for storage in storage_data:
            existing = db.query(Resource).filter(
                Resource.name == storage["name"]
            ).first()
            if not existing:
                resource = Resource(
                    id=uuid4(),
                    project_id=storage["project"].id,
                    asset_type_id=asset_types["Storage"].id,
                    name=storage["name"],
                    cost=Decimal(str(storage["cost"])),
                    allocation_date=date.today(),
                    status=ResourceStatus.ACTIVE,
                    created_by=admin_user.id,
                    custom_field_values={
                        "model": storage["model"],
                        "serial_number": storage["serial"],
                        "warranty_end": storage["warranty_end"].isoformat(),
                    }
                )
                db.add(resource)
                created_storage += 1
        
        if created_storage > 0:
            db.commit()
            logger.info(f"Created {created_storage} storage units")
        
        # Firewall data
        firewall_data = [
            {
                "name": "Check Point Firewall 1550",
                "model": "1550 Appliances",
                "serial": "BA22B04180",
                "cost": 500000,
                "project": seaweb_project,
                "warranty_end": date(2026, 8, 28),
            },
            {
                "name": "Fortinet FortiGate V750",
                "model": "V750",
                "serial": "W1789V750DI2002082",
                "cost": 300000,
                "project": seaweb_project,
                "warranty_end": date(2026, 8, 28),
            },
        ]
        
        created_firewalls = 0
        for fw in firewall_data:
            existing = db.query(Resource).filter(
                Resource.name == fw["name"]
            ).first()
            if not existing:
                resource = Resource(
                    id=uuid4(),
                    project_id=fw["project"].id,
                    asset_type_id=asset_types["Firewall"].id,
                    name=fw["name"],
                    cost=Decimal(str(fw["cost"])),
                    allocation_date=date.today(),
                    status=ResourceStatus.ACTIVE,
                    created_by=admin_user.id,
                    custom_field_values={
                        "model": fw["model"],
                        "serial_number": fw["serial"],
                        "warranty_end": fw["warranty_end"].isoformat(),
                    }
                )
                db.add(resource)
                created_firewalls += 1
        
        if created_firewalls > 0:
            db.commit()
            logger.info(f"Created {created_firewalls} firewalls")
        
        # Network Switches (L3)
        l3_switches = [
            {
                "name": "Dell EMC L3 Switch 1 (S4148F)",
                "model": "S4148F - ON",
                "serial": "JG05W43",
                "cost": 400000,
                "warranty_end": date(2028, 8, 28),
            },
            {
                "name": "Dell EMC L3 Switch 2 (S4148F)",
                "model": "S4148F - ON",
                "serial": "GG05W43",
                "cost": 400000,
                "warranty_end": date(2028, 8, 28),
            },
        ]
        
        created_switches = 0
        for switch in l3_switches:
            existing = db.query(Resource).filter(
                Resource.name == switch["name"]
            ).first()
            if not existing:
                resource = Resource(
                    id=uuid4(),
                    project_id=seaweb_project.id,
                    asset_type_id=asset_types["Switch"].id,
                    name=switch["name"],
                    cost=Decimal(str(switch["cost"])),
                    allocation_date=date.today(),
                    status=ResourceStatus.ACTIVE,
                    created_by=admin_user.id,
                    custom_field_values={
                        "model": switch["model"],
                        "serial_number": switch["serial"],
                        "type": "L3",
                        "warranty_end": switch["warranty_end"].isoformat(),
                    }
                )
                db.add(resource)
                created_switches += 1
        
        if created_switches > 0:
            db.commit()
            logger.info(f"Created {created_switches} L3 switches")
        
        # Workstations (sample)
        workstations = [
            {
                "name": "Acer Workstation 1 (Seaweb Data)",
                "model": "Acer Vertion 52680G",
                "serial": "UXBGVSI814M4052103",
                "cost": 150000,
                "project": seaweb_project,
                "warranty_end": date(2025, 10, 14),
            },
            {
                "name": "Dell Workstation 1 (MTNL)",
                "model": "Dell Optiplex 5060",
                "serial": "GHRR3W2",
                "cost": 120000,
                "project": seaweb_project,
                "warranty_end": date(2022, 12, 31),
            },
            {
                "name": "Tyrone Workstation 1 (222D)",
                "model": "Tyrone SS400TR-34",
                "serial": "TX20552303",
                "cost": 350000,
                "project": seaweb_project,
                "warranty_end": date(2026, 8, 9),
            },
        ]
        
        created_workstations = 0
        for ws in workstations:
            existing = db.query(Resource).filter(
                Resource.name == ws["name"]
            ).first()
            if not existing:
                resource = Resource(
                    id=uuid4(),
                    project_id=ws["project"].id,
                    asset_type_id=asset_types["Workstation"].id,
                    name=ws["name"],
                    cost=Decimal(str(ws["cost"])),
                    allocation_date=date.today(),
                    status=ResourceStatus.ACTIVE,
                    created_by=admin_user.id,
                    custom_field_values={
                        "model": ws["model"],
                        "serial_number": ws["serial"],
                        "warranty_end": ws["warranty_end"].isoformat(),
                    }
                )
                db.add(resource)
                created_workstations += 1
        
        if created_workstations > 0:
            db.commit()
            logger.info(f"Created {created_workstations} workstations")
        
        # Update project budgets
        seaweb_allocated = db.query(func.sum(Resource.cost)).filter(
            Resource.project_id == seaweb_project.id,
            Resource.deleted_at.is_(None)
        ).scalar() or 0
        
        baaz_allocated = db.query(func.sum(Resource.cost)).filter(
            Resource.project_id == baaz_project.id,
            Resource.deleted_at.is_(None)
        ).scalar() or 0
        
        seaweb_project.allocated_budget = Decimal(str(seaweb_allocated))
        baaz_project.allocated_budget = Decimal(str(baaz_allocated))
        
        db.commit()
        logger.info(f"Updated project budgets")
        
        # Summary
        total_projects = db.query(Project).filter(Project.deleted_at.is_(None)).count()
        total_resources = db.query(Resource).filter(Resource.deleted_at.is_(None)).count()
        
        logger.info(f"✅ Database seeding complete!")
        logger.info(f"   Projects: {total_projects}")
        logger.info(f"   Resources: {total_resources}")
        logger.info(f"   Asset Types: {len(asset_types)}")
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting database seeding...")
    seed_data()
    logger.info("Done!")
