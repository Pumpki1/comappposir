from flask import Flask, render_template, request, redirect, url_for, jsonify
from supabase import create_client, Client

SUPABASE_URL = 'https://stjbdocpwnbpnvymzqfw.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0amJkb2Nwd25icG52eW16cWZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY0OTU0MjQsImV4cCI6MjA2MjA3MTQyNH0.L6jCodygKJlZRrjUQJQQBV7REBZX-ujrxvNyrO7QTV8'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = Flask(__name__)
app.secret_key = 'your-flask-secret-key'

users = {
    'user1@example.com': '123456',
    'user2@example.com': '654321',
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()  
        password = request.form['password'].strip()  

        if email in users and users[email] == password:
            return redirect(url_for('menu'))
        else:
            return "Invalid Email or Password!", 400  

    return render_template('alogin.html')  

@app.route('/menu')
def menu():
    return render_template('bmenu.html')  

@app.route('/documents')
def documents():
    return render_template('documents.html')

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
        "agreement":       data['agreement']
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

@app.route('/api/requests', methods=['GET'])
def get_requests():
    """Fetch all document requests, newest first."""
    res = supabase.table('document_requests') \
                   .select('*') \
                   .order('requested_at', desc=True) \
                   .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 500
    return jsonify(res.data), 200

@app.route('/api/requests/<int:req_id>', methods=['GET'])
def get_request(req_id):
    """Fetch a single document request by ID."""
    res = supabase.table('document_requests') \
                   .select('*') \
                   .eq('id', req_id) \
                   .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 500
    return jsonify(res.data), 200

@app.route('/api/requests', methods=['POST'])
def add_request():
    """Insert a new document request. Expects application/json."""
    data = request.json
    record = {
        "name":          data['name'],
        "address":       data['address'],
        "birthdate":     data['birthdate'],      # ISO string “YYYY-MM-DD”
        "start_living":  data['startLiving'],    # ISO string “YYYY-MM-DD”
        "purpose":       data['purpose'],
        "age":           data['age'],
        "guardian_name": data.get('guardianName', None),
        "document_type": data['documentType'],
        "status":        data.get('status', 'Pending')
    }
    res = supabase.table('document_requests') \
            .insert(record) \
            .select('*') \
            .execute()
    
    if res.error:
        return jsonify({"error": res.error.message}), 400
    return jsonify(res.data[0]), 201

@app.route('/api/requests/<int:req_id>', methods=['PUT'])
def update_request(req_id):
    """Update the document request with the given ID."""
    data = request.json
    updates = {
        "name":          data['name'],
        "address":       data['address'],
        "birthdate":     data['birthdate'],
        "start_living":  data['startLiving'],
        "purpose":       data['purpose'],
        "age":           data['age'],
        "guardian_name": data.get('guardianName', None),
        "document_type": data['documentType'],
        "status":        data.get('status', 'Pending')
    }
    res = supabase.table('document_requests') \
                  .update(updates) \
                  .select('*') \
                  .eq('id', req_id) \
                  .execute()
    
    if res.error:
        return jsonify({"error": res.error.message}), 400
    return jsonify(res.data[0]), 200

@app.route('/api/requests/<int:req_id>', methods=['DELETE'])
def delete_request(req_id):
    """Delete the document request with the given ID."""
    res = supabase.table('document_requests') \
                  .delete() \
                  .eq('id', req_id) \
                  .execute()
    if res.error:
        return jsonify({"error": res.error.message}), 400
    return '', 204

if __name__ == "__main__":
    app.run(debug=True)
