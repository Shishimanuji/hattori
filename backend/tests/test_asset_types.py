"""Tests for Asset Type API endpoints"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.asset_type import AssetType, CustomField, FieldType
from app.models.user import User, UserRole
from app.utils.jwt_utils import create_access_token


# Fixtures for test data
@pytest.fixture
def asset_type_personnel(db: Session) -> AssetType:
    """Create a test asset type"""
    asset_type = AssetType(
        id=uuid4(),
        name="Personnel",
        description="Personnel resource type",
        is_active=True,
    )
    db.add(asset_type)
    db.commit()
    db.refresh(asset_type)
    return asset_type


@pytest.fixture
def asset_type_equipment(db: Session) -> AssetType:
    """Create a test asset type with custom fields"""
    asset_type = AssetType(
        id=uuid4(),
        name="Equipment",
        description="Equipment resource type",
        is_active=True,
    )
    
    # Add custom fields
    field1 = CustomField(
        id=uuid4(),
        asset_type_id=asset_type.id,
        name="Department",
        field_type=FieldType.DROPDOWN.value,
        is_required=True,
        options=["Engineering", "Sales", "HR"],
        display_order=1,
    )
    
    field2 = CustomField(
        id=uuid4(),
        asset_type_id=asset_type.id,
        name="Condition",
        field_type=FieldType.TEXT.value,
        is_required=False,
        display_order=2,
    )
    
    asset_type.custom_fields.append(field1)
    asset_type.custom_fields.append(field2)
    
    db.add(asset_type)
    db.commit()
    db.refresh(asset_type)
    return asset_type


@pytest.fixture
def admin_headers(test_admin_user: User) -> dict:
    """Generate auth headers for admin user"""
    token = create_access_token(str(test_admin_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(test_user: User) -> dict:
    """Generate auth headers for manager user"""
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


# Tests for GET /api/asset-types
class TestListAssetTypes:
    """Tests for listing asset types"""
    
    def test_list_asset_types_success_admin(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
        asset_type_equipment: AssetType,
    ):
        """Test successful listing of asset types by admin"""
        response = client.get(
            "/api/asset-types",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_more" in data
        
        # Verify items
        assert len(data["items"]) >= 2
        assert data["total"] >= 2
        
        # Verify asset type details
        names = [item["name"] for item in data["items"]]
        assert "Personnel" in names
        assert "Equipment" in names
        
        # Check field counts
        equipment = next(item for item in data["items"] if item["name"] == "Equipment")
        assert equipment["field_count"] == 2
    
    def test_list_asset_types_pagination(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test pagination in asset type listing"""
        # Create multiple asset types
        for i in range(5):
            asset_type = AssetType(
                id=uuid4(),
                name=f"Type_{i}",
                is_active=True,
            )
            db.add(asset_type)
        db.commit()
        
        # Request first page with limit 2
        response = client.get(
            "/api/asset-types?page=0&limit=2",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 0
        assert data["page_size"] == 2
        assert data["has_more"] is True
        
        # Request second page
        response = client.get(
            "/api/asset-types?page=1&limit=2",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
    
    def test_list_asset_types_exclude_inactive(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test excluding inactive asset types"""
        # Create active and inactive types
        active = AssetType(id=uuid4(), name="Active", is_active=True)
        inactive = AssetType(id=uuid4(), name="Inactive", is_active=False)
        db.add(active)
        db.add(inactive)
        db.commit()
        
        # Request excluding inactive
        response = client.get(
            "/api/asset-types?include_inactive=false",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert "Active" in names
        assert "Inactive" not in names
    
    def test_list_asset_types_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
    ):
        """Test that non-admin users cannot list asset types"""
        response = client.get(
            "/api/asset-types",
            headers=manager_headers,
        )
        
        assert response.status_code == 403
    
    def test_list_asset_types_no_auth(self, client: TestClient):
        """Test that unauthenticated users cannot list asset types"""
        response = client.get("/api/asset-types")
        
        assert response.status_code == 401


# Tests for POST /api/asset-types
class TestCreateAssetType:
    """Tests for creating asset types"""
    
    def test_create_asset_type_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test successful asset type creation"""
        payload = {
            "name": "Software License",
            "description": "Software license resources",
            "custom_fields": [],
        }
        
        response = client.post(
            "/api/asset-types",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response
        assert data["name"] == "Software License"
        assert data["description"] == "Software license resources"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["custom_fields"] == []
    
    def test_create_asset_type_with_custom_fields(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test asset type creation with initial custom fields"""
        payload = {
            "name": "Vehicle",
            "description": "Vehicle resources",
            "custom_fields": [
                {
                    "name": "Make",
                    "field_type": "text",
                    "is_required": True,
                    "display_order": 1,
                },
                {
                    "name": "Mileage",
                    "field_type": "number",
                    "is_required": False,
                    "display_order": 2,
                },
                {
                    "name": "Status",
                    "field_type": "dropdown",
                    "is_required": True,
                    "options": ["Active", "Maintenance", "Retired"],
                    "display_order": 3,
                },
            ],
        }
        
        response = client.post(
            "/api/asset-types",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify asset type
        assert data["name"] == "Vehicle"
        
        # Verify custom fields
        assert len(data["custom_fields"]) == 3
        fields = {cf["name"]: cf for cf in data["custom_fields"]}
        
        assert "Make" in fields
        assert fields["Make"]["field_type"] == "text"
        assert fields["Make"]["is_required"] is True
        
        assert "Status" in fields
        assert fields["Status"]["field_type"] == "dropdown"
        assert set(fields["Status"]["options"]) == {"Active", "Maintenance", "Retired"}
    
    def test_create_asset_type_duplicate_name(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test that duplicate names are rejected"""
        payload = {
            "name": "Personnel",  # Already exists
            "description": "Another personnel",
        }
        
        response = client.post(
            "/api/asset-types",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    def test_create_asset_type_invalid_field(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test that invalid field configuration is rejected"""
        payload = {
            "name": "Invalid Type",
            "custom_fields": [
                {
                    "name": "Dropdown Field",
                    "field_type": "dropdown",
                    "is_required": True,
                    # Missing options for dropdown
                }
            ],
        }
        
        response = client.post(
            "/api/asset-types",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_create_asset_type_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
    ):
        """Test that non-admin users cannot create asset types"""
        payload = {
            "name": "New Type",
            "description": "Should fail",
        }
        
        response = client.post(
            "/api/asset-types",
            json=payload,
            headers=manager_headers,
        )
        
        assert response.status_code == 403


# Tests for GET /api/asset-types/{id}
class TestGetAssetType:
    """Tests for getting asset type details"""
    
    def test_get_asset_type_success(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_equipment: AssetType,
    ):
        """Test successful asset type retrieval"""
        response = client.get(
            f"/api/asset-types/{asset_type_equipment.id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify asset type
        assert data["id"] == str(asset_type_equipment.id)
        assert data["name"] == "Equipment"
        assert data["field_count"] == 2
        
        # Verify custom fields are sorted by display_order
        assert len(data["custom_fields"]) == 2
        assert data["custom_fields"][0]["name"] == "Department"
        assert data["custom_fields"][1]["name"] == "Condition"
    
    def test_get_asset_type_not_found(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test retrieving non-existent asset type"""
        fake_id = uuid4()
        response = client.get(
            f"/api/asset-types/{fake_id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_get_asset_type_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test that non-admin cannot retrieve asset types"""
        response = client.get(
            f"/api/asset-types/{asset_type_personnel.id}",
            headers=manager_headers,
        )
        
        assert response.status_code == 403


# Tests for PUT /api/asset-types/{id}
class TestUpdateAssetType:
    """Tests for updating asset types"""
    
    def test_update_asset_type_name(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_personnel: AssetType,
    ):
        """Test updating asset type name"""
        payload = {
            "name": "Personnel Updated",
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_personnel.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Personnel Updated"
        
        # Verify in database
        db.refresh(asset_type_personnel)
        assert asset_type_personnel.name == "Personnel Updated"
    
    def test_update_asset_type_description(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_personnel: AssetType,
    ):
        """Test updating asset type description"""
        payload = {
            "description": "New description",
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_personnel.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
    
    def test_update_asset_type_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_personnel: AssetType,
    ):
        """Test deactivating asset type"""
        payload = {
            "is_active": False,
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_personnel.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
    
    def test_update_asset_type_duplicate_name(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test that duplicate names are rejected during update"""
        # Create two asset types
        type1 = AssetType(id=uuid4(), name="Type1", is_active=True)
        type2 = AssetType(id=uuid4(), name="Type2", is_active=True)
        db.add(type1)
        db.add(type2)
        db.commit()
        
        # Try to rename type2 to type1's name
        payload = {"name": "Type1"}
        response = client.put(
            f"/api/asset-types/{type2.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 409
    
    def test_update_asset_type_not_found(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test updating non-existent asset type"""
        fake_id = uuid4()
        payload = {"name": "New Name"}
        
        response = client.put(
            f"/api/asset-types/{fake_id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_update_asset_type_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test that non-admin cannot update asset types"""
        payload = {"name": "New Name"}
        
        response = client.put(
            f"/api/asset-types/{asset_type_personnel.id}",
            json=payload,
            headers=manager_headers,
        )
        
        assert response.status_code == 403


# Tests for DELETE /api/asset-types/{id}
class TestDeleteAssetType:
    """Tests for deleting (marking inactive) asset types"""
    
    def test_delete_asset_type_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_personnel: AssetType,
    ):
        """Test successful asset type soft delete"""
        response = client.delete(
            f"/api/asset-types/{asset_type_personnel.id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 204
        
        # Verify in database
        db.refresh(asset_type_personnel)
        assert asset_type_personnel.is_active is False
    
    def test_delete_asset_type_not_found(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test deleting non-existent asset type"""
        fake_id = uuid4()
        response = client.delete(
            f"/api/asset-types/{fake_id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_delete_asset_type_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test that non-admin cannot delete asset types"""
        response = client.delete(
            f"/api/asset-types/{asset_type_personnel.id}",
            headers=manager_headers,
        )
        
        assert response.status_code == 403


# Integration tests
class TestAssetTypeIntegration:
    """Integration tests for asset type workflow"""
    
    def test_full_asset_type_workflow(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test complete asset type CRUD workflow"""
        # 1. Create asset type
        create_payload = {
            "name": "Contractor",
            "description": "Contractor resources",
            "custom_fields": [
                {
                    "name": "Skill",
                    "field_type": "text",
                    "is_required": True,
                }
            ],
        }
        
        response = client.post(
            "/api/asset-types",
            json=create_payload,
            headers=admin_headers,
        )
        assert response.status_code == 201
        asset_type_id = response.json()["id"]
        
        # 2. List asset types (verify new one appears)
        response = client.get(
            "/api/asset-types",
            headers=admin_headers,
        )
        assert response.status_code == 200
        names = [item["name"] for item in response.json()["items"]]
        assert "Contractor" in names
        
        # 3. Get specific asset type
        response = client.get(
            f"/api/asset-types/{asset_type_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Contractor"
        
        # 4. Update asset type
        update_payload = {
            "description": "Updated contractor resources",
        }
        response = client.put(
            f"/api/asset-types/{asset_type_id}",
            json=update_payload,
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated contractor resources"
        
        # 5. Delete (deactivate) asset type
        response = client.delete(
            f"/api/asset-types/{asset_type_id}",
            headers=admin_headers,
        )
        assert response.status_code == 204
        
        # 6. Verify deletion
        response = client.get(
            f"/api/asset-types/{asset_type_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False
    
    def test_asset_types_with_multiple_fields(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test asset type with many custom fields"""
        fields = [
            {"name": "Field1", "field_type": "text", "display_order": 1},
            {"name": "Field2", "field_type": "number", "display_order": 2},
            {"name": "Field3", "field_type": "date", "display_order": 3},
            {"name": "Field4", "field_type": "boolean", "display_order": 4},
            {"name": "Field5", "field_type": "dropdown", "options": ["A", "B"], "display_order": 5},
        ]
        
        payload = {
            "name": "Complex Type",
            "custom_fields": fields,
        }
        
        response = client.post(
            "/api/asset-types",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["custom_fields"]) == 5
        
        # Verify order is preserved
        for i, field in enumerate(data["custom_fields"]):
            assert field["display_order"] == i + 1


# Tests for POST /api/asset-types/{id}/fields
class TestAddCustomField:
    """Tests for adding custom fields to asset types"""
    
    def test_add_custom_field_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_personnel: AssetType,
    ):
        """Test successful custom field addition"""
        payload = {
            "name": "Skill Level",
            "field_type": "dropdown",
            "is_required": True,
            "options": ["Junior", "Mid", "Senior"],
            "display_order": 1,
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert data["name"] == "Skill Level"
        assert data["field_type"] == "dropdown"
        assert data["is_required"] is True
        assert data["display_order"] == 1
        assert data["options"] == ["Junior", "Mid", "Senior"]
        assert data["asset_type_id"] == str(asset_type_personnel.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify in database
        db.refresh(asset_type_personnel)
        assert len(asset_type_personnel.custom_fields) == 1
        assert asset_type_personnel.custom_fields[0].name == "Skill Level"
    
    def test_add_custom_field_text_type(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test adding text field"""
        payload = {
            "name": "Notes",
            "field_type": "text",
            "is_required": False,
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "text"
        assert data["is_required"] is False
    
    def test_add_custom_field_number_type(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test adding number field"""
        payload = {
            "name": "Experience Years",
            "field_type": "number",
            "is_required": True,
            "validation_rules": {"min": 0, "max": 50},
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "number"
        assert data["validation_rules"]["min"] == 0
        assert data["validation_rules"]["max"] == 50
    
    def test_add_custom_field_date_type(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test adding date field"""
        payload = {
            "name": "Start Date",
            "field_type": "date",
            "is_required": True,
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "date"
    
    def test_add_custom_field_boolean_type(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test adding boolean field"""
        payload = {
            "name": "Is Available",
            "field_type": "boolean",
            "is_required": False,
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_type"] == "boolean"
    
    def test_add_custom_field_duplicate_name(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_equipment: AssetType,
    ):
        """Test that duplicate field names are rejected"""
        # asset_type_equipment already has "Department" field
        payload = {
            "name": "Department",  # Duplicate
            "field_type": "text",
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_equipment.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    def test_add_custom_field_asset_type_not_found(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test adding field to non-existent asset type"""
        fake_id = uuid4()
        payload = {
            "name": "Field",
            "field_type": "text",
        }
        
        response = client.post(
            f"/api/asset-types/{fake_id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_add_custom_field_invalid_field_type(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test that invalid field type is rejected"""
        payload = {
            "name": "Bad Field",
            "field_type": "invalid_type",
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_add_custom_field_dropdown_without_options(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test that dropdown without options is rejected"""
        payload = {
            "name": "Bad Dropdown",
            "field_type": "dropdown",
            # Missing options
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 422
    
    def test_add_custom_field_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
        asset_type_personnel: AssetType,
    ):
        """Test that non-admin cannot add fields"""
        payload = {
            "name": "Field",
            "field_type": "text",
        }
        
        response = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json=payload,
            headers=manager_headers,
        )
        
        assert response.status_code == 403
    
    def test_add_multiple_custom_fields(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_personnel: AssetType,
    ):
        """Test adding multiple fields to same asset type"""
        # Add first field
        response1 = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json={"name": "Field1", "field_type": "text"},
            headers=admin_headers,
        )
        assert response1.status_code == 201
        field1_id = response1.json()["id"]
        
        # Add second field
        response2 = client.post(
            f"/api/asset-types/{asset_type_personnel.id}/fields",
            json={"name": "Field2", "field_type": "number"},
            headers=admin_headers,
        )
        assert response2.status_code == 201
        field2_id = response2.json()["id"]
        
        # Verify both exist
        db.refresh(asset_type_personnel)
        assert len(asset_type_personnel.custom_fields) == 2
        field_ids = {cf.id for cf in asset_type_personnel.custom_fields}
        assert UUID(field1_id) in field_ids
        assert UUID(field2_id) in field_ids


# Tests for PUT /api/asset-types/{id}/fields/{field-id}
class TestUpdateCustomField:
    """Tests for updating custom fields"""
    
    def test_update_custom_field_name(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test updating field name"""
        field = asset_type_equipment.custom_fields[0]  # "Department"
        
        payload = {
            "name": "Department Updated",
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Department Updated"
        
        # Verify in database
        db.refresh(field)
        assert field.name == "Department Updated"
    
    def test_update_custom_field_is_required(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test updating is_required flag"""
        field = asset_type_equipment.custom_fields[1]  # "Condition"
        
        payload = {
            "is_required": True,
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_required"] is True
        
        db.refresh(field)
        assert field.is_required is True
    
    def test_update_custom_field_display_order(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test updating display order"""
        field = asset_type_equipment.custom_fields[0]
        
        payload = {
            "display_order": 10,
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["display_order"] == 10
    
    def test_update_custom_field_options(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test updating dropdown options"""
        field = asset_type_equipment.custom_fields[0]  # "Department" dropdown
        
        payload = {
            "options": ["Engineering", "Sales", "HR", "Marketing"],
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["options"] == ["Engineering", "Sales", "HR", "Marketing"]
    
    def test_update_custom_field_validation_rules(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_equipment: AssetType,
    ):
        """Test updating validation rules"""
        field = asset_type_equipment.custom_fields[1]  # "Condition" text field
        
        payload = {
            "validation_rules": {"min_length": 5, "max_length": 50},
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["validation_rules"]["min_length"] == 5
        assert data["validation_rules"]["max_length"] == 50
    
    def test_update_custom_field_duplicate_name(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test that duplicate names are rejected during update"""
        field1 = asset_type_equipment.custom_fields[0]  # "Department"
        field2 = asset_type_equipment.custom_fields[1]  # "Condition"
        
        # Try to rename field2 to field1's name
        payload = {
            "name": "Department",  # Duplicate
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field2.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    def test_update_custom_field_not_found(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_equipment: AssetType,
    ):
        """Test updating non-existent field"""
        fake_field_id = uuid4()
        payload = {"name": "New Name"}
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{fake_field_id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_update_custom_field_wrong_asset_type(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_personnel: AssetType,
        asset_type_equipment: AssetType,
    ):
        """Test that field cannot be updated with wrong asset type ID"""
        field = asset_type_equipment.custom_fields[0]
        
        # Try to access field with wrong asset type ID
        payload = {"name": "New Name"}
        
        response = client.put(
            f"/api/asset-types/{asset_type_personnel.id}/fields/{field.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_update_custom_field_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
        asset_type_equipment: AssetType,
    ):
        """Test that non-admin cannot update fields"""
        field = asset_type_equipment.custom_fields[0]
        payload = {"name": "New Name"}
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            json=payload,
            headers=manager_headers,
        )
        
        assert response.status_code == 403
    
    def test_update_multiple_field_properties(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test updating multiple field properties at once"""
        field = asset_type_equipment.custom_fields[0]
        
        payload = {
            "name": "Department Updated",
            "is_required": False,
            "display_order": 5,
            "options": ["Dept A", "Dept B", "Dept C"],
        }
        
        response = client.put(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            json=payload,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Department Updated"
        assert data["is_required"] is False
        assert data["display_order"] == 5
        assert data["options"] == ["Dept A", "Dept B", "Dept C"]


# Tests for DELETE /api/asset-types/{id}/fields/{field-id}
class TestRemoveCustomField:
    """Tests for removing custom fields"""
    
    def test_remove_custom_field_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test successful field removal"""
        field = asset_type_equipment.custom_fields[0]
        field_id = field.id
        
        response = client.delete(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field_id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 204
        
        # Verify field is deleted from database
        db.refresh(asset_type_equipment)
        remaining_field_ids = {cf.id for cf in asset_type_equipment.custom_fields}
        assert field_id not in remaining_field_ids
        assert len(asset_type_equipment.custom_fields) == 1
    
    def test_remove_custom_field_not_found(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_equipment: AssetType,
    ):
        """Test removing non-existent field"""
        fake_field_id = uuid4()
        
        response = client.delete(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{fake_field_id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_remove_custom_field_wrong_asset_type(
        self,
        client: TestClient,
        admin_headers: dict,
        asset_type_personnel: AssetType,
        asset_type_equipment: AssetType,
    ):
        """Test that field cannot be removed with wrong asset type ID"""
        field = asset_type_equipment.custom_fields[0]
        
        # Try to remove field with wrong asset type ID
        response = client.delete(
            f"/api/asset-types/{asset_type_personnel.id}/fields/{field.id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_remove_custom_field_asset_type_not_found(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test removing field from non-existent asset type"""
        fake_asset_type_id = uuid4()
        fake_field_id = uuid4()
        
        response = client.delete(
            f"/api/asset-types/{fake_asset_type_id}/fields/{fake_field_id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 404
    
    def test_remove_custom_field_non_admin_forbidden(
        self,
        client: TestClient,
        manager_headers: dict,
        asset_type_equipment: AssetType,
    ):
        """Test that non-admin cannot remove fields"""
        field = asset_type_equipment.custom_fields[0]
        
        response = client.delete(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field.id}",
            headers=manager_headers,
        )
        
        assert response.status_code == 403
    
    def test_remove_multiple_fields_sequentially(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
        asset_type_equipment: AssetType,
    ):
        """Test removing multiple fields one by one"""
        field_ids = [cf.id for cf in asset_type_equipment.custom_fields]
        
        # Remove first field
        response1 = client.delete(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field_ids[0]}",
            headers=admin_headers,
        )
        assert response1.status_code == 204
        
        # Remove second field
        response2 = client.delete(
            f"/api/asset-types/{asset_type_equipment.id}/fields/{field_ids[1]}",
            headers=admin_headers,
        )
        assert response2.status_code == 204
        
        # Verify all fields are deleted
        db.refresh(asset_type_equipment)
        assert len(asset_type_equipment.custom_fields) == 0


# Integration tests for custom field management
class TestCustomFieldIntegration:
    """Integration tests for custom field CRUD workflow"""
    
    def test_custom_field_full_workflow(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test complete custom field CRUD workflow"""
        # 1. Create asset type
        asset_type_response = client.post(
            "/api/asset-types",
            json={
                "name": "Test Asset Type",
                "description": "For testing custom fields",
            },
            headers=admin_headers,
        )
        assert asset_type_response.status_code == 201
        asset_type_id = asset_type_response.json()["id"]
        
        # 2. Add first custom field
        add_field1_response = client.post(
            f"/api/asset-types/{asset_type_id}/fields",
            json={
                "name": "Field 1",
                "field_type": "text",
                "is_required": True,
                "display_order": 1,
            },
            headers=admin_headers,
        )
        assert add_field1_response.status_code == 201
        field1_id = add_field1_response.json()["id"]
        
        # 3. Add second custom field
        add_field2_response = client.post(
            f"/api/asset-types/{asset_type_id}/fields",
            json={
                "name": "Field 2",
                "field_type": "number",
                "is_required": False,
                "display_order": 2,
            },
            headers=admin_headers,
        )
        assert add_field2_response.status_code == 201
        field2_id = add_field2_response.json()["id"]
        
        # 4. Verify fields appear in asset type
        get_response = client.get(
            f"/api/asset-types/{asset_type_id}",
            headers=admin_headers,
        )
        assert get_response.status_code == 200
        asset_type = get_response.json()
        assert asset_type["field_count"] == 2
        field_names = [f["name"] for f in asset_type["custom_fields"]]
        assert "Field 1" in field_names
        assert "Field 2" in field_names
        
        # 5. Update first field
        update_response = client.put(
            f"/api/asset-types/{asset_type_id}/fields/{field1_id}",
            json={
                "name": "Field 1 Updated",
                "is_required": False,
            },
            headers=admin_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Field 1 Updated"
        
        # 6. Remove second field
        delete_response = client.delete(
            f"/api/asset-types/{asset_type_id}/fields/{field2_id}",
            headers=admin_headers,
        )
        assert delete_response.status_code == 204
        
        # 7. Verify final state
        final_response = client.get(
            f"/api/asset-types/{asset_type_id}",
            headers=admin_headers,
        )
        assert final_response.status_code == 200
        final_asset_type = final_response.json()
        assert final_asset_type["field_count"] == 1
        assert final_asset_type["custom_fields"][0]["name"] == "Field 1 Updated"
    
    def test_custom_fields_with_all_types(
        self,
        client: TestClient,
        admin_headers: dict,
        db: Session,
    ):
        """Test creating fields of all types"""
        # Create asset type
        asset_type_response = client.post(
            "/api/asset-types",
            json={"name": "All Field Types"},
            headers=admin_headers,
        )
        asset_type_id = asset_type_response.json()["id"]
        
        # Add each field type
        field_configs = [
            {
                "name": "Text Field",
                "field_type": "text",
            },
            {
                "name": "Number Field",
                "field_type": "number",
                "validation_rules": {"min": 0},
            },
            {
                "name": "Date Field",
                "field_type": "date",
            },
            {
                "name": "Boolean Field",
                "field_type": "boolean",
            },
            {
                "name": "Dropdown Field",
                "field_type": "dropdown",
                "options": ["Option 1", "Option 2", "Option 3"],
            },
        ]
        
        for i, config in enumerate(field_configs):
            config["display_order"] = i + 1
            response = client.post(
                f"/api/asset-types/{asset_type_id}/fields",
                json=config,
                headers=admin_headers,
            )
            assert response.status_code == 201
            assert response.json()["field_type"] == config["field_type"]
        
        # Verify all fields exist
        get_response = client.get(
            f"/api/asset-types/{asset_type_id}",
            headers=admin_headers,
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["field_count"] == 5
        
        # Verify types
        field_types = {f["name"]: f["field_type"] for f in data["custom_fields"]}
        assert field_types["Text Field"] == "text"
        assert field_types["Number Field"] == "number"
        assert field_types["Date Field"] == "date"
        assert field_types["Boolean Field"] == "boolean"
        assert field_types["Dropdown Field"] == "dropdown"
