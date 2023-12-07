from flask import Flask, render_template, request, redirect, url_for
from firebaseConfig import db
from datetime import datetime
import uuid
import os
from werkzeug.utils import secure_filename
from pyrebase import pyrebase

# Configure Pyrebase
config = {
    'apiKey': "AIzaSyDixTViLvjgMjSZRia-0HnH2ma-MlbOQxg",
    'authDomain': "maintenancerequestapp.firebaseapp.com",
    'databaseURL': "https://maintenancerequestapp-default-rtdb.firebaseio.com",
    'projectId': "maintenancerequestapp",
    'storageBucket': "maintenancerequestapp.appspot.com",
    'messagingSenderId': "10327506154",
    'appId': "1:10327506154:web:13d3ba1a2b64755e496b93"
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# Configuration for file uploads
UPLOAD_FOLDER = 'path/to/upload/folder'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submitRequest', methods=['GET', 'POST'])
def submit_request():
    if request.method == 'POST':
        apartment_number = request.form['apartment_number']
        area = request.form['area']
        description = request.form['description']
        photo = request.files.get('photo')
        photo_url = None  # Default value if no photo is uploaded

        # Check if the photo part is present in the request
        if 'photo' in request.files:
            photo = request.files['photo']
            # Handle file upload
            if photo and photo.filename != '' and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_url = 'URL to the uploaded photo' 

        # Data to store in Firebase
        request_data = {
            'request_id': str(uuid.uuid4()),
            'apartment_number': apartment_number,
            'area': area,
            'description': description,
            'photo_url': photo_url,
            'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }


        db.child("requests").push(request_data)
        return redirect(url_for('home'))
    return render_template('submitRequest.html')

@app.route('/viewRequests', methods=['GET', 'POST'])
def view_requests():
    requests = db.child("requests").get().val() or {}

    if request.method == 'POST':
        apartment_number = request.form.get('apartment_number', '')
        area = request.form.get('area', '')
        status = request.form.get('status', '')

        if apartment_number:
            requests = {k: v for k, v in requests.items() if v.get('apartment_number') == apartment_number}
        if area:
            requests = {k: v for k, v in requests.items() if v.get('area') == area}
        if status:
            requests = {k: v for k, v in requests.items() if v.get('status') == status}

    return render_template('viewRequests.html', requests=requests)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/manageTenants', methods=['GET', 'POST'])
def manage_tenants():
    if request.method == 'POST':
        # Retrieving form data
        tenant_name = request.form['tenant_name']
        tenant_apartment = request.form['tenant_apartment']

        # Prepare data to be saved
        tenant_data = {
            'name': tenant_name,
            'apartment_number': tenant_apartment
        }

        # Save data to Firebase
        db.child("tenants").push(tenant_data)

    # Fetch updated list of tenants to display
    tenants = db.child("tenants").get().val() or {}
    formatted_tenants = {key[:8]: val for key, val in tenants.items()}
    return render_template('manageTenants.html', tenants=formatted_tenants)

@app.route('/update-status/<request_id>', methods=['POST'])
def update_status(request_id):
    new_status = request.form.get('new_status')
    
    db.child("requests").child(request_id).update({"status": new_status})

    return redirect(url_for('view_requests'))

if __name__ == '__main__':
    app.run(debug=True)