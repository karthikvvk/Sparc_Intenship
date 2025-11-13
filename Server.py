from Starter import *
starter()#Take care of All the dependencies like DB, Folders etc., before starting the Server.

import time
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
default_pdf = os.getenv("PDF_DIR1")
temp_pdf = os.getenv("PDF_DIR2")

#Initialising app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)



# MySQL DB config
db_config = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

# Global state to track active clients
active_clients = {}



# -------------------- ROUTES --------------------
@app.route("/update_summary", methods=["POST"]) # Unified endpoint for replace, add, and merge operations.
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

@app.route('/load_history', methods=['POST'])# loads specific patient's past summaries from DB
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

@app.route("/merge", methods=["POST"])# Merge End-Point
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

@app.route("/start_summarisation", methods=["GET", "POST"])# Summary's starting end-point
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

        # using pdf upload via form-data(direct pdf upload)
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            patient_id = request.form.get("patientId", "")
            idea = request.form.get("idea", "")
            pdf_file = request.files.get("pdf")
            if not pdf_file:
                return jsonify({"error": "PDF file required"}), 400

            pdf = f"{temp_pdf}/{pdf_file.filename}"
            pdf_file.save(pdf)

            return handle_single_summarisation(patient_id, idea=idea, pdf=pdf, form="true")

        # Rest below is using the patient detail from DB
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({"error": "Invalid JSON"}), 400
        patient_id = data.get("patientId")
        if not patient_id:
            return jsonify({"error": "patientId is required"}), 400
        
        # print("pdf_iruka", data.get("pdf"))
        pdf_value = str(data.get("pdf", "")).strip().lower()

        if pdf_value and pdf_value != "false":
            #calls the handler for internlm + DB
            return handle_single_summarisation(
                patient_id,
                idea=data.get("idea", ""),
                pdf="true",
                form="false"
            )
        elif pdf_value and pdf_value == "false":
            #calls the handler for only medgemma
            return handle_single_summarisation(
                patient_id,
                idea=data.get("idea", ""),
                pdf="false",
                form="false"
            )

        #ensure fallback return
        return jsonify({"error": "Invalid pdf flag, must be 'true' or ''"}), 400

    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        active_clients[client_id] = False

@app.route("/replace", methods=["POST"])# replace end-point
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

@app.route("/add", methods=["POST"])# add this version end-point
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

@app.route("/searchpatient", methods=["POST"])# search patient end-point
def search_patient():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        search_query = """
            SELECT id, patient_name, report_summary
            FROM sparrc_patient_info
            WHERE patient_name LIKE %s OR id LIKE %s
            LIMIT 10
        """
        like_pattern = f"%{query}%"
        print("query", search_query, (like_pattern, like_pattern))
        cursor.execute(search_query, (like_pattern, like_pattern))
        results = cursor.fetchall()
        for row in results:
            summary = row.get("report_summary")
            if summary:
                # first 20 characters + ellipsis
                row["report_summary"] = summary[:50] + ("..." if len(summary) > 20 else "")

        print("results", results)
        cursor.close()
        conn.close()

        return jsonify({"patients": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stop", methods=["POST"])# stop current processing end-point
def stop_processing():
    client_id = request.remote_addr
    print(active_clients)
    try:
        if client_id in active_clients:
            # If you stored an AI process handle, terminate it here
            # Example: active_clients[client_id].terminate()
            # But threading not possible without GPU. And the subprocessing also resource intensive.
            del active_clients[client_id]
            print(active_clients)
            return jsonify({"status": "Stopped AI processing for this client"}), 200
        else:
            return jsonify({"status": "No active process for this client"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# -------------------- HELPERS --------------------
def handle_bulk_summarisation(): # Summarises all patients who have empty report_summary field.
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

def handle_single_summarisation(patient_id, idea="", pdf="", form="true"):# Summary for single patient based on doctor's requirement.
    if form == "true":
        #direct pdf upload
        summary = StartSummarize(path=pdf, idea=idea, form="true")
        summary = clean_summary_text(summary)
    elif pdf == "true":
        #internlm(handles images) + DB(summarise using pdf path in db)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sparrc_patient_info WHERE id = %s", (patient_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({"error": f"No patient found with id {patient_id}"}), 404

        pdf_path = row[-2]
        summary = StartSummarize(path=pdf_path, idea=idea, data=row, pdf='true')
        summary = clean_summary_text(summary)

    elif pdf == "false":
        #only medgemma (no image reading and pdf reading from anywhere)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sparrc_patient_info WHERE id = %s", (patient_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        summary = StartSummarize(idea=idea, data=row, pdf="false")
        summary = clean_summary_text(summary)
        # summary = "single two" #use for testing faster without Ai

        structured_data = print_structured_summary(summary)
        # structured_data = summary
        print("structured_data", structured_data)
        return jsonify({
            "summary": structured_data["formatted_summary"],
            "structured": structured_data["structured"],
            "idea": idea
        })


    
    structured_data = print_structured_summary(summary)
    # structured_data = summary
    print("structured_data", structured_data)
    return jsonify({
        "summary": structured_data["formatted_summary"],
        "structured": structured_data["structured"],
        "idea": idea
    })

def update_summary_in_db(conn, cursor, patient_id, new_text, method="replace"):#handles the merge, add, replace operations finally in DB.
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
            # updated_summary = "merged one" #use for faster testing without Ai
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
    public_url = None

    # #comment these below lines if you don't want to use  ngrok
    tunnel = ngrok.connect(5000)
    public_url = tunnel.public_url

    # print("Tunnel URL:", public_url)# Use this to access the Flask app URL during development

    # Fallback if tunnel fails. Falls to Localhost
    if not public_url:
        public_url = "http://127.0.0.1:5001"

    # Save to .env (This allow us to seperate/chain the development of Fronten and Backend. When chained both backend and frontend RESTARTS in same URL) USE in Deployment
    set_key("./frontend/.env", "VITE_API_URL", public_url)

    # Run Flask
    app.run(host="0.0.0.0", port=5001)
