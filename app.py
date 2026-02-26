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
@app.route('/addadmin', methods = ['GET','POST'])
def addadmin():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        data = request.json

        id = str(uuid.uuid4())
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = "Admin"
        profile_img = data.get('profile_img')
        status = "Active"
        contact = data.get('contact')
        org_id = str(uuid.uuid4())

        hashed_password = generate_password_hash(password)

        cursor.execute("SELECT EMAIL FROM USERS")
        email1 = cursor.fetchall()
        emails = [x[0] for x in email1]
        if email in emails:
            return jsonify({
                'status': 'fail',
                'message': 'Email Already Exists'
            })
        else:

            cursor.execute("INSERT INTO USERS(id, Name, Email, Password, Role, Profile_img, Status, Contact, org_id, Created_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW())",(id,name,email,hashed_password,role,profile_img,status,contact,org_id))
            conn.commit()
            return jsonify({
                'status':'success',
                'message': 'Admin Added Successfully'
            })
    except Exception as e:
        print(e)
        return jsonify({
            'status':'error',
            'message': str(e)
        })
    
    finally:
        conn.close()
        cursor.close()
        



if __name__ == '__main__':
    app.run(debug=True, port=5001)