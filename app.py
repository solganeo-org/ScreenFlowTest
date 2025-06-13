from flask import Flask, render_template, request, redirect, url_for, session
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = "une_clé_ultra_secrète"
serializer = URLSafeTimedSerializer(app.secret_key)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/otp-request')
def otp_request():
    # Simule un envoi OTP (en prod : email/SMS)
    otp = serializer.dumps("user@example.com")
    session['otp'] = otp
    return f"OTP généré : {otp} (dans un vrai projet, envoyé par email/SMS)"

@app.route('/otp-verify', methods=['POST'])
def otp_verify():
    otp = request.form.get('otp')
    try:
        email = serializer.loads(otp, max_age=300)
        session['authenticated'] = True
        return redirect(url_for('dynamic_page'))
    except:
        return "OTP invalide ou expiré", 400

@app.route('/dynamic')
def dynamic_page():
    if not session.get('authenticated'):
        return redirect(url_for('otp_request'))
    return render_template('dynamic_page.html')

if __name__ == "__main__":
    app.run(debug=True)
