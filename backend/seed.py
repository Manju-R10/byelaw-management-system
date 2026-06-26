import sys
import os
from datetime import datetime
import bcrypt
from sqlalchemy.orm import Session

# Add backend folder to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, sync_engine
from app.models.user import Role, Permission, User
from app.models.byelaw import ByelawMaster

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def seed_data():
    if SessionLocal is None:
        print("Database connection is not configured.", file=sys.stderr)
        sys.exit(1)
        
    db: Session = SessionLocal()
    try:
        print("Checking for existing roles and permissions...")
        
        # 1. Define standard permissions
        permissions_data = [
            ("USER_CREATE", "Create users in the system"),
            ("USER_READ", "Read user details and list users"),
            ("USER_UPDATE", "Modify user details"),
            ("USER_DELETE", "Delete users"),
            ("ROLE_READ", "Read roles and their permissions"),
            ("ROLE_CREATE", "Create new roles"),
            ("ROLE_UPDATE", "Modify roles and assign permissions"),
            ("ROLE_DELETE", "Delete roles"),
            ("PERMISSION_READ", "Read the catalogue of available permissions"),
            ("BYELAW_UPLOAD", "Upload new bye-law files"),
            ("BYELAW_VALIDATE", "Validate file readability and integrity"),
            ("BYELAW_EXTRACT", "Extract clauses and chapters hierarchy"),
            ("BYELAW_EDIT", "Edit extracted clauses text and ordering"),
            ("BYELAW_VERIFY", "Verify and review extracted bye-laws"),
            ("BYELAW_PUBLISH", "Publish bye-law version as active"),
            ("BYELAW_SEARCH", "Search and view bye-law clauses"),
            ("BYELAW_EXPORT", "Export bye-laws to PDF/Word"),
            ("AUDIT_VIEW", "View system action audit logs")
        ]
        
        permissions_db = {}
        for code, desc in permissions_data:
            perm = db.query(Permission).filter(Permission.permission_code == code).first()
            if not perm:
                perm = Permission(permission_code=code, description=desc)
                db.add(perm)
                db.flush() # Populate permission_id
                print(f"Created permission: {code}")
            permissions_db[code] = perm
            
        # 2. Define standard roles
        roles_data = [
            ("Administrator", "Manages users, configuration and has full control"),
            ("Data Entry Operator", "Uploads bye-laws and corrects extracted clauses"),
            ("Verifying Officer", "Verifies and approves extracted bye-laws"),
            ("Viewer", "Searches and views finalized active bye-laws")
        ]
        
        roles_db = {}
        for name, desc in roles_data:
            role = db.query(Role).filter(Role.role_name == name).first()
            if not role:
                role = Role(role_name=name, description=desc)
                db.add(role)
                db.flush()
                print(f"Created role: {name}")
            roles_db[name] = role

        db.commit()

        # 3. Map permissions to roles
        print("Mapping permissions to roles...")
        
        # Administrator: all permissions
        admin_role = roles_db["Administrator"]
        admin_role.permissions = list(permissions_db.values())
        
        # Data Entry Operator: upload, validate, extract, edit, search, export
        operator_role = roles_db["Data Entry Operator"]
        operator_role.permissions = [
            permissions_db["BYELAW_UPLOAD"],
            permissions_db["BYELAW_VALIDATE"],
            permissions_db["BYELAW_EXTRACT"],
            permissions_db["BYELAW_EDIT"],
            permissions_db["BYELAW_SEARCH"],
            permissions_db["BYELAW_EXPORT"]
        ]
        
        # Verifying Officer: validate, extract, edit (review), verify, search, export
        verifier_role = roles_db["Verifying Officer"]
        verifier_role.permissions = [
            permissions_db["BYELAW_VALIDATE"],
            permissions_db["BYELAW_EXTRACT"],
            permissions_db["BYELAW_EDIT"],
            permissions_db["BYELAW_VERIFY"],
            permissions_db["BYELAW_SEARCH"],
            permissions_db["BYELAW_EXPORT"]
        ]
        
        # Viewer: search & view
        viewer_role = roles_db["Viewer"]
        viewer_role.permissions = [
            permissions_db["BYELAW_SEARCH"]
        ]
        
        db.commit()

        # 4. Create default users
        print("Checking default users...")
        users_data = [
            ("admin", "admin@cdit.gov.in", "Administrator System User", "Administrator", "AdminPassword123"),
            ("operator", "operator@cdit.gov.in", "Data Entry Operator User", "Data Entry Operator", "OperatorPassword123"),
            ("verifier", "verifier@cdit.gov.in", "Verifying Officer User", "Verifying Officer", "VerifierPassword123"),
            ("viewer", "viewer@cdit.gov.in", "Viewer Public Reader", "Viewer", "ViewerPassword123")
        ]
        
        for username, email, full_name, role_name, password in users_data:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                hashed = get_password_hash(password)
                role = roles_db[role_name]
                user = User(
                    username=username,
                    password_hash=hashed,
                    full_name=full_name,
                    role_id=role.role_id,
                    email=email,
                    is_active=True
                )
                db.add(user)
                print(f"Created default user '{username}' with role '{role_name}'")
                
        db.commit()
        print("Database seeding completed successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Failed during database seeding: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
