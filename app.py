from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import datetime
import pytesseract
from PIL import Image
import os
from flask_uploads import UploadSet, configure_uploads, IMAGES


# https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.4.20240503.exe
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract"

app = Flask(__name__)

# Configuration for file uploads
app.config["UPLOADED_PHOTOS_DEST"] = "uploads"
photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)


# Initialize the database
def init_db():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            id_card TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            doctor TEXT NOT NULL,
            issued_date TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


# Patient class
class Patient:
    def __init__(
        self, name, age, sex, id_card, birthdate, diagnosis, doctor, issued_date
    ):
        self.name = name
        self.age = age
        self.sex = sex
        self.id_card = id_card
        self.birthdate = birthdate
        self.diagnosis = diagnosis
        self.doctor = doctor
        self.issued_date = issued_date

    def age_details(self):
        today = datetime.date.today()
        birthdate = datetime.datetime.strptime(self.birthdate, "%Y-%m-%d").date()
        years = (
            today.year
            - birthdate.year
            - ((today.month, today.day) < (birthdate.month, birthdate.day))
        )
        months = today.month - birthdate.month - (1 if today.day < birthdate.day else 0)
        if months < 0:
            months += 12
        return years, months


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ocr", methods=["GET", "POST"])
def ocr():
    if request.method == "POST" and "photo" in request.files:
        filename = photos.save(request.files["photo"])
        file_path = os.path.join(app.config["UPLOADED_PHOTOS_DEST"], filename)
        text = pytesseract.image_to_string(Image.open(file_path))
        os.remove(file_path)

        # Example: Parse OCR text into structured data (customize based on OCR output format)
        lines = text.split("\n")
        data = {
            "name": "",
            "age": "",
            "sex": "",
            "id_card": "",
            "birthdate": "",
            "diagnosis": "",
            "doctor": "",
            "issued_date": "",
        }
        for line in lines:
            if "Patient:" in line:
                data["name"] = line.split("Patient:")[1].strip().split("\t")[0]
                age_info = line.split("Age:")[1].strip().split("\t")[0]
                data["age"] = age_info.split(" ")[0] if age_info else ""
            elif "ID Card:" in line:
                data["id_card"] = line.split("ID Card:")[1].strip().split("\t")[0]
            elif "Sex:" in line:
                data["sex"] = line.split("Sex:")[1].strip().split("\t")[0]
            elif "Issued Date:" in line:
                data["issued_date"] = (
                    line.split("Issued Date:")[1].strip().split("\t")[0]
                )
            elif "DIAGNOSIS" in line:
                if lines.index(line) + 2 < len(lines):
                    diagnosis_line = lines[lines.index(line) + 2]
                    if "[" in diagnosis_line and "]" in diagnosis_line:
                        data["diagnosis"] = diagnosis_line.split("[")[1].split("]")[0]
            elif "Dr." in line:
                data["doctor"] = line.strip()

        return render_template("add_patient.html", data=data)
    return render_template("ocr.html")


@app.route("/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        sex = request.form["sex"]
        id_card = request.form["id_card"]
        birthdate = request.form["birthdate"]
        diagnosis = request.form["diagnosis"]
        doctor = request.form["doctor"]
        issued_date = request.form["issued_date"]

        if (
            not name
            or not age
            or not sex
            or not id_card
            or not birthdate
            or not diagnosis
            or not doctor
            or not issued_date
        ):
            return "All fields are required", 400

        try:
            datetime.datetime.strptime(birthdate, "%Y-%m-%d")
            datetime.datetime.strptime(issued_date, "%Y-%m-%d")
        except ValueError:
            return "Invalid date format", 400

        patient = Patient(
            name, age, sex, id_card, birthdate, diagnosis, doctor, issued_date
        )

        conn = sqlite3.connect("patients.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO patients (name, age, sex, id_card, birthdate, diagnosis, doctor, issued_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                patient.name,
                patient.age,
                patient.sex,
                patient.id_card,
                patient.birthdate,
                patient.diagnosis,
                patient.doctor,
                patient.issued_date,
            ),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("add_patient.html")


@app.route("/report", methods=["GET", "POST"])
def report():
    query = "SELECT * FROM patients WHERE 1=1"
    params = []

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if start_date:
            query += " AND issued_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND issued_date <= ?"
            params.append(end_date)

    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    patients = []
    for row in rows:
        patient = Patient(*row[1:])  # Skip the ID
        years, months = patient.age_details()
        patients.append(
            {
                "name": patient.name,
                "age": patient.age,
                "sex": patient.sex,
                "id_card": patient.id_card,
                "birthdate": patient.birthdate,
                "years": years,
                "months": months,
                "diagnosis": patient.diagnosis,
                "doctor": patient.doctor,
                "issued_date": patient.issued_date,
            }
        )

    return render_template("report.html", patients=patients)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
