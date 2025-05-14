from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from supabase import create_client, Client
from datetime import datetime


SUPABASE_URL = 'https://stjbdocpwnbpnvymzqfw.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0amJkb2Nwd25icG52eW16cWZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY0OTU0MjQsImV4cCI6MjA2MjA3MTQyNH0.L6jCodygKJlZRrjUQJQQBV7REBZX-ujrxvNyrO7QTV8'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = Flask(__name__)
app.secret_key = 'your-flask-secret-key'

# Add admin credentials
users = {
    'user1@example.com': '123456',
    'user2@example.com': '654321',
}

# Admin verification code (should be stored more securely in production)
ADMIN_CODE = "12345"

# This is the main login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()  
        password = request.form['password'].strip()  

        if email in users and users[email] == password:
            # Set a session variable to indicate a regular user is logged in
            session['user_type'] = 'regular'
            return redirect(url_for('menu'))
        else:
            flash("Invalid Email or Password!", "error")
            return render_template('alogin.html'), 400  

    return render_template('alogin.html')  

# New route for admin verification
@app.route('/admin_verify', methods=['POST'])
def admin_verify():
    data = request.json
    admin_code = data.get('admin_code', '')
    
    if admin_code == ADMIN_CODE:
        # Set a session variable to indicate admin is logged in
        session['user_type'] = 'admin'
        return jsonify({'success': True, 'redirect': url_for('admin')})
    else:
        return jsonify({'success': False, 'message': 'Invalid admin code'}), 401

@app.route('/admin')
def admin():
    # Check if user is logged in as admin (in a real app, you'd verify this)
    if session.get('user_type') != 'admin':
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for('login'))
    
    # Clear any cached data by adding a timestamp parameter
    import time
    timestamp = int(time.time())
    
    # Fetch document requests
    doc_res = supabase.table('document_requests') \
                   .select('*') \
                   .order('requested_at', desc=True) \
                   .execute()
    document_requests = doc_res.data or []
    
    # Fetch complaints
    comp_res = supabase.table('filed_complaints') \
                   .select('*') \
                   .order('filed_date', desc=True) \
                   .execute()
    complaints = comp_res.data or []
    
    return render_template('admin.html', 
                          document_requests=document_requests, 
                          complaints=complaints,
                          cache_buster=timestamp)


@app.route('/api/requests/<int:req_id>/status', methods=['PUT'])
def update_request_status(req_id):
    data = request.json
    new_status = data.get('status', 'Pending')
    # perform the update
    res = supabase.table('document_requests') \
                  .update({"status": new_status}) \
                  .eq('id', req_id) \
                  .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 400
    # return the updated record
    return jsonify(res.data), 200


@app.route('/menu')
def menu():
    # Check if user is logged in (in a real app, you'd use proper authentication)
    if 'user_type' not in session:
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))
    
    return render_template('bmenu.html')  


@app.route('/documents')
def documents():
    # Fetch all document requests, newest first
    res = supabase.table('document_requests') \
                  .select('*') \
                  .order('requested_at', desc=True) \
                  .execute()
    requests = res.data or []
    return render_template('documents.html', requests=requests)


@app.route('/complaint')
def complaint():
    # Fetch all complaints from Supabase
    res = supabase.table('filed_complaints').select('*').order('filed_date', desc=True).execute()
    complaints = res.data or []
    return render_template('complaint.html', complaints=complaints)

@app.route('/api/complaints', methods=['POST'])
def add_complaint():
    data = request.json
    # Map incoming fields to your table columns
    record = {
        "full_name":       data['name'],
        "address":         data['address'],
        "contact_number":  data['contactNumber'],
        "complaint_type":  data['complaintType'],
        "incident_date":   data['incidentDate'],
        "incident_time":   data['incidentTime'],
        "incident_location": data['incidentLocation'],
        "description":     data['description'],
        "agreement":       data['agreement'],
        "status":          "Pending"  # Default status for new complaints
    }
    res = supabase.table('filed_complaints').insert(record).execute()
    if res.error:
        return jsonify({"error": res.error.message}), 400
    return jsonify(res.data[0]), 201

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT REQUESTS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/requests', methods=['POST'])
def add_request():
    data = request.json
    try:
        record = {
            "name":           data['name'],
            "address":        data['address'],
            "birthdate":      data['birthdate'],
            "start_living":   data['startLiving'],
            "purpose":        data['purpose'],
            "age":            data['age'],
            "guardian_name":  data.get('guardianName', ''),
            "document_type":  data['documentType'],
            "status":         "Pending",
            "requested_at":   datetime.utcnow().isoformat()
        }
        res = supabase.table('document_requests').insert(record).execute()

        if res.error:
            return jsonify({"message": res.error.message}), 400

        return jsonify(res.data[0]), 201
    except Exception as e:
        print("Server error:", str(e))
        return jsonify({"message": "Server error"}), 500

@app.route('/api/requests', methods=['GET'])
def list_requests():
    res = supabase.table('document_requests') \
                  .select('*') \
                  .order('requested_at', desc=True) \
                  .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 500
    return jsonify(res.data or []), 200

@app.route('/api/requests/<int:req_id>', methods=['PUT'])
def update_request(req_id):
    data = request.json
    changes = {
        "name":          data['name'],
        "address":       data['address'],
        "birthdate":     data['birthdate'],
        "start_living":  data['startLiving'],
        "purpose":       data['purpose'],
        "age":           data['age'],
        "guardian_name": data.get('guardianName', ''),
        "document_type": data['documentType'],
    }
    res = supabase.table('document_requests') \
                  .update(changes) \
                  .eq('id', req_id) \
                  .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 400
    return jsonify(res.data[0] if res.data else {}), 200

@app.route('/api/requests/<int:req_id>', methods=['DELETE'])
def delete_request(req_id):
    res = supabase.table('document_requests') \
                  .delete() \
                  .eq('id', req_id) \
                  .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 400
    return '', 204

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN COMPLAINT MANAGEMENT ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/complaints/<int:complaint_id>', methods=['GET'])
def get_complaint(complaint_id):
    """Fetch a single complaint by ID."""
    res = supabase.table('filed_complaints') \
                   .select('*') \
                   .eq('id', complaint_id) \
                   .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 500
    return jsonify(res.data), 200

@app.route('/api/complaints/<int:complaint_id>/status', methods=['PUT'])
def update_complaint_status(complaint_id):
    """Update just the status of a complaint."""
    data = request.json
    status = data.get('status', 'Pending')
    
    res = supabase.table('filed_complaints') \
                  .update({"status": status}) \
                  .eq('id', complaint_id) \
                  .execute()
    
    if res.error:
        return jsonify({"error": res.error.message}), 400
    return jsonify(res.data), 200

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
