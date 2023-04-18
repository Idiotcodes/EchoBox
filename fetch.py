import mysql.connector
import os


# MySQL configuration
mysql_config = {
    'user': 'root',
    'password': 'sK)#kV;NHSbX#7C0pU{p',
    'host': 'localhost',
    'database': 'project'
}

cnx = mysql.connector.connect(**mysql_config)
cursor = cnx.cursor()

# specify the SQL query to retrieve the BLOB data
query = "SELECT * FROM user_data WHERE audio = %s"

# specify the audio_id of the audio file you want to download
audio = 3

# execute the query with the audio_id parameter
cursor.execute(query, (audio,))

# fetch the BLOB data
audio_row = cursor.fetchone()

if audio_row is not None:
    audio_blob = audio_row[0]

    # specify the file path to save the downloaded audio file
    file_path = 'data/audios/downloaded_audio.mp3'

    # write the BLOB data to the file
    with open(file_path, 'wb') as f:
        f.write(audio_blob)

    print(f"Audio file downloaded and saved at {os.path.abspath(file_path)}")
else:
    print(f"No audio file found with ID {audio}")

# close the cursor and database connection
cursor.close()
cnx.close()
