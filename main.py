from flask import Flask, render_template, request, redirect, flash, url_for
import cv2
import uuid
import os
import mysql.connector
from datetime import datetime
import re

IMG_UPLOAD_FOLDER = "static/images"
AUDIO_UPLOAD_FOLDER = "staic/audios"
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav'}

app = Flask(__name__)
app.config["IMG_UPLOAD_FOLDER"] = IMG_UPLOAD_FOLDER
app.config["AUDIO_UPLOAD_FOLDER"] = AUDIO_UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# MySQL configuration
mysql_config = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'host': os.environ.get('MYSQL_HOST'),
    'database': os.environ.get('MYSQL_DATABASE')
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


@app.route("/submit", methods=["POST"])
def submit():
    # get the user's name and mobile number
    username = request.form["username"]
    mobile_number = request.form["mobile_number"]
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # validate username with valid characters
    if not re.match("^[a-zA-Z0-9_ ]*$", username):
        return render_template("error.html", message="ഉപയോക്തൃനാമത്തിൽ അസാധുവായ പ്രതീകങ്ങൾ!  അക്ഷരങ്ങൾ, അക്കങ്ങൾ, സ്‌പെയ്‌സുകൾ, അടിവരകൾ എന്നിവ മാത്രം ഉപയോഗിക്കുക.")

    if len(mobile_number) != 10:
        return render_template("error.html", message="ശരിയായ ഫോൺ നമ്പർ അല്ല! ശരിയായ നമ്പർ ഉപയോഗിക്കുക.")

    # check if the mobile number already exists
    cnx = mysql.connector.connect(**mysql_config)
    cursor = cnx.cursor()
    query = "SELECT * FROM user_data WHERE mobile_number=%s"
    cursor.execute(query, (sanitize_sql_string(mobile_number),))

    result = cursor.fetchone()
    if result is not None:
        cursor.close()
        cnx.close()
        return render_template("error.html", message="ഫോൺ നമ്പർ ഇതിനകം നിലവിലുണ്ട്! മറ്റൊരു നമ്പർ ഉപയോഗിക്കുക.")

    # initialize the camera
    cap = cv2.VideoCapture(0)

    # read the image from the camera
    ret, frame = cap.read()

    # release the camera
    cap.release()

    # generate a unique filename with timestamp for the photo
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{current_time}_{str(uuid.uuid4())}.jpg"
    img_file_name = os.path.join(
        app.config["IMG_UPLOAD_FOLDER"], os.path.basename(filename))
    img_file_name = os.path.abspath(img_file_name)
#        if not img_file_name.startswith(app.config["IMG_UPLOAD_FOLDER"]):
#            raise ValueError("Invalid file name")

    # save the image to disk
    cv2.imwrite(img_file_name, frame)

    # fetch the audio file name from save_record function
    full_file_name = save_record()

    # save the user's name, mobile number, image and audio to the database
    insert_query = "INSERT INTO user_data (Username, Number, Image, Timestamp) VALUES (%s, %s, %s, %s)"
    cursor.execute(insert_query, (sanitize_sql_string(username), sanitize_sql_string(
        mobile_number), sanitize_sql_string(img_file_name), timestamp))

    cnx.commit()
    cursor.close()
    cnx.close()

    # return a success message to the user
    return render_template("thankyou.html")


def save_record():
    # check if the post request has the file part
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files["file"]

    # if user does not select file, browser also submits an empty part without filename
    if file.filename == "":
        flash("No selected file")
        return redirect(request.url)

    # check if the file is an audio file
    if file.filename.split('.')[-1] not in ALLOWED_AUDIO_EXTENSIONS:
        flash("Only audio files are allowed")
        return redirect(request.url)

    # generate a unique filename with timestamp for the audio file
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_ext = file.filename.split('.')[-1]
    file_name = f"{current_time}_{str(uuid.uuid4())}.{file_ext}"
    full_file_name = os.path.join(
        app.config["AUDIO_UPLOAD_FOLDER"], os.path.basename(file_name))
    full_file_name = os.path.abspath(full_file_name)
#    if not full_file_name.startswith(app.config["AUDIO_UPLOAD_FOLDER"]):
#        raise ValueError("Invalid file name")

    file.save(full_file_name)

    # sanitize the file name before inserting it into the database
    full_file_name = sanitize_sql_string(full_file_name)

    return full_file_name


if __name__ == "__main__":
    app.run(debug=True)
