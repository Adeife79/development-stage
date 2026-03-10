from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

businesses = []


@app.route('/')
def home():
    return render_template('app.html')

@app.route("/api/business/register", methods=["POST"])
def register_business():
    data = request.get_json()
    
    business_name = data.get("businessName")
    owner_name = data.get("ownerName")
    email = data.get("email")
    tel = data.get("tel")
    password = data.get("password")
    confirm_password = data.get("confirmPassword")
    business_type = data.get("businessType")
    terms_accepted = data.get("terms")
    newsletter_opt_in = data.get("newsletter")
    
    if not all([business_name, owner_name, email, tel, password, confirm_password, business_type, terms_accepted is not None, newsletter_opt_in is not None]):
        return jsonify({"message": "All fields are required."}), 400
    
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match."})
    #else:
        #return jsonify({"message": "Passwords match."})

    new_business = {
        "businessName": business_name,
        "ownerName": owner_name,
        "email": email,
        "tel": tel,
        "password": password,
        "businessType": business_type,
        "termsAccepted": terms_accepted,
        "newsletterOptIn": newsletter_opt_in
    }
    
    businesses.append(new_business)
    print(f"Registered new business: {new_business}")
    
    
    return jsonify({"message": "Business registered successfully."}), 201
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085, debug=True)    
    