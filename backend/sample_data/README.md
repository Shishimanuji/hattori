# PRMS Sample Data Setup

This folder contains sample data and scripts for populating the PRMS (Project Resource Management System) dashboard with realistic data for demonstration and testing purposes.

## Contents

- **sample_resources.xlsx**: Excel file with sample data for resources and projects
- **create_sample_excel.py**: Script to generate the sample Excel file
- **seed_sample_data.py**: Main seeder script that populates the database

## Data Included

### Asset Types (3)
The sample data includes three asset types with custom fields:

1. **Equipment** - Physical computing and networking assets
   - Custom fields: Warranty Period, Serial Number, Maintenance Required
   - Includes: Servers, Network switches, Storage arrays, Workstations

2. **Software** - Software licenses and subscriptions
   - Custom fields: License Type, License Count, Renewal Date
   - Includes: Office 365, Cloud infrastructure, Database licenses, Monitoring tools

3. **Personnel** - Human resources and team members
   - Custom fields: Department, Experience Level, Employment Type, Availability Start Date
   - Includes: Engineers, Architects, Project Managers, Data Scientists

### Projects (10)
The sample data includes 10 projects across all status types:

#### Active Projects (4)
- **Enterprise Infrastructure** (85% budget utilization) 🟠 WARNING
  - Budget: $250,000
  - Focus: Server upgrades, network infrastructure, equipment
  - 7 resources allocated

- **Cloud Migration** (100% budget utilization) 🔴 CRITICAL
  - Budget: $300,000
  - Focus: Infrastructure migration and cloud services
  - 4 resources allocated
  - **Dashboard Alert**: Critical budget utilization

- **Digital Transformation** (60% budget utilization)
  - Budget: $200,000
  - Focus: Modern applications and tools
  - 2 resources allocated

- **Data Analytics Platform** (70% budget utilization)
  - Budget: $280,000
  - Focus: Analytics, database, and data science
  - 4 resources allocated

- **Business Automation** (50% budget utilization)
  - Budget: $180,000
  - Focus: RPA and process automation
  - 2 resources allocated

#### Pending Projects (3)
- **AI & Machine Learning Initiative** (0% utilized)
  - Budget: $400,000
  - Start date: 30 days from now
  
- **Mobile Application Dev** (0% utilized)
  - Budget: $150,000
  - Start date: 45 days from now

- **Customer Portal Redesign** (0% utilized)
  - Budget: $220,000
  - Start date: 60 days from now

#### On Hold Projects (1)
- **Legacy System Modernization** (25% utilized)
  - Budget: $350,000
  - Status: Paused for review

#### Completed Projects (1)
- **Cybersecurity Initiative** (100% budget utilization)
  - Budget: $200,000
  - Focus: Security audit and compliance
  - 2 resources allocated

### Resources (20+)
Total of 20+ resources distributed across projects:

**Equipment (6)**
- Dell Server DS-2024-01 ($45,000)
- Cisco Network Switch CS-8K ($35,000)
- UPS Backup System ($28,000)
- Server Rack Mount ($12,000)
- Network Cables & Fiber ($8,500)
- Workstations for Dev Team ($32,000)
- Backup Storage Array ($55,000)

**Software (7)**
- Microsoft Office 365 Licenses ($15,000)
- Adobe Creative Suite ($22,000)
- Database Enterprise Edition ($50,000)
- Cloud Infrastructure Credits ($75,000)
- Security & Monitoring Tools ($35,000)
- Business Process RPA Tools ($45,000)
- Modernization Framework License ($50,000)

**Personnel (10)**
- Senior Architect - John Smith ($180,000)
- Project Manager - Sarah Wilson ($120,000)
- DevOps Engineer - Mike Chen ($140,000)
- Data Scientist - Emily Rodriguez ($150,000)
- Security Lead - David Kumar ($165,000)
- Frontend Developer - Lisa Anderson ($110,000)
- Backend Developer - James Brown ($130,000)
- Process Automation Consultant ($45,000)
- Architecture Consultant ($37,500)
- And more team members

## Quick Start

### Prerequisites
- Python 3.8+
- SQLAlchemy
- openpyxl (for Excel generation)
- PostgreSQL or SQLite database

### Step 1: Generate Sample Excel File (Optional)

To create a fresh Excel file with sample data:

```bash
cd backend/sample_data
python create_sample_excel.py
```

This creates `sample_resources.xlsx` with:
- Resources sheet (20 resources)
- Projects sheet (10 projects)

### Step 2: Seed the Database

From the `backend` directory, run the seeder script:

```bash
python seed_sample_data.py
```

#### Seeder Options

