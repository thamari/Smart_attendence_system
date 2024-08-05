from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import numpy as np
import cv2
from tensorflow.keras.models import load_model
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.database import create_table, mark_attendance, get_attendance_records

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Load the trained model
model = load_model('model/face_recognition_model_best.keras')
label_names = ['Fahim', 'Abir', 'Hemel', 'Shepon', 'Nipa', 'Rupak', 'Sabiqul', 'Tama', 'Tarup', 'Tamim']

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16 MB

def preprocess_image(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (224, 224))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_normalized = img_rgb / 255.0
    img_expanded = np.expand_dims(img_normalized, axis=0)
    return img_expanded

def recognize_face(img_path):
    img_array = preprocess_image(img_path)
    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions, axis=1)
    predicted_label = label_names[predicted_class[0]]
    return predicted_label

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Recognize face and mark attendance
        try:
            student_name = recognize_face(file_path)
            mark_attendance(student_name)
            return render_template('index.html', label=student_name, image_url='uploads/' + filename)
        except Exception as e:
            print(e)
            return render_template('index.html', error='Face recognition failed')

@app.route('/attendance_status')
def attendance_status():
    try:
        records = get_attendance_records()
        return render_template('attendance.html', records=records)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error fetching records"}), 500

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    create_table()  # Ensure the table is created before starting the app
    app.run(debug=True, port=5001)  # Use a different port if 5000 is in use
