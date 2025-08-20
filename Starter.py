import os
import csv
import json
import mysql.connector
from fpdf import FPDF


def starter():

    # DB connection config
    db_config = {
        'host': 'localhost',
        'user': 'jacksparrow',
        'password': '1234',
        'database': 'sparc'
    }


    col_defs_str = """CREATE TABLE IF NOT EXISTS patient_details (
        id VARCHAR(255) PRIMARY KEY,
        patient_name VARCHAR(100),
        dob DATE NULL,
        age INT NULL,
        mobile_number VARCHAR(20),
        emergency_contact VARCHAR(20),
        gender VARCHAR(10),
        address TEXT,
        referred_by VARCHAR(100),
        consultation_type VARCHAR(50),
        occupation VARCHAR(100),
        lifestyle VARCHAR(50),
        email VARCHAR(100),
        recent_viral_infection VARCHAR(255),
        vitamin_d3_level VARCHAR(50),
        main_complaints TEXT,
        complaint_duration VARCHAR(50),
        pain_duration VARCHAR(50),
        pain_region VARCHAR(100),
        joint_name VARCHAR(100),
        joint_side VARCHAR(50),
        pain_scale INT NULL,
        pain_presentation VARCHAR(255),
        pain_character VARCHAR(255),
        onset VARCHAR(100),
        aggravating_factors TEXT,
        associated_symptoms TEXT,
        relieving_factors TEXT,
        medical_history TEXT,
        movement_restriction VARCHAR(100),
        advised_for_surgery VARCHAR(10),
        current_medication TEXT,
        past_surgery_or_accident TEXT,
        recent_travel_or_function TEXT,
        recent_activities TEXT,
        optimal_water_intake VARCHAR(50),
        investigation_report TEXT,
        previous_treatment_details TEXT,
        treatment_outcome TEXT,
        received_injection_or_surgery VARCHAR(10),
        ergonomic_setup VARCHAR(255),
        sunlight_exposure_hours VARCHAR(50),
        caregiving_responsibility TEXT,
        challenging_daily_activities TEXT,
        walking_pain_description TEXT,
        work_or_hobbies_impact TEXT,
        sleep_hours VARCHAR(50),
        sleep_quality VARCHAR(50),
        post_sleep_recovery VARCHAR(50),
        furniture_used VARCHAR(100),
        sitting_posture VARCHAR(100),
        screen_time_hours VARCHAR(50),
        screen_devices_used VARCHAR(255),
        mattress_type VARCHAR(100),
        mattress_flipping_frequency VARCHAR(50),
        mattress_age VARCHAR(50),
        daily_commute_details TEXT,
        transportation_mode VARCHAR(100),
        vehicle_model VARCHAR(100),
        vehicle_age VARCHAR(50),
        road_condition VARCHAR(100),
        self_drive VARCHAR(10),
        passenger_seat_preference VARCHAR(100),
        footwear_age_model VARCHAR(100),
        sports_shoe_model VARCHAR(100),
        sports_shoes_used_casually VARCHAR(10),
        shoe_toe_box_pinching VARCHAR(10),
        emotional_stress_level VARCHAR(50),
        physical_stress_level VARCHAR(50),
        mental_stress_level VARCHAR(50),
        stress_triggers TEXT,
        updated_on DATE,
        reported_by VARCHAR(100),
        chat_history LONGTEXT,
        med_history_pdf VARCHAR(255),
        med_history_summary TEXT
    );
    """



    pdf_dir = "/home/muruga/Documents/patient_his_pd/"
    # Paths
    if not os.path.exists(pdf_dir):
        os.mkdir(pdf_dir)

    # PDF creation
    def create_pdf_if_not_exists(pdf_name, row_dict):
        pdf_path = os.path.join(pdf_dir, f"{pdf_name}.pdf")
        if not os.path.exists(pdf_path):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            json_str = json.dumps(row_dict, indent=4)
            for line in json_str.splitlines():
                pdf.multi_cell(0, 5, line)
            pdf.output(pdf_path)
            print(f"[+] Created PDF: {pdf_path}")
        else:
            print(f"[=] PDF already exists: {pdf_path}")
        return os.path.basename(pdf_path)

    # Step 1: Connect to MySQL
    conn = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password']
    )
    cursor = conn.cursor()

    # Ensure DB exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
    conn.database = db_config['database']
    cursor.execute(col_defs_str)


    # Step 2: Read CSV headers
    csv_file = "patient_intake_mockdata.csv"
    # fh = open(csv_file)
    # raw = fh.readlines()
    # n =  len(raw)
    # fh.close()
    with open(csv_file, "r", encoding="utf-8", errors="replace") as file:
        reader = csv.reader(file)
        headers = next(reader)   # get header row
        col_len = len(headers)

        for row in reader:
            val_n = len(row)
            if val_n < col_len:
                print("[-] Columns missing. Adding NULL instead")
                row += ["null"] * (col_len - val_n)
            elif val_n > col_len:
                print("[-] Extra columns found. Trimming")
                row = row[:col_len]

            # Build query dynamically
            placeholders = ", ".join(["%s"] * col_len)
            columns = ", ".join(headers)
            insert_query = f"INSERT INTO patient_details ({columns}) VALUES ({placeholders})"

            # Normalize values (convert empty/null strings → None)
            row = [None if v is None or v.strip().lower() == "null" or v.strip() == "" else v for v in row]

            try:
                # Insert row into DB
                cursor.execute(insert_query, row)
                conn.commit()
                print(f"[+] Inserted row with id={row[0]}")

                # Create PDF for this patient
                row_dict = dict(zip(headers, row))
                pdf_filename = create_pdf_if_not_exists(row[0], row_dict)

                # Update DB with PDF filename
                update_query = "UPDATE patient_details SET med_history_pdf = %s WHERE id = %s"
                cursor.execute(update_query, (pdf_dir+pdf_filename, row[0]))
                conn.commit()

            except mysql.connector.Error as e:
                print(f"[!] Error inserting row {row[0]}: {e}")