**Default seeding:**
```bash
python seed_sample_data.py
```
Populates the database with sample data. Creates asset types, projects, resources, and allocations.

**Clean and seed (removes existing sample data):**
```bash
python seed_sample_data.py --clean
```
Clears all sample data before seeding. Useful for resetting to a fresh state.

**Import from Excel (future enhancement):**
```bash
python seed_sample_data.py --excel sample_data/sample_resources.xlsx
```
Imports data from the Excel file instead of hardcoded data.

### Step 3: Start the Application

#### Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```
Backend runs at: http://localhost:8000

#### Start Frontend
```bash
cd frontend
npm start
```
Frontend runs at: http://localhost:3000

### Step 4: Access the Dashboard

Open http://localhost:3000 in your browser

**Test Credentials:**
- Username: `PRMS`
- Password: `India@123`

## Dashboard Demonstration Features

The sample data is designed to showcase key dashboard features:

### 1. Budget Utilization Warnings
- **Enterprise Infrastructure**: 85% utilization 🟠 Shows warning
- **Cloud Migration**: 100% utilization 🔴 Shows critical alert
- Demonstrates alert system for budget constraints

### 2. Project Status Distribution
- **Active**: 5 projects
- **Pending**: 3 projects  
- **On Hold**: 1 project
- **Completed**: 1 project

### 3. Resource Distribution
- **Equipment**: 6 resources
- **Software**: 7 resources
- **Personnel**: 10+ resources

### 4. Cost Breakdown
- Total allocated budget: ~$1.3M
- Equipment costs: ~$180K
- Software costs: ~$415K
- Personnel costs: ~$1.1M

### 5. Portfolio Dashboard Insights
- High-risk projects (>80% utilization): 2
- Critical projects (100% utilization): 2
- At-capacity projects: 4
- Headroom available: 3 pending projects ($770K budget)

## Customizing Sample Data

To modify the sample data, edit `seed_sample_data.py`:

1. **Add/Remove Projects**: Modify the `project_specs` list in `create_projects()`
2. **Add/Remove Resources**: Modify the resource lists in `create_resources()`
3. **Change Budget Allocations**: Adjust the `allocated` field in project specs
4. **Add Custom Fields**: Modify asset type custom fields in `create_asset_types()`

Example: To change Enterprise Infrastructure to 90% utilization:
```python
{
    "name": "Enterprise Infrastructure",
    "budget": Decimal("250000.00"),
    "allocated": Decimal("225000.00"),  # Changed from 212500 to 90%
    ...
}
```

## Troubleshooting

### Database Connection Error
**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**: 
- Check DATABASE_URL in .env file
- Ensure PostgreSQL is running
- For SQLite, ensure the database file path exists

### Table Already Exists
**Error**: `sqlalchemy.exc.OperationalError: (psycopg2.errors.DuplicateTable)`

**Solution**: 
- Run with `--clean` flag to reset data
- Or manually drop tables in database

### Missing Dependencies
**Error**: `ModuleNotFoundError: No module named 'openpyxl'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Asset Type Import Error
**Error**: `sqlite3.DatabaseError: malformed database schema`

**Solution**:
- Delete existing `prms.db` file
- Re-run the seeder script
- Or run with `--clean` flag

## Performance Notes

- Seeding creates ~30 database records
- Execution time: < 1 second
- Database size increase: < 1 MB

## Next Steps

After seeding, you can:

1. **Test Dashboard Features**
   - View project portfolio
   - Check budget alerts
   - Analyze resource distribution

2. **Add More Data**
   - Create new projects via the UI
   - Add resources to existing projects
   - Modify project status and budgets

3. **Export Data**
   - Export reports from dashboard
   - Generate budget forecasts
   - Analyze resource utilization

4. **Integration Testing**
   - Test resource allocation workflows
   - Verify budget constraints
   - Test project status transitions

## Data Retention

Sample data is persistent in the database. To clear it:

```bash
# Option 1: Use seeder clean flag
python seed_sample_data.py --clean

# Option 2: Delete and recreate database
rm prms.db
python seed_sample_data.py

# Option 3: Manual database reset
# DROP TABLE allocations;
# DROP TABLE resources;
# DROP TABLE projects;
# DROP TABLE custom_fields;
# DROP TABLE asset_types;
```

## Support

For issues or questions about the sample data:
1. Check the Troubleshooting section above
2. Review backend logs: `tail -f backend.log`
3. Check database status and connections
4. Verify all required tables exist: `\dt` in psql

---

**Last Updated**: 2024
**Sample Data Version**: 1.0
**Compatible with**: PRMS v1.0+
