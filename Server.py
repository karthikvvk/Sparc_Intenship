from flask import Flask, jsonify, request
import mysql.connector
from SumAi import *
from Starter import *
from flask_cors import CORS  # Import CORS
import io, fitz, re
from pyngrok import ngrok
from pycloudflared import try_cloudflare



app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

# MySQL DB config
db_config = {
    'host': 'localhost',
    'user': 'jacksparrow',         # change if needed
    'password': '1234',         # change if needed
    'database': 'sparc'
}
active_clients = {}

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
        update_summary_in_db(conn, cursor, patient_id, new_text, method="merge")   # unified update handler
        return jsonify({"message": "Summary merged successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/start_summarisation", methods=["GET", "POST"])
def start_summarisation():
    client_id = request.remote_addr  
     # you could also bind by auth token
    if active_clients.get(client_id, False):
        return jsonify({"status": "Already running for this device"}), 429
    active_clients[client_id] = True
    try:
        #print("yesd")
        # Ensure DB exists and has starter data
        conn = mysql.connector.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["password"])
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        lis = cursor.fetchall()
        if ("sparc",) not in lis:
            starter()
        conn.close()
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patient_details LIMIT 1")
        if len(cursor.fetchall()) == 0:
            starter()
        cursor.close()
        conn.close()

        # If form-data (PDF upload)
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            patient_id = request.form.get("patientId", "")
            idea = request.form.get("idea", "")
            pdf_file = request.files.get("pdf")

            if not pdf_file:
                return jsonify({"error": "PDF file required"}), 400

            pdf = f"/home/muruga/workspace/intern/summ/temppdfs/{pdf_file.filename}"
            pdf_file.save(pdf)

            return handle_single_summarisation(patient_id, idea=idea, pdf=pdf)

        # If JSON body
        try:
            data = request.get_json(force=True)
            #print("datahi (json)")
        except Exception as e:
            return jsonify({"error": "Invalid JSON"}), 400

        patient_id = data.get("patientId")
        if not patient_id:
            return jsonify({"error": "patientId is required"}), 400

        return handle_single_summarisation(patient_id, idea=data.get("idea", ""))

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
            return jsonify({"error": "patientId and text are required"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        replaced_summary = update_summary_in_db(conn, cursor, patient_id, new_text, method="replace")
        print(replaced_summary)
        return jsonify({
            "status": "Replace complete",
            "patient_id": patient_id,
            "summary": replaced_summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

@app.route("/add", methods=["POST"])
def add_summary():
    try:
        data = request.get_json(force=True)
        patient_id = data.get("patientId")
        
        new_text = data.get("summary")

        if not patient_id or not new_text:
            return jsonify({"error": "patientId and text are required"}), 400

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
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


def handle_bulk_summarisation():
    """Summarise all patients with empty summary"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        select_query = """
            SELECT id, med_history_pdf
            FROM patient_details
            WHERE (med_history_summary IS NULL OR med_history_summary = '')
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
                update_summary_in_db(conn, cursor, patient_id, summary, method="<replace>")
                updated_patients.append({"id": patient_id, "pdf": pdf_path})
            except Exception as e:
                print(f"Error summarizing patient {patient_id}: {e}")
                continue

        return jsonify({"status": "Summarisation complete", "patients_updated": updated_patients})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def clean_summary_text(raw_text: str) -> str:
    """
    Cleans extracted text:
    - Removes extra newlines, quotes, weird characters
    - Removes AI meta markers like <|end|>, <|start|>, assistant, final, etc.
    - Collapses multiple spaces into one
    - Returns a single clean paragraph
    """
    if not raw_text:
        return ""

    # Remove control characters except basic punctuation
    cleaned = re.sub(r'[^\x20-\x7E\n]', ' ', raw_text)

    # Remove meta markers like <|...|> or tokens like assistant/final/message
    cleaned = re.sub(r'<\|.*?\|>', ' ', cleaned)
    cleaned = re.sub(r'\b(?:assistant|final|message|channel|start|end)\b', ' ', cleaned, flags=re.IGNORECASE)

    # Replace multiple newlines with a single space
    cleaned = re.sub(r'\s*\n\s*', ' ', cleaned)

    # Remove quotes and extra spaces
    cleaned = re.sub(r'["“”]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned.strip()

def handle_single_summarisation(patient_id, idea="", pdf=""):
    if pdf != "":
        # summary = StartSummarize(pdf, idea=idea)
        # summary = clean_summary_text(summary)
        summary = "this is summary"
        return jsonify({
            "summary": summary,
            "idea": idea
        })

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT med_history_pdf FROM patient_details WHERE id = %s", (patient_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": f"No patient found with id {patient_id}"}), 404

        pdf_path = row[0]
        # summary = f"this is summary"
        summary = StartSummarize(pdf_path, idea)
        summary = clean_summary_text(summary)

        
        return jsonify({

            "summary": summary,"idea": idea
        })

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_summary_in_db(conn, cursor, patient_id, new_text, method="replace"):
    """
    Update med_history_summary based on method:
    - replace: overwrite everything with new_text
    - merge: summarise(last + new_text)
    - add: append with "|" delimiter, no summarisation
    """
    # Fetch existing summary
    cursor.execute("SELECT med_history_summary FROM patient_details WHERE id = %s", (patient_id,))
    row = cursor.fetchone()
    existing_raw = row[0] if row else None

    if method == "replace":
        # overwrite completely
        updated_summary = new_text

    elif method == "merge":
        if existing_raw and existing_raw.strip() != "":
            last_piece = existing_raw.split("|")[-1]
            merged = "merged text"
            merged = StartSummarize(last_piece + new_text)
            updated_summary = merged
        else:
            updated_summary = new_text

    elif method == "add":
        if existing_raw and existing_raw.strip() != "":
            updated_summary = existing_raw + "|" + new_text
        else:
            updated_summary = new_text

    else:
        raise ValueError(f"Invalid method: {method}")

    # update DB
    update_query = """
        UPDATE patient_details
        SET med_history_summary = %s
        WHERE id = %s
    """
    cursor.execute(update_query, (updated_summary, patient_id))
    conn.commit()
    return updated_summary

if __name__ == "__main__":
    # url = try_cloudflare(port=5000)
    # print("Tunnel URL:", url)
    app.run(host="0.0.0.0", port=5000)
