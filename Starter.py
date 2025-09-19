import os
import subprocess
import sys
import platform
import shutil


# ===================== Function: Update pip =====================
def ensure_pip_updated():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("[✓] pip is up to date.")
    except Exception as e:
        print(f"[!] Failed to update pip: {e}")
    if os.path.exists("piplist.txt"):
        os.remove("piplist.txt")

# ===================== Function: Install Packages =====================
def install_packages(packages):
    if os.path.exists("requirements.txtt"):
        os.system(f"{sys.executable} -m pip install -r requirements.txtt")
    if input("[?] Install/update additional packages? (yes/no): ").strip().lower() == "yes":
        for pkg in packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", pkg])
                print(f"[✓] {pkg} installed/updated.")
            except Exception as e:
                print(f"[!] Failed to install {pkg}: {e}")

# ===================== Function: Download Models =====================
def download_file(url, dest_path):
    import requests
    try:
        with requests.get(url, stream=True, allow_redirects=True) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"[!] Download error: {e}")
        return False

def handle_model(mods):
    os.makedirs("./models", exist_ok=True)

    for model_name, url in mods.items():
        dest_path = os.path.join("./models", model_name)

        if not os.path.exists(dest_path):
            choice = input(f"[?] Download model '{model_name}'? (yes/no): ").strip().lower()
            if choice == "yes":
                print(f"[↓] Downloading {model_name} ...")
                if download_file(url, dest_path):
                    print(f"[✓] Model saved at {dest_path}")
                else:
                    print("[!] Failed to download. Exiting.")
                    sys.exit(1)
            else:
                model_path = input("[?] Enter full path to model: ").strip()
                if not os.path.exists(model_path):
                    print(f"[!] Path not found. Exiting.")
                    continue
                    #sys.exit(1)
                try:
                    shutil.copy(model_path, dest_path)
                    print(f"[✓] Copied model to {dest_path}")
                except Exception as e:
                    print(f"[!] Failed to copy model: {e}")
                    sys.exit(1)
        else:
            print(f"[✓] Model already present: {dest_path}")





