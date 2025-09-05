import os
import subprocess
import sys
import csv
import json
import platform

# ========== Function: Install/Update Pip & Packages ==========
def ensure_pip_updated():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("[✓] pip is up to date.")
    except Exception as e:
        print(f"[!] Failed to update pip: {e}")

def install_packages(packages):
    if os.path.exists("requirements.txt"):
        os.system(f"{sys.executable} -m pip install -r requirements.txt")
    if input("[?] Do you want to install/update additional packages? (yes/no): ").strip().lower() == "yes":
        for missing in packages:
            print(f"[?] Checking packages: {missing}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", missing])
                print(f"[✓] Package {missing} installed/updated.")
            except Exception as e:
                print(f"[!] Package installation failed: {e}")

# ========== Function: Handle Model Download (Linux + Windows) ==========
def handle_model(mods):
    for model_name, download_url in mods.items():
        model_path = f"./models/{model_name}"
        if not os.path.exists(model_path):
            choice = input(f"[?] Model '{model_name}' not found. Download it? (yes/no): ").strip().lower()
            if choice == "yes":
                os.makedirs("./models", exist_ok=True)
                print(f"[↓] Downloading {model_name} from {download_url} ...")
                try:
                    if platform.system() == "Windows":
                        subprocess.check_call(["powershell", "-Command", f"Invoke-WebRequest -Uri {download_url} -OutFile {model_path}"])
                    else:
                        subprocess.check_call(["curl", "-L", download_url, "-o", model_path])
                    print(f"[✓] Model downloaded to {model_path}")
                except Exception as e:
                    print(f"[!] Failed to download model: {e}")
                    sys.exit(1)
            else:
                model_path = input("[?] Enter full path to the model: ").strip()
                if not os.path.exists(model_path):
                    print(f"[!] Model path '{model_path}' not found. Exiting.")
                    sys.exit(1)

# ========== Main Starter Function (rest remains same) ==========
def starter():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="./frontend/.env")

    import mysql.connector
    from fpdf import FPDF

    db_config = {
        'host': os.getenv("DB_HOST"),
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD"),
        'database': os.getenv("DB_NAME")
    }

    col_defs_str = """CREATE TABLE IF NOT EXISTS patient_details (... same table definition ...)"""

    pdf_dirs = ["./patient_his_pdf", "./temppdfs"]
    for d in pdf_dirs:
        os.makedirs(d, exist_ok=True)

    def create_pdf_if_not_exists(pdf_name, row_dict):
        pdf_paths = []
        for d in pdf_dirs:
            pdf_path = os.path.join(d, f"{pdf_name}.pdf")
            if not os.path.exists(pdf_path):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                json_str = json.dumps(row_dict, indent=4)
                for line in json_str.splitlines():
                    pdf.multi_cell(0, 5, line)
                pdf.output(pdf_path)
                print(f"[+] Created PDF: {pdf_path}")
            pdf_paths.append(pdf_path)
        return pdf_paths[0]

    conn = mysql.connector.connect(host=db_config['host'], user=db_config['user'], password=db_config['password'])
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
    conn.database = db_config['database']
    cursor.execute(col_defs_str)

    csv_file = os.getenv("CSV_FILE")
    with open(csv_file, "r", encoding="utf-8", errors="replace") as file:
        reader = csv.reader(file)
        headers = next(reader)
        col_len = len(headers)

        for row in reader:
            if len(row) < col_len:
                row += ["null"] * (col_len - len(row))
            elif len(row) > col_len:
                row = row[:col_len]

            row = [None if v is None or v.strip().lower() == "null" or v.strip() == "" else v for v in row]

            placeholders = ", ".join(["%s"] * col_len)
            columns = ", ".join(headers)
            insert_query = f"""
            INSERT INTO patient_details ({columns}) 
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE updated_on = VALUES(updated_on)
            """

            try:
                cursor.execute(insert_query, row)
                conn.commit()
                row_dict = dict(zip(headers, row))
                pdf_path = create_pdf_if_not_exists(row[0], row_dict)

                update_query = "UPDATE patient_details SET med_history_pdf = %s WHERE id = %s"
                cursor.execute(update_query, (pdf_path, row[0]))
                conn.commit()
            except Exception as e:
                print(f"[!] Error inserting row {row[0]}: {e}")

    print("[✓] Processing complete.\nNow run 'python Server.py' to start the server.")

# ========== Execution ==========
if __name__ == "__main__":
    ensure_pip_updated()

    os.system(f"{sys.executable} -m pip list >> piplist.txt")
    piplis = open("piplist.txt").readlines()
    piplis = [i.split()[0].lower() for i in piplis[2:]]
    install_packages(piplis)

    handle_model({
        "gpt-oss-20b-MXFP4.gguf": "https://huggingface.co/lmstudio-community/gpt-oss-20b-GGUF/resolve/main/gpt-oss-20b-MXFP4.gguf",
        "medgemma-4b-it-Q4_K_M.gguf": "https://huggingface.co/lmstudio-community/medgemma-4b-it-GGUF/resolve/main/medgemma-4b-it-Q4_K_M.gguf"
    })
    starter()
