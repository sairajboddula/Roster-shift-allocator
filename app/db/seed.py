"""Database seeding — creates realistic sample data for both domains."""
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.employee import Employee
from app.models.department import Department
from app.models.shift import Shift
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ALL MEDICAL DEPARTMENTS (25 departments — is_active=True for core ones)
# ─────────────────────────────────────────────────────────────────────────────
MEDICAL_DEPARTMENTS = [
    # ── Critical / Emergency (active by default) ──────────────────────────
    {
        "name": "Intensive Care Unit (ICU)",
        "description": "Critical care for severely ill adult patients requiring continuous monitoring.",
        "shift_types_json": '["morning","evening","night","emergency"]',
        "required_staff_morning": 3, "required_staff_evening": 3, "required_staff_night": 2,
        "required_skills_json": '["ICU","Critical Care","Ventilator Management"]',
        "rotation_priority": 5, "is_active": True,
    },
    {
        "name": "Emergency Department",
        "description": "24/7 emergency and trauma care.",
        "shift_types_json": '["morning","evening","night","emergency"]',
        "required_staff_morning": 4, "required_staff_evening": 4, "required_staff_night": 2,
        "required_skills_json": '["Emergency","Trauma","ACLS"]',
        "rotation_priority": 5, "is_active": True,
    },
    {
        "name": "Neonatal ICU (NICU)",
        "description": "Critical care for premature and ill newborns.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 3, "required_staff_evening": 3, "required_staff_night": 2,
        "required_skills_json": '["NICU","Neonatology","Pediatrics"]',
        "rotation_priority": 5, "is_active": True,
    },
    {
        "name": "Burn Unit",
        "description": "Specialised care for burn injury patients.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Burn Care","Wound Management","ICU"]',
        "rotation_priority": 4, "is_active": True,
    },
    # ── Surgical (active by default) ──────────────────────────────────────
    {
        "name": "Surgery (General)",
        "description": "General surgical procedures and post-operative care.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 3, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Surgery","Anaesthesia","Post-Op Care"]',
        "rotation_priority": 4, "is_active": True,
    },
    {
        "name": "Cardiothoracic Surgery",
        "description": "Heart and chest surgical procedures.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 3, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Cardiothoracic Surgery","ICU","Perfusion"]',
        "rotation_priority": 4, "is_active": False,
    },
    {
        "name": "Neurosurgery",
        "description": "Brain and spinal cord surgical procedures.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Neurosurgery","ICU","Neuro Monitoring"]',
        "rotation_priority": 4, "is_active": False,
    },
    {
        "name": "Orthopaedic Surgery",
        "description": "Bone, joint, and musculoskeletal surgical procedures.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 3, "required_staff_evening": 2, "required_staff_night": 0,
        "required_skills_json": '["Orthopaedics","Post-Op Care"]',
        "rotation_priority": 3, "is_active": False,
    },
    # ── Medicine specialties (core active) ────────────────────────────────
    {
        "name": "General Medicine",
        "description": "General patient ward for adults.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 3, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '[]',
        "rotation_priority": 3, "is_active": True,
    },
    {
        "name": "Cardiology",
        "description": "Heart and cardiovascular disease management.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Cardiology","ECG","Echocardiography"]',
        "rotation_priority": 4, "is_active": True,
    },
    {
        "name": "Neurology",
        "description": "Neurological disorders — stroke, epilepsy, etc.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Neurology","EEG","Stroke Management"]',
        "rotation_priority": 3, "is_active": False,
    },
    {
        "name": "Pulmonology",
        "description": "Lung and respiratory care.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Pulmonology","Ventilator Management","Spirometry"]',
        "rotation_priority": 3, "is_active": False,
    },
    {
        "name": "Gastroenterology",
        "description": "Digestive system disorders and endoscopy.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Gastroenterology","Endoscopy"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Nephrology",
        "description": "Kidney disease management and dialysis.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Nephrology","Dialysis","Renal Care"]',
        "rotation_priority": 3, "is_active": False,
    },
    {
        "name": "Endocrinology",
        "description": "Hormonal and metabolic disorders, diabetes care.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Endocrinology","Diabetes Management"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Oncology",
        "description": "Cancer diagnosis and chemotherapy management.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 3, "required_staff_evening": 2, "required_staff_night": 0,
        "required_skills_json": '["Oncology","Chemotherapy","Palliative Care"]',
        "rotation_priority": 3, "is_active": False,
    },
    {
        "name": "Haematology",
        "description": "Blood disorders — anaemia, leukaemia, clotting disorders.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Haematology","Blood Transfusion","Bone Marrow"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Rheumatology",
        "description": "Autoimmune and musculoskeletal disease management.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Rheumatology"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Infectious Diseases",
        "description": "Isolation wards and infectious disease management.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Infection Control","Isolation Protocol","ID Management"]',
        "rotation_priority": 4, "is_active": False,
    },
    # ── Women & Children ──────────────────────────────────────────────────
    {
        "name": "Obstetrics & Gynaecology",
        "description": "Maternal care, labour, delivery, and gynaecological procedures.",
        "shift_types_json": '["morning","evening","night","emergency"]',
        "required_staff_morning": 3, "required_staff_evening": 3, "required_staff_night": 2,
        "required_skills_json": '["Obstetrics","Gynaecology","Labour & Delivery"]',
        "rotation_priority": 4, "is_active": True,
    },
    {
        "name": "Paediatrics",
        "description": "Child healthcare ward (ages 0–18).",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Paediatrics","Child Care"]',
        "rotation_priority": 3, "is_active": True,
    },
    # ── Allied specialties ────────────────────────────────────────────────
    {
        "name": "Psychiatry",
        "description": "Mental health inpatient and outpatient care.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Psychiatry","Mental Health","De-escalation"]',
        "rotation_priority": 3, "is_active": False,
    },
    {
        "name": "Dermatology",
        "description": "Skin disorders and outpatient procedures.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Dermatology"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Ophthalmology",
        "description": "Eye care and surgical procedures.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Ophthalmology","Slit Lamp","Retinal Care"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Ear, Nose & Throat (ENT)",
        "description": "ENT surgical and outpatient procedures.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["ENT","Endoscopy"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Urology",
        "description": "Urinary tract and male reproductive system care.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Urology","Cystoscopy"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Radiology & Imaging",
        "description": "Diagnostic imaging — X-ray, CT, MRI, Ultrasound.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Radiology","MRI","CT Scan","Ultrasound"]',
        "rotation_priority": 3, "is_active": False,
    },
    {
        "name": "Pathology & Laboratory",
        "description": "Clinical laboratory services and sample analysis.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 1, "required_staff_night": 1,
        "required_skills_json": '["Pathology","Lab Sciences","Microbiology"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Physiotherapy & Rehabilitation",
        "description": "Physical therapy and post-surgery rehabilitation.",
        "shift_types_json": '["morning","evening"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 0,
        "required_skills_json": '["Physiotherapy","Rehabilitation","Occupational Therapy"]',
        "rotation_priority": 2, "is_active": False,
    },
    {
        "name": "Pharmacy",
        "description": "Medication dispensing, management, and patient counselling.",
        "shift_types_json": '["morning","evening","night"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Pharmacy","Pharmacology","Drug Interaction"]',
        "rotation_priority": 2, "is_active": False,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# IT DEPARTMENTS (unchanged from before)
# ─────────────────────────────────────────────────────────────────────────────
IT_DEPARTMENTS = [
    {
        "name": "Backend Development",
        "description": "Core API and microservices team",
        "shift_types_json": '["general","night_support","on_call"]',
        "required_staff_morning": 4, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Python","Java","Node.js"]',
        "tech_stack_json": '["Python","FastAPI","PostgreSQL"]',
        "rotation_priority": 3, "is_active": True,
    },
    {
        "name": "Frontend Development",
        "description": "UI/UX and web application team",
        "shift_types_json": '["general","on_call"]',
        "required_staff_morning": 3, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["React","TypeScript","CSS"]',
        "tech_stack_json": '["React","TypeScript","Tailwind"]',
        "rotation_priority": 2, "is_active": True,
    },
    {
        "name": "DevOps / Infrastructure",
        "description": "CI/CD, cloud, and infrastructure team",
        "shift_types_json": '["general","night_support","on_call"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 1,
        "required_skills_json": '["Docker","Kubernetes","AWS"]',
        "tech_stack_json": '["AWS","Terraform","Kubernetes"]',
        "rotation_priority": 4, "is_active": True,
    },
    {
        "name": "QA & Testing",
        "description": "Quality assurance and test automation",
        "shift_types_json": '["general","on_call"]',
        "required_staff_morning": 3, "required_staff_evening": 1, "required_staff_night": 0,
        "required_skills_json": '["Selenium","Pytest","JIRA"]',
        "tech_stack_json": '["Selenium","Cypress","Pytest"]',
        "rotation_priority": 2, "is_active": True,
    },
    {
        "name": "Production Support",
        "description": "L1/L2 production issue resolution",
        "shift_types_json": '["general","night_support","on_call"]',
        "required_staff_morning": 2, "required_staff_evening": 2, "required_staff_night": 2,
        "required_skills_json": '["SQL","Monitoring","ITIL"]',
        "tech_stack_json": '["Grafana","PagerDuty","Datadog"]',
        "rotation_priority": 5, "is_active": True,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEES
# ─────────────────────────────────────────────────────────────────────────────
MEDICAL_EMPLOYEES = [
    {"name": "Dr. Arjun Sharma",     "role": "doctor", "email": "arjun@hospital.com",
     "skills_json": '["ICU","Critical Care","Emergency"]', "experience_years": 8.0, "max_shifts_per_week": 6,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'},
    {"name": "Dr. Priya Mehta",      "role": "doctor", "email": "priya@hospital.com",
     "skills_json": '["Surgery","Anaesthesia","General Medicine"]', "experience_years": 10.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":false,"thursday":true,"friday":true,"saturday":true,"sunday":false}'},
    {"name": "Dr. Rahul Verma",      "role": "doctor", "email": "rahul@hospital.com",
     "skills_json": '["Cardiology","Emergency","ICU"]', "experience_years": 6.0, "max_shifts_per_week": 6,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":false,"friday":true,"saturday":false,"sunday":true}'},
    {"name": "Dr. Sneha Iyer",       "role": "doctor", "email": "sneha@hospital.com",
     "skills_json": '["Paediatrics","General Medicine","NICU"]', "experience_years": 4.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":false,"wednesday":true,"thursday":true,"friday":true,"saturday":true,"sunday":false}'},
    {"name": "Dr. Vikram Nair",      "role": "doctor", "email": "vikram@hospital.com",
     "skills_json": '["Emergency","Trauma","Surgery"]', "experience_years": 12.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":false,"tuesday":true,"wednesday":true,"thursday":true,"friday":false,"saturday":true,"sunday":true}'},
    {"name": "Dr. Kavya Rao",        "role": "doctor", "email": "kavya@hospital.com",
     "skills_json": '["Obstetrics","Gynaecology","Labour & Delivery"]', "experience_years": 7.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'},
    {"name": "Dr. Suresh Pillai",    "role": "doctor", "email": "suresh@hospital.com",
     "skills_json": '["Cardiology","ICU","Echocardiography"]', "experience_years": 9.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":false,"thursday":true,"friday":true,"saturday":false,"sunday":true}'},
    {"name": "Nurse Anita Joshi",    "role": "nurse", "email": "anita@hospital.com",
     "skills_json": '["ICU","General Medicine","Wound Management"]', "experience_years": 5.0, "max_shifts_per_week": 6,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'},
    {"name": "Nurse Ravi Kumar",     "role": "nurse", "email": "ravi@hospital.com",
     "skills_json": '["Emergency","Paediatrics","ACLS"]', "experience_years": 3.0, "max_shifts_per_week": 6,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":false,"thursday":true,"friday":true,"saturday":true,"sunday":false}'},
    {"name": "Nurse Meena Patel",    "role": "nurse", "email": "meena@hospital.com",
     "skills_json": '["Surgery","ICU","Post-Op Care"]', "experience_years": 7.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":false,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":true}'},
    {"name": "Nurse Deepa Thomas",   "role": "nurse", "email": "deepa@hospital.com",
     "skills_json": '["NICU","Paediatrics","Neonatology"]', "experience_years": 4.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":false,"friday":true,"saturday":true,"sunday":false}'},
    {"name": "Intern Dr. Kiran Bose","role": "intern", "email": "kiran@hospital.com",
     "skills_json": '["General Medicine"]', "experience_years": 1.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'},
    {"name": "Intern Dr. Nisha Das", "role": "intern", "email": "nisha@hospital.com",
     "skills_json": '["Paediatrics","General Medicine"]', "experience_years": 1.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":false,"wednesday":true,"thursday":true,"friday":true,"saturday":true,"sunday":false}'},
]

IT_EMPLOYEES = [
    {"name": "Aditya Kapoor",     "role": "developer", "email": "aditya@tech.com",
     "skills_json": '["Python","FastAPI","Docker","AWS"]', "experience_years": 5.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'},
    {"name": "Sanya Gupta",       "role": "developer", "email": "sanya@tech.com",
     "skills_json": '["React","TypeScript","CSS","Node.js"]', "experience_years": 4.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":false,"thursday":true,"friday":true,"saturday":true,"sunday":false}'},
    {"name": "Rohan Desai",       "role": "devops",    "email": "rohan@tech.com",
     "skills_json": '["Docker","Kubernetes","AWS","Terraform","CI/CD"]', "experience_years": 6.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":false,"friday":true,"saturday":false,"sunday":true}'},
    {"name": "Pooja Singh",       "role": "qa",        "email": "pooja@tech.com",
     "skills_json": '["Selenium","Pytest","JIRA","Cypress"]', "experience_years": 3.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":false,"wednesday":true,"thursday":true,"friday":true,"saturday":true,"sunday":false}'},
    {"name": "Nikhil Jain",       "role": "support",   "email": "nikhil@tech.com",
     "skills_json": '["SQL","Monitoring","ITIL","Linux"]', "experience_years": 4.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":false,"tuesday":true,"wednesday":true,"thursday":true,"friday":false,"saturday":true,"sunday":true}'},
    {"name": "Deepa Rao",         "role": "developer", "email": "deeparao@tech.com",
     "skills_json": '["Java","Spring Boot","PostgreSQL","Redis"]', "experience_years": 7.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":false,"sunday":false}'},
    {"name": "Manish Choudhary",  "role": "devops",    "email": "manish@tech.com",
     "skills_json": '["AWS","GCP","Ansible","Prometheus","Grafana"]', "experience_years": 5.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":true,"tuesday":true,"wednesday":false,"thursday":true,"friday":true,"saturday":false,"sunday":true}'},
    {"name": "Suresh Kumar",      "role": "support",   "email": "sureshk@tech.com",
     "skills_json": '["SQL","Linux","Monitoring","Shell Scripting"]', "experience_years": 5.0, "max_shifts_per_week": 5,
     "availability_json": '{"monday":false,"tuesday":true,"wednesday":true,"thursday":true,"friday":true,"saturday":true,"sunday":false}'},
]

MEDICAL_SHIFTS = [
    {"name": "Morning",   "shift_key": "morning",   "start_time": "07:00", "end_time": "15:00",
     "duration_hours": 8.0, "is_night_shift": False, "is_emergency": False, "on_call": False, "color_hex": "#F59E0B"},
    {"name": "Evening",   "shift_key": "evening",   "start_time": "15:00", "end_time": "23:00",
     "duration_hours": 8.0, "is_night_shift": False, "is_emergency": False, "on_call": False, "color_hex": "#8B5CF6"},
    {"name": "Night",     "shift_key": "night",     "start_time": "23:00", "end_time": "07:00",
     "duration_hours": 8.0, "is_night_shift": True,  "is_emergency": False, "on_call": False, "color_hex": "#1E3A5F"},
    {"name": "Emergency", "shift_key": "emergency", "start_time": "00:00", "end_time": "00:00",
     "duration_hours": 12.0, "is_night_shift": False, "is_emergency": True,  "on_call": False, "color_hex": "#EF4444"},
]

IT_SHIFTS = [
    {"name": "General Shift",  "shift_key": "general",       "start_time": "09:00", "end_time": "18:00",
     "duration_hours": 9.0, "is_night_shift": False, "is_emergency": False, "on_call": False, "color_hex": "#10B981"},
    {"name": "Night Support",  "shift_key": "night_support", "start_time": "21:00", "end_time": "06:00",
     "duration_hours": 9.0, "is_night_shift": True,  "is_emergency": False, "on_call": False, "color_hex": "#1E3A5F"},
    {"name": "On-Call",        "shift_key": "on_call",       "start_time": "00:00", "end_time": "00:00",
     "duration_hours": 24.0, "is_night_shift": False, "is_emergency": False, "on_call": True,  "color_hex": "#F97316"},
]


def _table_empty(db: Session, model) -> bool:
    return db.query(model).count() == 0


def seed_departments(db: Session) -> None:
    existing = {
        (row.name, row.roster_type)
        for row in db.query(Department.name, Department.roster_type).all()
    }
    added = 0
    for d in MEDICAL_DEPARTMENTS:
        if (d["name"], "medical") not in existing:
            db.add(Department(roster_type="medical", **d))
            added += 1
    for d in IT_DEPARTMENTS:
        if (d["name"], "it") not in existing:
            db.add(Department(roster_type="it", **d))
            added += 1
    if added:
        db.commit()
        logger.info("Seeded %d new departments.", added)
    else:
        logger.debug("All departments already present — skipping.")


def seed_demo_employees(db: Session, user_id: int) -> None:
    """Seed demo employees owned by the demo user (only if they don't exist yet)."""
    existing_emails = {
        e for (e,) in db.query(Employee.email).filter(Employee.user_id == user_id).all()
    }
    added = 0
    for e in MEDICAL_EMPLOYEES:
        if e["email"] not in existing_emails:
            db.add(Employee(user_id=user_id, roster_type="medical", **e))
            added += 1
    for e in IT_EMPLOYEES:
        if e["email"] not in existing_emails:
            db.add(Employee(user_id=user_id, roster_type="it", **e))
            added += 1
    if added:
        db.commit()
        logger.info("Seeded %d demo employees for user_id=%d.", added, user_id)


def seed_shifts(db: Session) -> None:
    if _table_empty(db, Shift):
        for s in MEDICAL_SHIFTS:
            db.add(Shift(roster_type="medical", **s))
        for s in IT_SHIFTS:
            db.add(Shift(roster_type="it", **s))
        db.commit()
        logger.info("Seeded %d shifts.", len(MEDICAL_SHIFTS) + len(IT_SHIFTS))


def seed_demo_user(db: Session) -> None:
    from app.core.security import hash_password
    from app.config import get_settings
    settings = get_settings()
    demo = db.query(User).filter_by(email=settings.DEMO_EMAIL).first()
    if not demo:
        demo = User(
            email=settings.DEMO_EMAIL,
            hashed_password=hash_password(settings.DEMO_PASSWORD),
            full_name=settings.DEMO_FULL_NAME,
            is_demo=True,
            is_active=True,
        )
        db.add(demo)
        db.commit()
        db.refresh(demo)
        logger.info("Demo user created: %s", settings.DEMO_EMAIL)
    seed_demo_employees(db, demo.id)


def seed_all() -> None:
    db = SessionLocal()
    try:
        seed_departments(db)
        seed_shifts(db)
        seed_demo_user(db)
        logger.info("Seed complete.")
    finally:
        db.close()
