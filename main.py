from flask import Flask, render_template, request, redirect, flash
import cv2
import uuid
import os
import mysql.connector
from datetime import datetime
import re

IMG_UPLOAD_FOLDER_NEGATIVE = "data/images/positive"
IMG_UPLOAD_FOLDER_POSITIVE = "data/images/negative"
AUDIO_UPLOAD_FOLDER = "data/audios"


app = Flask(__name__)
app.config["IMG_UPLOAD_FOLDER_POSITIVE"] = IMG_UPLOAD_FOLDER_POSITIVE
app.config["IMG_UPLOAD_FOLDER_NEGATIVE"] = IMG_UPLOAD_FOLDER_NEGATIVE
app.config["AUDIO_UPLOAD_FOLDER"] = AUDIO_UPLOAD_FOLDER
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


mysql_config = {
    "user": "root",
    "password": "sK)#kV;NHSbX#7C0pU{p",
    "host": "localhost",
    "database": "project",
}


def sanitize_sql_string(value):
    """Helper function to sanitize SQL strings"""
    return re.sub(r"[-'\"\\]", "", value)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/response")
def response():
    return render_template("response.html")


@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")


@app.route("/feedback")
def feedback():
    return render_template("feedback.html")


@app.route("/rate")
def rate():
    return render_template("rate.html")


@app.route("/save-record", methods=["POST"])
def save_record():
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files["file"]

    if file.filename == "":
        flash("No selected file")
        return redirect(request.url)

    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_name = f"{current_time}_{str(uuid.uuid4())}.mp3"
    full_file_name = os.path.join(app.config["AUDIO_UPLOAD_FOLDER"], file_name)
    file.save(full_file_name)

    full_file_name = sanitize_sql_string(full_file_name)

    return full_file_name


@app.route("/submit", methods=["POST"])
def submit():
    username = request.form["username"]
    mobile_number = request.form["mobile_number"]
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not re.match("^[a-zA-Z0-9_ ]*$", username):
        return render_template(
            "error.html",
            message="ഉപയോക്തൃനാമത്തിൽ അസാധുവായ പ്രതീകങ്ങൾ!  അക്ഷരങ്ങൾ, അക്കങ്ങൾ, സ്‌പെയ്‌സുകൾ, അടിവരകൾ എന്നിവ മാത്രം ഉപയോഗിക്കുക.",
            error="/static/audios/error1.mp3",
        )

    if len(mobile_number) != 10:
        return render_template(
            "error.html", 
            message="ശരിയായ ഫോൺ നമ്പർ അല്ല! ശരിയായ നമ്പർ ഉപയോഗിക്കുക.",
            error="/static/audios/error2.mp3",
        )

    cnx = mysql.connector.connect(**mysql_config)
    cursor = cnx.cursor()
    query = "SELECT * FROM user_data WHERE mobile_number=%s"
    cursor.execute(query, (sanitize_sql_string(mobile_number),))

    result = cursor.fetchone()
    if result is not None:
        cursor.close()
        cnx.close()
        return render_template(
            "error.html",
            message="ഫോൺ നമ്പർ ഇതിനകം നിലവിലുണ്ട്! മറ്റൊരു നമ്പർ ഉപയോഗിക്കുക.",
            error="/static/audios/error3.mp3",
        )

    cap = cv2.VideoCapture(0)

    ret, frame = cap.read()

    cap.release()

    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{current_time}_{str(uuid.uuid4())}.jpg"
    img_file_name = os.path.join(app.config["IMG_UPLOAD_FOLDER_POSITIVE"], filename)

    cv2.imwrite(img_file_name, frame)

    img_file_name = sanitize_sql_string(img_file_name)

    full_file_name = save_record() if "file" in request.files else ""
    insert_query = "INSERT INTO user_data (username, mobile_number, image, audio, timestamp) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(
        insert_query,
        (
            sanitize_sql_string(username),
            sanitize_sql_string(mobile_number),
            img_file_name,
            full_file_name,
            timestamp,
        ),
    )

    cnx.commit()
    cursor.close()
    cnx.close()

    return render_template("thankyou.html")


@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    username = request.form["username"]
    mobile_number = request.form["mobile_number"]
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not re.match("^[a-zA-Z0-9_ ]*$", username):
        return render_template(
            "error.html",
            message="ഉപയോക്തൃനാമത്തിൽ അസാധുവായ പ്രതീകങ്ങൾ!  അക്ഷരങ്ങൾ, അക്കങ്ങൾ, സ്‌പെയ്‌സുകൾ, അടിവരകൾ എന്നിവ മാത്രം ഉപയോഗിക്കുക.",
            error="/static/audios/error1.mp3",
        )

    if len(mobile_number) != 10:
        return render_template(
            "error.html",
            message="ശരിയായ ഫോൺ നമ്പർ അല്ല! ശരിയായ നമ്പർ ഉപയോഗിക്കുക.",
            error="/static/audios/error2.mp3",
        )

    cnx = mysql.connector.connect(**mysql_config)
    cursor = cnx.cursor()
    query = "SELECT * FROM user_data_positive WHERE mobile_number=%s"
    cursor.execute(query, (sanitize_sql_string(mobile_number),))

    result = cursor.fetchone()
    if result is not None:
        cursor.close()
        cnx.close()
        return render_template(
            "error.html",
            message="ഫോൺ നമ്പർ ഇതിനകം നിലവിലുണ്ട്! മറ്റൊരു നമ്പർ ഉപയോഗിക്കുക.",
            error="/static/audios/error3.mp3",
        )

    rating = int(request.form["rating"])
    cnx = mysql.connector.connect(**mysql_config)
    cursor = cnx.cursor()

    cap = cv2.VideoCapture(0)

    ret, frame = cap.read()

    cap.release()

    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{current_time}_{str(uuid.uuid4())}.jpg"
    img_file_name = os.path.join(app.config["IMG_UPLOAD_FOLDER_NEGATIVE"], filename)

    cv2.imwrite(img_file_name, frame)

    insert_query = "INSERT INTO user_data_positive (username, mobile_number, rating, image, timestamp) VALUES (%s, %s, %s ,%s, %s)"
    cursor.execute(
        insert_query,
        (
            sanitize_sql_string(username),
            sanitize_sql_string(mobile_number),
            rating,
            img_file_name,
            timestamp,
        ),
    )
    cnx.commit()
    cursor.close()
    cnx.close()

    return render_template("thankyou.html")


if __name__ == "__main__":
    app.run(debug=True)
