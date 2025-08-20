from flask import Flask, jsonify
import mysql.connector
from SumAi import *
from Starter import *
app = Flask(__name__)

# MySQL DB config
db_config = {
    'host': 'localhost',
    'user': 'jacksparrow',         # change if needed
    'password': '1234',         # change if needed
    'database': 'sparc'
}


@app.route("/start_summarisation", methods=["GET"])
def start_summarisation():
    conn = mysql.connector.connect(host=db_config["host"], user=db_config["user"],passwd=db_config["password"])
    cursor = conn.cursor()
    cursor.execute("show databases")
    lis = cursor.fetchall()
    if "sparc" not in lis:
        print(space,lis)
        starter()
    conn.close()
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("select * from patient_details limit 10")
        if len(cursor.fetchall()) == 0:
            starter()
        cursor.close()
        
        
        cursor = conn.cursor()
        # Step 1: Fetch all patients with empty summary
        select_query = """
            SELECT id, Med_History_Pdf 
            FROM patient_details 
            WHERE (Med_History_Summary IS NULL OR Med_History_Summary = '') 
            ORDER BY id ASC
        """
        cursor.execute(select_query)
        patients = cursor.fetchall()

        if not patients:
            return jsonify({"status": "No patients pending summarisation"})

        updated_patients = []

        for patient_id, pdf_path in patients:
            try:
                print(space, pdf_path, space)
                # Step 2: Summarize using SumAi
                summary = StartSummarize(pdf_path)

                # Step 3: Update DB
                update_query = """
                    UPDATE patient_details
                    SET Med_History_Summary = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (summary, patient_id))
                conn.commit()

                updated_patients.append({"id": patient_id, "pdf": pdf_path})

            except Exception as e:
                print(f"Error summarizing patient {patient_id}: {e}")
                continue

        return jsonify({
            "status": "Summarisation complete",
            "patients_updated": updated_patients
        })

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
