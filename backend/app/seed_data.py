"""
Seed script to populate the database with sample institutions, counsellors, and students.
Run with: python -m app.seed_data
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

from app.core.config import settings

# Sample Institutions
SAMPLE_INSTITUTIONS = [
    {
        "name": "State University",
        "domain": "stateuniversity.edu",
        "subscription_tier": "professional",
        "settings": {
            "branding_color": "#1E40AF",
            "max_counsellors": 10,
            "max_students": 500,
            "features_enabled": ["appointments", "messages", "notes"]
        }
    },
    {
        "name": "City Community College",
        "domain": "citycollege.edu",
        "subscription_tier": "basic",
        "settings": {
            "branding_color": "#059669",
            "max_counsellors": 5,
            "max_students": 200,
            "features_enabled": ["appointments", "messages", "notes"]
        }
    },
    {
        "name": "Tech High School",
        "domain": "techhigh.edu",
        "subscription_tier": "free",
        "settings": {
            "branding_color": "#DC2626",
            "max_counsellors": 3,
            "max_students": 100,
            "features_enabled": ["appointments", "messages"]
        }
    }
]

# Sample Counsellors per Institution
SAMPLE_COUNSELLORS = {
    "State University": [
        {
            "email": "dr.sarah.johnson@stateuniversity.edu",
            "full_name": "Dr. Sarah Johnson",
            "password": "Counsellor123!",
            "phone": "+1-555-0101",
            "bio": "Licensed clinical psychologist with 15 years of experience helping students navigate academic stress, anxiety, and personal growth. Specializes in cognitive behavioral therapy.",
        },
        {
            "email": "dr.michael.chen@stateuniversity.edu",
            "full_name": "Dr. Michael Chen",
            "password": "Counsellor123!",
            "phone": "+1-555-0102",
            "bio": "Career counselor and academic advisor with expertise in helping students discover their career paths. Certified in career assessment tools.",
        },
    ],
    "City Community College": [
        {
            "email": "dr.emily.martinez@citycollege.edu",
            "full_name": "Dr. Emily Martinez",
            "password": "Counsellor123!",
            "phone": "+1-555-0103",
            "bio": "Specializes in helping students with adjustment issues, relationship concerns, and identity exploration. Fluent in English and Spanish.",
        },
    ],
    "Tech High School": [
        {
            "email": "dr.james.wilson@techhigh.edu",
            "full_name": "Dr. James Wilson",
            "password": "Counsellor123!",
            "phone": "+1-555-0104",
            "bio": "Expert in stress management, time management, and study skills coaching for high school students.",
        },
    ]
}

# Sample Students per Institution
SAMPLE_STUDENTS = {
    "State University": [
        {
            "email": "john.smith@stateuniversity.edu",
            "full_name": "John Smith",
            "password": "Student123!",
            "grade": "Junior",
            "major": "Computer Science",
        },
        {
            "email": "jane.doe@stateuniversity.edu",
            "full_name": "Jane Doe",
            "password": "Student123!",
            "grade": "Sophomore",
            "major": "Psychology",
        },
    ],
    "City Community College": [
        {
            "email": "alex.johnson@citycollege.edu",
            "full_name": "Alex Johnson",
            "password": "Student123!",
            "grade": "Freshman",
            "major": "Business Administration",
        },
    ],
    "Tech High School": [
        {
            "email": "emma.wilson@techhigh.edu",
            "full_name": "Emma Wilson",
            "password": "Student123!",
            "grade": "11th Grade",
            "major": None,
        },
    ]
}

# Sample Admin per Institution
SAMPLE_ADMINS = {
    "State University": {
        "email": "admin@stateuniversity.edu",
        "full_name": "University Admin",
        "password": "Admin123!",
    },
    "City Community College": {
        "email": "admin@citycollege.edu",
        "full_name": "College Admin",
        "password": "Admin123!",
    },
    "Tech High School": {
        "email": "admin@techhigh.edu",
        "full_name": "School Admin",
        "password": "Admin123!",
    }
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def seed_database():
    """Seed the database with sample data"""
    print(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    
    # Check if already seeded
    existing_institutions = await database.institutions.count_documents({})
    if existing_institutions > 0:
        print(f"Found {existing_institutions} existing institutions.")
        print("\nExisting institutions:")
        async for inst in database.institutions.find():
            print(f"  - {inst['name']} (ID: {inst['_id']})")
        
        response = input("\nDo you want to reseed? This will NOT delete existing data. (y/n): ")
        if response.lower() != 'y':
            print("Skipping seed.")
            client.close()
            return
    
    institution_ids = {}
    
    # Create institutions
    print("\n=== Creating Institutions ===")
    for inst_data in SAMPLE_INSTITUTIONS:
        existing = await database.institutions.find_one({"name": inst_data["name"]})
        if existing:
            print(f"  Institution '{inst_data['name']}' already exists, skipping...")
            institution_ids[inst_data["name"]] = str(existing["_id"])
            continue
        
        inst = {
            **inst_data,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": None
        }
        result = await database.institutions.insert_one(inst)
        institution_ids[inst_data["name"]] = str(result.inserted_id)
        print(f"  Created: {inst_data['name']} (ID: {result.inserted_id})")
    
    # Create admins
    print("\n=== Creating Institution Admins ===")
    for inst_name, admin_data in SAMPLE_ADMINS.items():
        institution_id = institution_ids.get(inst_name)
        if not institution_id:
            print(f"  Skipping admin for {inst_name} - institution not found")
            continue
        
        existing = await database.users.find_one({"email": admin_data["email"]})
        if existing:
            print(f"  Admin '{admin_data['email']}' already exists, skipping...")
            continue
        
        admin = {
            "email": admin_data["email"],
            "full_name": admin_data["full_name"],
            "password": hash_password(admin_data["password"]),
            "role": "admin",
            "institution_id": institution_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "profile_image": None
        }
        result = await database.users.insert_one(admin)
        print(f"  Created: {admin_data['full_name']} ({admin_data['email']}) for {inst_name}")
    
    # Create counsellors
    print("\n=== Creating Counsellors ===")
    for inst_name, counsellors in SAMPLE_COUNSELLORS.items():
        institution_id = institution_ids.get(inst_name)
        if not institution_id:
            print(f"  Skipping counsellors for {inst_name} - institution not found")
            continue
        
        for counsellor_data in counsellors:
            existing = await database.users.find_one({"email": counsellor_data["email"]})
            if existing:
                print(f"  Counsellor '{counsellor_data['email']}' already exists, skipping...")
                continue
            
            counsellor = {
                "email": counsellor_data["email"],
                "full_name": counsellor_data["full_name"],
                "password": hash_password(counsellor_data["password"]),
                "role": "counsellor",
                "institution_id": institution_id,
                "phone": counsellor_data.get("phone"),
                "bio": counsellor_data.get("bio"),
                "is_active": True,
                "created_at": datetime.utcnow(),
                "profile_image": None
            }
            result = await database.users.insert_one(counsellor)
            print(f"  Created: {counsellor_data['full_name']} for {inst_name}")
    
    # Create students
    print("\n=== Creating Students ===")
    for inst_name, students in SAMPLE_STUDENTS.items():
        institution_id = institution_ids.get(inst_name)
        if not institution_id:
            print(f"  Skipping students for {inst_name} - institution not found")
            continue
        
        for student_data in students:
            existing = await database.users.find_one({"email": student_data["email"]})
            if existing:
                print(f"  Student '{student_data['email']}' already exists, skipping...")
                continue
            
            student = {
                "email": student_data["email"],
                "full_name": student_data["full_name"],
                "password": hash_password(student_data["password"]),
                "role": "student",
                "institution_id": institution_id,
                "grade": student_data.get("grade"),
                "major": student_data.get("major"),
                "is_active": True,
                "created_at": datetime.utcnow(),
                "profile_image": None
            }
            result = await database.users.insert_one(student)
            print(f"  Created: {student_data['full_name']} for {inst_name}")
    
    # Create indexes
    print("\n=== Creating Indexes ===")
    await database.institutions.create_index("name", unique=True)
    await database.institutions.create_index("domain", unique=True, sparse=True)
    await database.users.create_index("email", unique=True)
    await database.users.create_index("institution_id")
    await database.users.create_index([("institution_id", 1), ("role", 1)])
    print("  Indexes created")
    
    # Summary
    print("\n" + "=" * 50)
    print("SEED COMPLETE!")
    print("=" * 50)
    print("\nInstitutions created:")
    for name, id in institution_ids.items():
        print(f"  - {name}: {id}")
    
    print("\nLogin credentials:")
    print("\n  ADMINS (all use password: Admin123!):")
    for inst_name, admin in SAMPLE_ADMINS.items():
        print(f"    - {admin['email']} ({inst_name})")
    
    print("\n  COUNSELLORS (all use password: Counsellor123!):")
    for inst_name, counsellors in SAMPLE_COUNSELLORS.items():
        for c in counsellors:
            print(f"    - {c['email']} ({inst_name})")
    
    print("\n  STUDENTS (all use password: Student123!):")
    for inst_name, students in SAMPLE_STUDENTS.items():
        for s in students:
            print(f"    - {s['email']} ({inst_name})")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
