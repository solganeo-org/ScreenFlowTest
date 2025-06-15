from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import random
from itsdangerous import TimestampSigner

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
signer = TimestampSigner(app.secret_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        otp = str(random.randint(100000, 999999))
        signed_otp = signer.sign(otp).decode()

        # Stocker OTP signé et email en session
        session['signed_otp'] = signed_otp
        session['email'] = email

        # (Simuler l'envoi - afficher dans les logs Heroku)
        print(f"Envoyer OTP à {email}: {otp}")

        return redirect(url_for('verify'))
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        otp_entered = request.form['otp']
        signed_otp = session.get('signed_otp')
        if not signed_otp:
            flash("Session expirée. Recommencez.")
            return redirect(url_for('login'))
        try:
            original_otp = signer.unsign(signed_otp, max_age=300).decode()
            if otp_entered == original_otp:
                session['authenticated'] = True
                return redirect(url_for('dynamic_page'))
            else:
                flash("OTP incorrect.")
        except Exception:
            flash("OTP expiré ou invalide.")
            return redirect(url_for('login'))
    return render_template('verify.html')

@app.route('/dynamic-page')
def dynamic_page():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('dynamic_page.html')

# Point d'entrée pour Heroku
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