TABLES_SQL = [
    # Paste all your table SQL definitions here exactly as in your message
    """CREATE TABLE IF NOT EXISTS sparrc_appointments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        doctor_id VARCHAR(50),
        appointment_date DATETIME,
        status ENUM('pending','approved','rejected','rescheduled') DEFAULT 'pending',
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        KEY idx_patient_id (patient_id),
        KEY idx_doctor_id (doctor_id)
    )""",
    """CREATE TABLE IF NOT EXISTS sparrc_doctor_info (
        doctor_id VARCHAR(50) PRIMARY KEY,
        doctor_name VARCHAR(255),
        dob DATE,
        contact_number VARCHAR(20),
        email VARCHAR(255),
        specialization VARCHAR(255),
        date_joined DATE,
        years_of_experience INT,
        clinic_branch TEXT,
        verified TINYINT(1) DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS sparrc_patient_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        doctor_id VARCHAR(50),
        visit_date DATETIME,
        diagnosis TEXT,
        treatment TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        KEY idx_patient_id (patient_id),
        KEY idx_doctor_id (doctor_id)
    )""",
    """CREATE TABLE IF NOT EXISTS sparrc_patient_info (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_name VARCHAR(255),
        password VARCHAR(255),
        dob DATE,
        age INT,
        mobile_number VARCHAR(20),
        emergency_contact VARCHAR(20),
        gender VARCHAR(20),
        address TEXT,
        referred_by VARCHAR(255),
        consultation_type VARCHAR(255),
        occupation VARCHAR(255),
        lifestyle VARCHAR(255),
        email VARCHAR(255),
        recent_viral_infection VARCHAR(255),
        vitamin_d3_level VARCHAR(50),
        main_complaints TEXT,
        complaint_duration VARCHAR(255),
        pain_duration VARCHAR(255),
        pain_region VARCHAR(255),
        joint_name VARCHAR(255),
        joint_side VARCHAR(50),
        pain_scale INT,
        pain_presentation VARCHAR(255),
        pain_character VARCHAR(255),
        onset VARCHAR(255),
        aggravating_factors TEXT,
        associated_symptoms TEXT,
        relieving_factors TEXT,
        medical_history TEXT,
        movement_restriction VARCHAR(255),
        advised_for_surgery VARCHAR(50),
        current_medication TEXT,
        past_surgery_or_accident TEXT,
        recent_travel_or_function TEXT,
        recent_activities TEXT,
        optimal_water_intake VARCHAR(50),
        investigation_report TEXT,
        previous_treatment_details TEXT,
        treatment_outcome TEXT,
        received_injection_or_surgery VARCHAR(50),
        ergonomic_setup VARCHAR(255),
        sunlight_exposure_hours VARCHAR(50),
        caregiving_responsibility VARCHAR(255),
        challenging_daily_activities TEXT,
        walking_pain_description TEXT,
        work_or_hobbies_impact TEXT,
        sleep_hours VARCHAR(50),
        sleep_quality VARCHAR(50),
        post_sleep_recovery VARCHAR(255),
        furniture_used VARCHAR(255),
        sitting_posture VARCHAR(255),
        screen_time_hours VARCHAR(50),
        screen_devices_used VARCHAR(255),
        mattress_type VARCHAR(255),
        mattress_flipping_frequency VARCHAR(50),
        mattress_age VARCHAR(50),
        daily_commute_details TEXT,
        transportation_mode VARCHAR(50),
        vehicle_model VARCHAR(100),
        vehicle_age VARCHAR(50),
        road_condition VARCHAR(100),
        self_drive VARCHAR(10),
        passenger_seat_preference VARCHAR(100),
        footwear_age_model VARCHAR(100),
        sports_shoe_model VARCHAR(100),
        sports_shoes_used_casually VARCHAR(50),
        shoe_toe_box_pinching VARCHAR(50),
        emotional_stress_level VARCHAR(50),
        physical_stress_level VARCHAR(50),
        mental_stress_level VARCHAR(50),
        stress_triggers TEXT,
        updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        reported_by VARCHAR(255),
        doctor_id VARCHAR(50),
        prescribed_by VARCHAR(255),
        doctor_prescribed TEXT,
        report_link TEXT,
        report_summary TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS sparrc_patient_reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        doctor_id VARCHAR(50) NOT NULL,
        report_summary TEXT NOT NULL,
        report_link VARCHAR(255),
        reported_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        KEY idx_patient_id (patient_id),
        KEY idx_doctor_id (doctor_id)
    )""",
    """CREATE TABLE IF NOT EXISTS sparrc_users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin','doctor') NOT NULL,
        doctor_id VARCHAR(50),
        KEY idx_doctor_id (doctor_id)
    )"""
]

