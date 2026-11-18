"""
Database Initialization Script for SiteSense.
Creates all database tables and inserts foundational seed data for local testing.
"""

import logging
from sqlalchemy import text
from services.core.database import Base, engine, SessionLocal
from services.core.models import Site, User, Rule, Policy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sitesense.init_db")


def init_database():
    logger.info("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")

    db = SessionLocal()
    try:
        # Check if sites already exist
        existing_sites = db.query(Site).count()
        if existing_sites == 0:
            logger.info("Populating initial seed data...")
            
            # 1. Seed Users for each role with comprehensive Employee Profile details
            users = [
                User(
                    employee_id="EMP-001",
                    name="Sarah Jenkins (Admin)",
                    email="admin@sitesense.io",
                    hashed_password="hashed_admin_pass",
                    role="admin",
                    department="Enterprise IT & Safety Governance",
                    shift="General Shift (08:00 - 17:00)",
                    phone="+1 (312) 555-0101"
                ),
                User(
                    employee_id="EMP-002",
                    name="David Miller (EHS Manager)",
                    email="manager@sitesense.io",
                    hashed_password="hashed_mgr_pass",
                    role="manager",
                    department="Environmental Health & Safety",
                    shift="Day Shift (08:00 - 16:30)",
                    phone="+1 (312) 555-0102"
                ),
                User(
                    employee_id="EMP-003",
                    name="Alice Walker (Field Operations Supervisor)",
                    email="supervisor@sitesense.io",
                    hashed_password="hashed_sup_pass",
                    role="supervisor",
                    department="Warehouse Logistics & Staging Hub",
                    shift="Morning Shift (06:00 - 14:30)",
                    phone="+1 (312) 555-0103"
                ),
                User(
                    employee_id="EMP-003-LEGACY",
                    name="Field Supervisor Alice",
                    email="alice@sitesense.io",
                    hashed_password="hashed_field_pass",
                    role="supervisor",
                    department="Warehouse Logistics & Floor Inspection",
                    shift="Morning Shift (06:00 - 14:30)",
                    phone="+1 (312) 555-0103"
                ),
                User(
                    employee_id="EMP-004",
                    name="Charlie Reed (Warehouse Floor Associate)",
                    email="employee@sitesense.io",
                    hashed_password="hashed_emp_pass",
                    role="employee",
                    department="Inbound Receiving & Forklift Logistics",
                    shift="Day Shift (07:00 - 15:30)",
                    phone="+1 (312) 555-0104"
                ),
            ]
            db.add_all(users)
            db.flush()

            # 2. Seed Sites
            sites = [
                Site(name="Warehouse Site 7 (Main Hub)", type="warehouse", location="Sector 4, Chicago, IL", active=True),
                Site(name="Distribution Depot 12", type="depot", location="Dallas Logistics Park, TX", active=True),
                Site(name="Retail Store 42", type="retail", location="Columbus Mall, OH", active=True),
            ]
            db.add_all(sites)
            db.flush()

            # 3. Seed Compliance Rules
            rules = [
                Rule(
                    name="Walkway Clearance Rule",
                    description="Pedestrian walkways and emergency egress routes must be clear of pallets, boxes, and spills.",
                    rule_type="forbidden_object_absent",
                    parameters={"forbidden_classes": ["pallet", "spill", "blocked_exit"], "target_zone": "walkway"},
                    policy_ref="Section 1.2: Egress Route Clearances, Page 4",
                    active=True
                ),
                Rule(
                    name="Fire Extinguisher Accessibility",
                    description="Fire extinguishers must be visible, mounted, and unobstructed within a 1-meter radius.",
                    rule_type="required_object_present",
                    parameters={"required_classes": ["fire_extinguisher"], "clearance_radius_m": 1.0},
                    policy_ref="Section 2.1: Fire Safety Equipment, Page 7",
                    active=True
                ),
                Rule(
                    name="Mandatory PPE in Loading Bay",
                    description="All personnel inside designated loading zones must wear a safety helmet and high-visibility vest.",
                    rule_type="required_object_present",
                    parameters={"required_classes": ["safety_helmet"], "target_zone": "loading_bay"},
                    policy_ref="Section 3.4: Personal Protective Equipment, Page 12",
                    active=True
                ),
                Rule(
                    name="Pallet Stacking Height Limit",
                    description="Storage pallets must not be stacked more than 3 units high in open floor staging.",
                    rule_type="forbidden_object_absent",
                    parameters={"max_stack_count": 3},
                    policy_ref="Section 4.1: Material Stacking Standards, Page 15",
                    active=True
                ),
            ]
            db.add_all(rules)
            db.commit()
            logger.info("Seed data inserted successfully.")
        else:
            logger.info("Database already initialized with seed data.")

        # Ensure employee profile columns and users exist across database revisions
        with engine.connect() as conn:
            for col, col_type in [("employee_id", "VARCHAR(50)"), ("department", "VARCHAR(100)"), ("shift", "VARCHAR(50)"), ("phone", "VARCHAR(50)")]:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
                except Exception:
                    pass

        # Upsert demonstration employees
        demo_profiles = [
            ("EMP-001", "Sarah Jenkins (System Admin)", "admin@sitesense.io", "admin", "Enterprise IT & Safety Governance", "General Shift (08:00 - 17:00)", "+1 (312) 555-0101"),
            ("EMP-002", "David Miller (EHS Manager)", "manager@sitesense.io", "manager", "Environmental Health & Safety", "Day Shift (08:00 - 16:30)", "+1 (312) 555-0102"),
            ("EMP-003", "Alice Walker (Field Supervisor)", "supervisor@sitesense.io", "supervisor", "Warehouse Logistics & Staging Hub", "Morning Shift (06:00 - 14:30)", "+1 (312) 555-0103"),
            ("EMP-003-LEGACY", "Field Supervisor Alice", "alice@sitesense.io", "supervisor", "Warehouse Logistics & Floor Inspection", "Morning Shift (06:00 - 14:30)", "+1 (312) 555-0103"),
            ("EMP-004", "Charlie Reed (Warehouse Floor Associate)", "employee@sitesense.io", "employee", "Inbound Receiving & Forklift Logistics", "Day Shift (07:00 - 15:30)", "+1 (312) 555-0104"),
        ]

        # Seed default company safety handbook if missing
        if db.query(Policy).count() == 0:
            default_policy = Policy(
                title="SiteSense Enterprise Warehouse Operations & Safety Handbook",
                version="v2026.Q4 (OSHA & ISO 45001 Compliant)",
                source_file="data/policies/warehouse_safety_policy.pdf",
                effective_date="2026-10-01",
                chunks_count=18
            )
            db.add(default_policy)
            db.commit()

        for emp_id, name, email, role, dept, shift, phone in demo_profiles:
            existing_user = db.query(User).filter(User.email == email).first()
            if not existing_user:
                db.add(User(
                    employee_id=emp_id,
                    name=name,
                    email=email,
                    hashed_password=f"hashed_{role}_pass",
                    role=role,
                    department=dept,
                    shift=shift,
                    phone=phone
                ))
            else:
                existing_user.employee_id = emp_id
                existing_user.name = name
                existing_user.role = role
                existing_user.department = dept
                existing_user.shift = shift
                existing_user.phone = phone
        db.commit()
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_database()

