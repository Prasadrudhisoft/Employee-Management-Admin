from flask import Flask, request, jsonify, render_template
from connector import get_connection
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

@app.route('/register_superadmin')
def register_superadmin():
    return render_template('register.html')

@app.route('/', methods = ['GET'])
def login_superadmin():
    return render_template('login.html')

@app.route('/dashboard')
def superadmin_dashboard():
    return render_template('dashboard.html')


import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/profile_imgs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file):
    if not file or file.filename == '':
        return ''
    if not allowed_file(file.filename):
        return ''
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath.replace('\\', '/')

#Login
@app.route('/login', methods=['POST'])
def login():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        data = request.json

        if not data:
            return jsonify({
                'status': 'fail',
                'message': 'Request body missing'
            }), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'status': 'fail',
                'message': 'Email and Password are required'
            }), 400

        cursor.execute("SELECT * FROM users WHERE Email = %s and Status = 'Active' and Role='Super_Admin'", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({
                'status': 'fail',
                'message': 'Wrong or Invalid Email'
            }), 400

        # Assuming password column index is 3
        stored_password = user[3]

        if not check_password_hash(stored_password, password):
            return jsonify({
                'status': 'fail',
                'message': 'Wrong Password'
            }), 400

        return jsonify({
            'status': 'success',
            'message': 'Logged Successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

    finally:
        conn.close()
        cursor.close()

#Add Admin/New Organization By Super Admin
@app.route('/addadmin', methods=['GET', 'POST'])
def addadmin():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        data = request.form  # ✅ FIXED: was request.json

        id       = str(uuid.uuid4())
        name     = data.get('name')
        email    = data.get('email')
        password = data.get('password')
        role     = "Admin"
        status   = "Active"
        contact  = data.get('contact')
        org_name = data.get('org_name')
        org_id   = str(uuid.uuid4())

        hashed_password = generate_password_hash(password)

        # ✅ FIXED: save uploaded file, not base64 string
        profile_file = request.files.get('profile_img')
        profile_img  = save_profile_image(profile_file)

        cursor.execute("SELECT Email FROM users")
        emails = [x[0] for x in cursor.fetchall()]

        if email in emails:
            return jsonify({'status': 'fail', 'message': 'Email Already Exists'})

        cursor.execute(
            "INSERT INTO users(id, Name, Email, Password, Role, Profile_img, Status, Contact, org_id, org_name, created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())",
            (id, name, email, hashed_password, role, profile_img, status, contact, org_id, org_name)
        )
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Admin Added Successfully'})

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)})

    finally:
        conn.close()
        cursor.close()
        

if __name__ == '__main__':
    app.run(debug=True, port=5001)