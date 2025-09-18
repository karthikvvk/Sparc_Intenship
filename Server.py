from Starter import *
starter()

from flask import Flask, jsonify, request
import mysql.connector
from SumAi import *
from flask_cors import CORS
import os
from pycloudflared import try_cloudflare
from dotenv import load_dotenv, set_key
from Cleaner import *
from pyngrok import ngrok


# ---------- Load environment variables ----------
load_dotenv(dotenv_path="./frontend/.env")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

default_pdf = os.getenv("PDF_DIR1")
temp_pdf = os.getenv("PDF_DIR2")

# MySQL DB config
db_config = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}
active_clients = {}




@app.route("/update_summary", methods=["POST"])
def update_summary():
    try:
        data = request.get_json(force=True)
        patient_id = data.get("patientId")
        new_text = data.get("summary")
        method = data.get("method", "replace")  # default is replace
        idea = data.get("idea", None)

        if not patient_id or not new_text:
            return jsonify({"error": "patientId and summary are required"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        updated_summary = update_summary_in_db(conn, cursor, patient_id, new_text, method=method)

        return jsonify({
            "status": f"{method.capitalize()} complete",
            "patient_id": patient_id,
            "summary": updated_summary,
            "idea": idea
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



@app.route('/load_history', methods=['POST'])
def load_history():
    try:
        data = request.get_json()
        patient_id = data.get("patientId")

        if not patient_id:
            return jsonify({"error": "patientId is required"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT report_summary FROM sparrc_patient_info WHERE id = %s", (patient_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row or not row[0]:
            return jsonify({"history": []}), 200

        # Split stored summaries by "|" and reverse for latest first
        history_items = row[0].split("|")
        history = [{"summary": item.strip(), "idea": None} for item in history_items if item.strip()]

        return jsonify({"history": list(reversed(history))}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# -------------------- ROUTES --------------------
@app.route("/merge", methods=["POST"])
def merge_summary():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    data = request.get_json()
    patient_id = data.get("patientId")
    new_text = data.get("summary")

    if not patient_id or not new_text:
        return jsonify({"error": "patientId and summary are required"}), 400

    try:
        update_summary_in_db(conn, cursor, patient_id, new_text, method="merge")
        return jsonify({"message": "Summary merged successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/start_summarisation", methods=["GET", "POST"])
def start_summarisation():
    client_id = request.remote_addr
    if active_clients.get(client_id, False):
        return jsonify({"status": "Already running for this device"}), 429
    active_clients[client_id] = True

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'sparrc_patient_info'")
        if cursor.fetchone() is None:
            starter()
        cursor.execute("SELECT * FROM sparrc_patient_info LIMIT 1")
        if len(cursor.fetchall()) == 0:
            starter()
        cursor.close()
        conn.close()

        # pdf upload via form-data
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            patient_id = request.form.get("patientId", "")
            idea = request.form.get("idea", "")
            pdf_file = request.files.get("pdf")

            if not pdf_file:
                return jsonify({"error": "PDF file required"}), 400

            pdf = f"{temp_pdf}/{pdf_file.filename}"
            pdf_file.save(pdf)

            return handle_single_summarisation(patient_id, idea=idea, pdf=pdf)

        # Handle JSON body
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({"error": "Invalid JSON"}), 400
        patient_id = data.get("patientId")
        if not patient_id:
            return jsonify({"error": "patientId is required"}), 400
        
        print("pdf_iruka", data.get("pdf"))
        pdf_value = str(data.get("pdf", "")).strip().lower()

        if pdf_value and pdf_value != "false":
            # pdf is present/selected
            return handle_single_summarisation(
                patient_id,
                idea=data.get("idea", ""),
                pdf="true"
            )
        else:
            # pdf is not present
            return handle_single_summarisation(
                patient_id,
                idea=data.get("idea", ""),
                pdf="false"
            )

        # 🔴 FIX: ensure fallback return
        return jsonify({"error": "Invalid pdf flag, must be 'true' or ''"}), 400

    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        active_clients[client_id] = False

@app.route("/replace", methods=["POST"])
def replace_summary():
    try:
        data = request.get_json(force=True)
        patient_id = data.get("patientId")
        new_text = data.get("summary")

        if not patient_id or not new_text:
            return jsonify({"error": "patientId and summary are required"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        replaced_summary = update_summary_in_db(conn, cursor, patient_id, new_text, method="replace")

        return jsonify({
            "status": "Replace complete",
            "patient_id": patient_id,
            "summary": replaced_summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route("/add", methods=["POST"])
def add_summary():
    try:
        data = request.get_json(force=True)
        patient_id = data.get("patientId")
        new_text = data.get("summary")

        if not patient_id or not new_text:
            return jsonify({"error": "patientId and summary are required"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        added_summary = update_summary_in_db(conn, cursor, patient_id, new_text, method="add")

        return jsonify({
            "status": "Add complete",
            "patient_id": patient_id,
            "summary": added_summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# -------------------- HELPERS --------------------
def handle_bulk_summarisation():
    """Summarise all patients with empty summary"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        select_query = """
            SELECT id, report_link
            FROM sparrc_patient_info
            WHERE (report_summary IS NULL OR report_summary = '')
            ORDER BY id ASC
        """
        cursor.execute(select_query)
        patients = cursor.fetchall()

        if not patients:
            return jsonify({"status": "No patients pending summarisation"})

        updated_patients = []
        for patient_id, pdf_path in patients:
            try:
                summary = StartSummarize(pdf_path)
                update_summary_in_db(conn, cursor, patient_id, summary, method="replace")
                updated_patients.append({"id": patient_id, "pdf": pdf_path})
            except Exception as e:
                print(f"Error summarizing patient {patient_id}: {e}")
                continue

        return jsonify({"status": "Summarisation complete", "patients_updated": updated_patients})

    finally:
        cursor.close()
        conn.close()

def handle_single_summarisation(patient_id, idea="", pdf=""):
    print("reached handle")
    if pdf != "true" or pdf != "false":
        summary = StartSummarize(pdf, idea=idea)
        summary = clean_summary_text(summary)
    elif pdf == "true":
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT report_link FROM sparrc_patient_info WHERE id = %s", (patient_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({"error": f"No patient found with id {patient_id}"}), 404

        pdf_path = row[0]
        summary = StartSummarize(pdf_path, idea)
        summary = clean_summary_text(summary)

    elif pdf == "false":
        summary = StartSummarize(idea=idea)
        summary = clean_summary_text(summary)
        # summary = "single two"
        return jsonify({"summary": summary, "idea": idea})

    
    # summary = "single one"
    return jsonify({"summary": summary, "idea": idea})


def update_summary_in_db(conn, cursor, patient_id, new_text, method="replace"):
    cursor.execute("SELECT report_summary FROM sparrc_patient_info WHERE id = %s", (patient_id,))
    row = cursor.fetchone()
    existing_raw = row[0] if row else None

    if method == "replace":
        updated_summary = new_text

    elif method == "merge":
        if existing_raw and existing_raw.strip() != "":
            # combine all versions including new one
            all_versions = existing_raw.split("|")[-1]
            all_versions.append(new_text)
            combined_text = " ".join(all_versions)
            updated_summary = StartSummarize(combined_text)
            # updated_summary = "merged one"
        else:
            updated_summary = new_text

    elif method == "add":
        if existing_raw and existing_raw.strip() != "":
            updated_summary = existing_raw + "|" + new_text
        else:
            updated_summary = new_text

    else:
        raise ValueError(f"Invalid method: {method}")

    update_query = """
        UPDATE sparrc_patient_info
        SET report_summary = %s
        WHERE id = %s
    """
    cursor.execute(update_query, (updated_summary, patient_id))
    conn.commit()
    return updated_summary



if __name__ == "__main__":
    # Open ngrok tunnel
    public_url = None
    # tunnel = ngrok.connect(5000)
    # public_url = tunnel.public_url
    print("Tunnel URL:", public_url)

    # Fallback if tunnel fails
    if not public_url:
        public_url = "http://127.0.0.1:5000"

    # Save to .env
    set_key("./frontend/.env", "VITE_API_URL", public_url)

    # Run Flask
    app.run(host="0.0.0.0", port=5000)



