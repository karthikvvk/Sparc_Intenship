from flask import Flask, request, jsonify
from pyngrok import ngrok
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
public_url = ngrok.connect(5000)
print(" * ngrok tunnel URL:", public_url)

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'jacksparrow',         # change if needed
    'password': '1234',         # change if needed
    'database': 'sparc'
}

# Utility: DB connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print("DB Error:", e)
        return None

# READ all patients
@app.route('/patients', methods=['GET'])
def get_patients():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patient_details")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

# READ single patient
@app.route('/patients/<int:pid>', methods=['GET'])
def get_patient(pid):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patient_details WHERE id=%s", (pid,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return jsonify(row)
    return jsonify({"error": "Patient not found"}), 404

# CREATE new patient
@app.route('/patients', methods=['POST'])
def add_patient():
    data = request.json
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor()
    cols = ", ".join(data.keys())
    vals = ", ".join(["%s"] * len(data))
    sql = f"INSERT INTO patient_details ({cols}) VALUES ({vals})"
    cursor.execute(sql, tuple(data.values()))
    conn.commit()
    pid = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Patient added", "id": pid})

# UPDATE patient
@app.route('/patients/<int:pid>', methods=['PUT'])
def update_patient(pid):
    data = request.json
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor()
    set_clause = ", ".join([f"{k}=%s" for k in data.keys()])
    sql = f"UPDATE patient_details SET {set_clause} WHERE id=%s"
    cursor.execute(sql, tuple(data.values()) + (pid,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Patient updated", "id": pid})

# DELETE patient
@app.route('/patients/<int:pid>', methods=['DELETE'])
def delete_patient(pid):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "DB connection failed"}), 500
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patient_details WHERE id=%s", (pid,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Patient deleted", "id": pid})

# Run app
app.run(port=5000)