# ===================== Main Starter Function =====================
def starter():
    from dotenv import load_dotenv
    from fpdf import FPDF
    import mysql.connector

    load_dotenv(dotenv_path="./frontend/.env")
    def ensure_mysql_connector():
        try:
            import mysql.connector  # noqa
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
            print("[✓] mysql-connector-python installed.")

    # ===================== Table Definitions =====================
    TABLES_SQL = [
        """CREATE TABLE IF NOT EXISTS sparrc_patient_info (
            id VARCHAR(30) PRIMARY KEY,
            patient_name VARCHAR(255),
            password VARCHAR(255),
            dob DATE,
            age INT,
            mobile_number VARCHAR(20),
            emergency_contact VARCHAR(20),
            gender VARCHAR(20),
            address TEXT,
            referred_by VARCHAR(255),
            consultation_type VARCHAR(255),
            occupation VARCHAR(255),
            lifestyle VARCHAR(255),
            email VARCHAR(255),
            recent_viral_infection VARCHAR(255),
            vitamin_d3_level VARCHAR(50),
            main_complaints TEXT,
            complaint_duration VARCHAR(255),
            pain_duration VARCHAR(255),
            pain_region VARCHAR(255),
            joint_name VARCHAR(255),
            joint_side VARCHAR(50),
            pain_scale INT,
            pain_presentation VARCHAR(255),
            pain_character VARCHAR(255),
            onset VARCHAR(255),
            aggravating_factors TEXT,
            associated_symptoms TEXT,
            relieving_factors TEXT,
            medical_history TEXT,
            movement_restriction VARCHAR(255),
            advised_for_surgery VARCHAR(50),
            current_medication TEXT,
            past_surgery_or_accident TEXT,
            recent_travel_or_function TEXT,
            recent_activities TEXT,
            optimal_water_intake VARCHAR(50),
            investigation_report TEXT,
            previous_treatment_details TEXT,
            treatment_outcome TEXT,
            received_injection_or_surgery VARCHAR(50),
            ergonomic_setup VARCHAR(255),
            sunlight_exposure_hours VARCHAR(50),
            caregiving_responsibility VARCHAR(255),
            challenging_daily_activities TEXT,
            walking_pain_description TEXT,
            work_or_hobbies_impact TEXT,
            sleep_hours VARCHAR(50),
            sleep_quality VARCHAR(50),
            post_sleep_recovery VARCHAR(255),
            furniture_used VARCHAR(255),
            sitting_posture VARCHAR(255),
            screen_time_hours VARCHAR(50),
            screen_devices_used VARCHAR(255),
            mattress_type VARCHAR(255),
            mattress_flipping_frequency VARCHAR(50),
            mattress_age VARCHAR(50),
            daily_commute_details TEXT,
            transportation_mode VARCHAR(50),
            vehicle_model VARCHAR(100),
            vehicle_age VARCHAR(50),
            road_condition VARCHAR(100),
            self_drive VARCHAR(10),
            passenger_seat_preference VARCHAR(100),
            footwear_age_model VARCHAR(100),
            sports_shoe_model VARCHAR(100),
            sports_shoes_used_casually VARCHAR(50),
            shoe_toe_box_pinching VARCHAR(50),
            emotional_stress_level VARCHAR(50),
            physical_stress_level VARCHAR(50),
            mental_stress_level VARCHAR(50),
            stress_triggers TEXT,
            updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            reported_by VARCHAR(255),
            doctor_id VARCHAR(50),
            prescribed_by VARCHAR(255),
            doctor_prescribed TEXT,
            report_link TEXT,
            report_summary TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS sparrc_doctor_info (
            doctor_id VARCHAR(50) PRIMARY KEY,
            doctor_name VARCHAR(255),
            dob DATE,
            contact_number VARCHAR(20),
            email VARCHAR(255),
            specialization VARCHAR(255),
            date_joined DATE,
            years_of_experience INT,
            clinic_branch TEXT,
            verified TINYINT(1) DEFAULT 0
        )"""
    ]

    # ===================== Sample Inserts =====================
    SAMPLE_INSERTS = [
        """INSERT INTO sparrc_patient_info 
(id, patient_name, dob, age, mobile_number, emergency_contact, gender, address, referred_by, consultation_type, occupation, lifestyle, email, recent_viral_infection, vitamin_d3_level, main_complaints, complaint_duration, pain_duration, pain_region, joint_name, joint_side, pain_scale, pain_presentation, pain_character, onset, aggravating_factors, associated_symptoms, relieving_factors, medical_history, movement_restriction, advised_for_surgery, current_medication, past_surgery_or_accident, recent_travel_or_function, recent_activities, optimal_water_intake, investigation_report, previous_treatment_details, treatment_outcome, received_injection_or_surgery, ergonomic_setup, sunlight_exposure_hours, caregiving_responsibility, challenging_daily_activities, walking_pain_description, work_or_hobbies_impact, sleep_hours, sleep_quality, post_sleep_recovery, furniture_used, sitting_posture, screen_time_hours, screen_devices_used, mattress_type, mattress_flipping_frequency, mattress_age, daily_commute_details, transportation_mode, vehicle_model, vehicle_age, road_condition, self_drive, passenger_seat_preference, footwear_age_model, sports_shoe_model, sports_shoes_used_casually, shoe_toe_box_pinching, emotional_stress_level, physical_stress_level, mental_stress_level, stress_triggers, reported_by, doctor_id, prescribed_by, doctor_prescribed, report_link, report_summary)
VALUES
("P001", 'Anandan Kumar','1983-05-12',41,'+91 9876543210','+91 9988776655','Male','12, Gandhi Street, T. Nagar, Chennai','Dr. Selvam','In Person','IT Professional','Sedentary','anandan.k@email.com','Nil','22 ng/mL','Chronic Low Back Pain','5 years','Chronic','Lumbar Spine L4-L5','Spine','Bilateral',7,'Continuous,Movement Associated','Dull ache with occasional sharpness','Gradual','Prolonged sitting, Bending forward','Numbness in left leg','Resting','None','Yes','Nil','Occasional painkiller','None','None','Started using a new office chair','Yes','MRI shows L4-L5 disc bulge','Physiotherapy 2 years ago','Temporary relief','Nil','Nil','Less than 30 mins','Nil','Difficulty tying shoelaces','Pain radiates down the leg after 1km','Reduced productivity at work','6','Disturbed due to pain','Stiff in the morning','Ergonomic Chair','Slouched','10','Laptop, Mobile','Foam','Never','7 years','25km daily commute','Car','Hyundai Verna','5 years','Mixed, many potholes','Yes','Nil','Clarks leather shoes 3 years','Nike Revolution 5','Yes','Nil','7','5','8','Work deadlines, Traffic','Patient','D001','Dr. Selvam','MRI confirmed L4-L5 disc bulge, Physiotheraphy','./patient_his_pdf/P001.pdf','NIL'),

("P002", 'Priya Venkatesh','1995-11-20',28,'+91 9123456789','+91 9234567890','Female','45, Cross Cut Road, Gandhipuram, Coimbatore','Friend','Online','Teacher','Active','priya.v@email.com','Yes','18.5 ng/mL','Right Knee Pain','3 months','Subacute','Anterior Right Knee','Knee','Right',6,'Intermittent,Movement Associated','Sharp pain on climbing stairs','Sudden','Climbing stairs, Squatting','Swelling around the kneecap','Resting,Painkillers','None','Yes','Nil','Ibuprofen as needed','None','Attended a temple festival','Increased jogging distance recently','Nil','X-ray shows no bony abnormality','Applied ice packs and rest','Mild improvement','Nil','Yes','1-2 hours','Nil','Squatting for prayers','Pain is sharp only on stairs','Stopped jogging','7.5','Good','Feels refreshed','Wooden dining chair','Upright','4','Mobile, Laptop','Cotton','Every 6 months','4 years','8km to school','Scooter','Honda Activa','3 years','Good city roads','Yes','Nil','Bata sandals 1 year','Puma running shoes','Nil','Nil','4','6','5','Managing classroom discipline','Patient','D002','Dr. Arjun','Right knee pain with mild swelling, First Aid','./patient_his_pdf/P002.pdf','NIL');""",
        """INSERT INTO sparrc_doctor_info 
(doctor_id, doctor_name, dob, contact_number, email, specialization, date_joined, years_of_experience, clinic_branch)
VALUES
('D001', 'Dr. Selvam', '1970-05-15', '+91 9090909090', 'dr.selvam@sparrc.com', 'Spine Care Specialist', '2015-08-25', 15, 'Anna Nagar, Chennai'),
('D002', 'Dr. Arjun', '1980-08-20', '+91 8080808080', 'dr.arjun@sparrc.com', 'Sports Medicine Specialist', '2015-08-25', 10, 'Avadi, Chennai');
    """]

    # ===================== Main Function =====================
    ensure_mysql_connector()
    import mysql.connector

    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "rootpass")
    db_name = os.getenv("DB_NAME", "sparrc")

    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass)
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    conn.database = db_name

    # create tables
    for sql in TABLES_SQL:
        cursor.execute(sql)
    print("[✓] Tables created.")

    # insert sample data
    for ins in SAMPLE_INSERTS:
        try:
            cursor.execute(ins)
        except mysql.connector.errors.IntegrityError:
            pass
    conn.commit()
    print("[✓] Sample data inserted.")

    cursor.close()
    conn.close()
# ===================== Execute =====================
if __name__ == "__main__":
    ensure_pip_updated()

    os.system(f"{sys.executable} -m pip list >> piplist.txt")
    packages = [line.split()[0] for line in open("piplist.txt").readlines()[2:]]
    install_packages(packages)

    handle_model({
        "Intern-S1-mini-Q8_0.gguf": "https://huggingface.co/internlm/Intern-S1-mini-GGUF/blob/main/Q8_0/Intern-S1-mini-Q8_0.gguf",
        "medgemma-4b-it-Q4_K_M.gguf": "https://huggingface.co/lmstudio-community/medgemma-4b-it-GGUF/resolve/main/medgemma-4b-it-Q4_K_M.gguf",
        "mmproj-model-F16.gguf": "https://huggingface.co/lmstudio-community/medgemma-4b-it-GGUF/resolve/main/mmproj-model-F16.gguf",
        "mmproj-Intern-S1-mini-Q8_0.gguf": "https://huggingface.co/internlm/Intern-S1-mini-GGUF/resolve/main/Q8_0/mmproj-Intern-S1-mini-Q8_0.gguf"
    })

    starter()
