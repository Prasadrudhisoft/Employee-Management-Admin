from flask import Flask, request, jsonify, render_template
from connector import get_connection
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from flask import send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = 'static/profile_imgs'

@app.route('/register_superadmin')
def register_superadmin():
    return render_template('register.html')

@app.route('/', methods = ['GET'])
def login_superadmin():
    return render_template('login.html')

@app.route('/dashboard')
def superadmin_dashboard():
    return render_template('dashboard.html')

@app.route('/admin_status')
def admin_status():
    return render_template('Admin_status.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('change_password.html')

@app.route('/static/profile_imgs/<filename>')
def serve_profile_img(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



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

@app.route("/register", methods=['GET','POST'])
def register():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("select * from users where Role='Super_Admin'")
        super_admin = cursor.fetchall()
        if not super_admin:
        
            data = request.json

            id = str(uuid.uuid4())
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
            Role = "Super_Admin"
            Profile_img = data.get('Profile_img')
            Status = "Active"
            Contact = data.get('contact')
            #org_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)


            cursor.execute("INSERT INTO users(id, Name, Email, Password, Role, Profile_img, Status, Contact, created_at) Values(%s,%s,%s,%s,%s,%s,%s,%s,NOW())",(id, name,email,hashed_password,Role, Profile_img, Status, Contact))
            conn.commit()
        
            return jsonify({
                'status': 'success',
                'message': 'Super Admin Registered Successfully.'
            })
        else:
            return jsonify({
                'status': 'fail',
                'message': 'Super Admin Is Already Registered'
            })
    
    except Exception as e:
        print(e)
        return jsonify({
        "status": "error",
        "message": str(e)
    }), 500

    finally:
        conn.close()
        cursor.close()

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


@app.route('/get_emp', methods=['GET'])
def get_emp():
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM USERS WHERE Status = 'Active' and role = 'Admin'")
        active_users = cursor.fetchall()

        cursor.execute("SELECT * FROM USERS WHERE Status != 'Active' and role = 'Admin'")
        deactive_users = cursor.fetchall()

        if not active_users and not deactive_users:
            return jsonify({
                'status':'fail',
                'message':'No User Found'
            })
        
        else:
            return jsonify({
                'status':'success',
                'message':'Employees Fetched Succcessfully..',
                'active_users':active_users,
                'deactive_users':deactive_users
            })
        

    except Exception as e:
        return jsonify({
            'status':'Error',
            'message':str(e)
        })
    


@app.route('/toggle_emp_status', methods=['POST'])
def toggle_emp_status():
    """
    Toggle employee status between 'Active' and 'Deactive'.
    Expects JSON body: { "user_id": "<employee_uuid>" }
    Only operates on employees belonging to the manager's org.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'status': 'error', 'message': 'user_id is required'}), 400

        # Fetch current status — scoped to manager's org for security
        cursor.execute(
            "SELECT id, name, status FROM users WHERE id = %s AND role = 'Admin'",
            (user_id,)
        )
        emp = cursor.fetchone()

        if not emp:
            return jsonify({'status': 'error', 'message': 'Employee not found'}), 404

        # Flip status
        new_status = 'Deactive' if emp['status'] == 'Active' else 'Active'

        cursor.execute(
            "UPDATE users SET status = %s WHERE id = %s",
            (new_status, user_id)
        )
        conn.commit()

        return jsonify({
            'status': 'success',
            'message': f"Employee status updated to '{new_status}'.",
            'user_id': user_id,
            'new_status': new_status
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()
        
@app.route('/forgot_pass',methods=['POST'])
def forgot_pass():
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        data = request.json
        email = data.get('email')
        new_pass = data.get('new_pass')
        old_pass = data.get('old_pass')

        new_pass1 = generate_password_hash(new_pass)

        cursor.execute("select * from users where email=%s",(email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({
                'status':'fail',
                'message':'Invalid Email Or Old Password'
            })

        if not check_password_hash(user['Password'], old_pass):
            return jsonify({
                'status':'fail',
                'message':'Invalid Password'
            })
        
        cursor.execute("update users set password = %s where email = %s",(new_pass1,email))
        conn.commit()
        return jsonify({
                'status':'success',
                'message':'password Updated Succssfully.'
            })


    except Exception as e:
        return jsonify({
            'status':'error',
            'message':str(e)
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/my_profile', methods=['GET'])
def my_profile():
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        user_id = request.headers.get('user_id')  # Replace with JWT later

        cursor.execute("""
            SELECT id, name, email, role, profile_img
            FROM users
            WHERE id = %s AND role = 'Super_Admin'
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        # Build image URL
        if user.get('profile_img'):
            user['profile_img_url'] = request.host_url + user['profile_img']
        else:
            user['profile_img_url'] = None

        user.pop('profile_img', None)

        return jsonify({'status': 'success', 'data': user}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)