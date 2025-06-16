# app.py - Application Flask avec authentification OTP et Flask-Limiter
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import os
from otp_manager import OTPManager

# Initialisation de l'application Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configuration de la clé secrète pour les sessions (depuis variable d'environnement)
app.secret_key = os.environ.get('SECRET_KEY', 'cle-temporaire-pour-developpement-seulement')

# === CONFIGURATION FLASK-LIMITER ===

# Initialisation de Flask-Limiter avec stockage Redis (production) ou mémoire (développement)
# === CONFIGURATION FLASK-LIMITER === (CORRECT)
limiter = Limiter(
    key_func=get_remote_address,  # Limitation par adresse IP
    default_limits=["200 per day", "50 per hour"],  # Limites globales par défaut
    storage_uri=os.environ.get("REDIS_URL", "memory://"),  # Redis en prod, mémoire en dev
    strategy="fixed-window"  # Stratégie de fenêtre fixe
)

# Initialisation avec l'app Flask
limiter.init_app(app)


# Instance unique du gestionnaire OTP (créée une seule fois)
otp_manager = OTPManager()

# === FONCTIONS UTILITAIRES DE SESSION ===

def is_session_valid():
    """
    Vérifie si la session OTP de l'utilisateur est encore valide
    Contrôle l'authentification ET l'expiration temporelle
    Returns:
        bool: True si session valide et non expirée, False sinon
    """
    # Vérification 1: L'utilisateur est-il authentifié via OTP ?
    if not session.get('otp_authenticated'):
        return False  # Pas d'authentification OTP

    # Vérification 2: Y a-t-il un timestamp d'expiration en session ?
    session_expires = session.get('otp_expires')
    if not session_expires:
        return False  # Pas de timestamp d'expiration

    # Vérification 3: La session n'a-t-elle pas expiré ?
    try:
        # Conversion du timestamp ISO en objet datetime
        expires_datetime = datetime.fromisoformat(session_expires)
        # Comparaison avec l'heure actuelle
        return datetime.now() < expires_datetime
    except (ValueError, TypeError):
        # Format de date invalide ou corrompu - session non valide
        return False

def get_session_status():
    """
    Calcule et retourne le statut détaillé de la session OTP actuelle
    Utilisé pour les vérifications JavaScript et l'affichage des warnings
    Returns:
        dict: {
            'valid': bool,              # Session encore valide ?
            'expires_in_minutes': int,  # Minutes restantes
            'warning': bool,            # Faut-il afficher un warning ?
            'message': str              # Message descriptif
        }
    """
    # Cas 1: Utilisateur non authentifié
    if not session.get('otp_authenticated'):
        return {
            'valid': False,
            'expires_in_minutes': 0,
            'warning': False,
            'message': 'Non authentifié'
        }

    # Cas 2: Pas de timestamp d'expiration en session
    session_expires = session.get('otp_expires')
    if not session_expires:
        return {
            'valid': False,
            'expires_in_minutes': 0,
            'warning': False,
            'message': 'Session corrompue'
        }

    try:
        # Conversion du timestamp et calcul du temps restant
        expires_datetime = datetime.fromisoformat(session_expires)
        time_left = expires_datetime - datetime.now()  # Différence temporelle

        # Cas 3: Session déjà expirée
        if time_left.total_seconds() <= 0:
            return {
                'valid': False,
                'expires_in_minutes': 0,
                'warning': False,
                'message': 'Session expirée'
            }

        # Cas 4: Session valide - calcul des minutes restantes
        minutes_left = int(time_left.total_seconds() / 60)  # Conversion secondes → minutes

        return {
            'valid': True,
            'expires_in_minutes': minutes_left,
            'warning': minutes_left <= 15,  # Warning si 15 minutes ou moins
            'message': f'{minutes_left} minute(s) restante(s)'
        }

    except (ValueError, TypeError):
        # Erreur de format de date - session corrompue
        return {
            'valid': False,
            'expires_in_minutes': 0,
            'warning': False,
            'message': 'Format de session invalide'
        }

def renew_session():
    """
    Renouvelle la session OTP pour 2 heures supplémentaires à partir de maintenant
    Appelé à chaque interaction utilisateur pour maintenir la session active
    Returns:
        bool: True si renouvellement réussi, False si pas d'authentification
    """
    # Vérification que l'utilisateur est bien authentifié
    if session.get('otp_authenticated'):
        # Reset du chrono à 2 heures à partir de l'instant présent
        new_expiration = datetime.now() + timedelta(hours=2)
        session['otp_expires'] = new_expiration.isoformat()  # Format ISO pour stockage
        return True  # Renouvellement réussi
    return False  # Pas d'authentification active

# === ROUTES PRINCIPALES ===

@app.route("/")
def home():
    """
    Route principale - accès à index.html protégé par authentification OTP
    Fonctionnalités:
    - Vérification de session valide
    - Renouvellement automatique du chrono à chaque chargement
    - Redirection vers auth si pas de session
    """
    # Étape 1: Vérification de la validité de la session OTP
    if not is_session_valid():
        # Session invalide, expirée ou inexistante → redirection vers authentification
        return redirect(url_for('auth_otp'))

    # Étape 2: Session valide → renouvellement automatique du chrono (2h supplémentaires)
    renew_session()

    # Étape 3: Récupération du statut de session pour le JavaScript côté client
    session_status = get_session_status()

    # Étape 4: Rendu de la page protégée avec injection des données de session
    return render_template("index.html", session_status=session_status)

@app.route("/auth-otp")
def auth_otp():
    """
    Page d'authentification OTP - formulaire de saisie email et code
    Si l'utilisateur est déjà authentifié, redirection vers page protégée
    """
    # Si déjà une session valide, pas besoin de re-authentification
    if is_session_valid():
        return redirect(url_for('home'))  # Redirection vers page protégée

    # Affichage du formulaire d'authentification OTP
    return render_template("auth_otp.html")

# === ROUTES API AVEC FLASK-LIMITER ===

@app.route("/api/send-otp", methods=['POST'])
@limiter.limit("5 per hour")  # ← LIMITATION AUTOMATIQUE : 5 requêtes par heure par IP
@limiter.limit("2 per minute")  # ← LIMITATION SUPPLÉMENTAIRE : 2 requêtes par minute par IP
def api_send_otp():
    """
    API REST pour déclencher l'envoi d'un code OTP par email
    PROTECTION FLASK-LIMITER : 5/heure + 2/minute par IP
    
    Méthode: POST
    Content-Type: application/json
    Body: {"email": "user@domain.com"}
    
    Fonctionnalités:
    - Validation du format email
    - Rate limiting automatique (plus besoin de check manuel)
    - Génération et stockage du code OTP
    - Envoi par email avec template CNOEC
    """
    try:
        # Étape 1: Récupération et validation des données JSON de la requête
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'message': 'Données JSON manquantes dans la requête.'
            }), 400  # HTTP 400 Bad Request

        # Étape 2: Extraction et nettoyage de l'adresse email
        email = data.get('email', '').strip().lower()  # Suppression espaces + minuscules
        if not email:
            return jsonify({
                'success': False, 
                'message': 'Adresse email requise.'
            }), 400

        # Étape 3: Validation basique du format email (présence @ et domaine)
        if '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify({
                'success': False, 
                'message': 'Format d\'adresse email invalide.'
            }), 400

        # Étape 4: SUPPRIMÉ - Plus besoin de check_rate_limit manuel (Flask-Limiter le gère)
        
        # Étape 5: Génération d'un nouveau code OTP aléatoire (6 chiffres)
        otp_code = otp_manager.generate_otp()

        # Étape 6: Stockage sécurisé du code avec expiration (5 minutes)
        store_result = otp_manager.store_otp(email, otp_code)
        if not store_result['success']:
            return jsonify({
                'success': False, 
                'message': 'Erreur de stockage. Contactez l\'administrateur.'
            }), 500  # HTTP 500 Internal Server Error

        # Étape 7: Envoi du code par email avec template HTML CNOEC
        send_result = otp_manager.send_otp_email(email, otp_code)

        # Étape 8: Stockage temporaire de l'email en session pour la vérification
        session['otp_email'] = email  # Nécessaire pour verify_otp

        # Étape 9: Retour du résultat (succès ou échec) avec code HTTP approprié
        return jsonify({
            'success': send_result['success'],
            'message': send_result['message']
        }), 200 if send_result['success'] else 500

    except Exception as e:
        # Gestion globale des erreurs inattendues avec message générique de sécurité
        return jsonify({
            'success': False, 
            'message': 'Erreur de service. Contactez l\'administrateur.'
        }), 500

@app.route("/api/verify-otp", methods=['POST'])
@limiter.limit("10 per hour")  # ← LIMITATION : 10 tentatives de vérification par heure par IP
@limiter.limit("3 per minute")  # ← LIMITATION : 3 tentatives par minute par IP
def api_verify_otp():
    """
    API REST pour vérifier un code OTP saisi par l'utilisateur
    PROTECTION FLASK-LIMITER : 10/heure + 3/minute par IP
    
    Méthode: POST
    Content-Type: application/json
    Body: {"otp": "123456"}
    
    Fonctionnalités:
    - Validation du format du code (6 chiffres)
    - Rate limiting automatique des tentatives
    - Vérification contre le code stocké
    - Création de session authentifiée si code correct
    """
    try:
        # Étape 1: Récupération et validation des données JSON
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'message': 'Données JSON manquantes.'
            }), 400

        # Étape 2: Extraction et nettoyage du code OTP fourni par l'utilisateur
        provided_otp = data.get('otp', '').strip()  # Suppression des espaces
        if not provided_otp:
            return jsonify({
                'success': False, 
                'message': 'Code OTP requis.'
            }), 400

        # Étape 3: Validation du format du code (exactement 6 chiffres)
        if len(provided_otp) != 6 or not provided_otp.isdigit():
            return jsonify({
                'success': False, 
                'message': 'Code invalide. Contactez l\'administrateur.'  # Message générique
            }), 400

        # Étape 4: Récupération de l'email depuis la session temporaire
        email = session.get('otp_email')
        if not email:
            return jsonify({
                'success': False, 
                'message': 'Session expirée. Recommencez la procédure.'
            }), 400

        # Étape 5: Vérification du code OTP via le gestionnaire sécurisé
        verify_result = otp_manager.verify_otp(email, provided_otp)

        # Étape 6a: Code correct → création de la session authentifiée
        if verify_result['success']:
            # Marquage de l'authentification réussie
            session['otp_authenticated'] = True
            # Stockage de l'email vérifié
            session['otp_email_verified'] = email
            # Définition de l'expiration de session (2 heures à partir de maintenant)
            session['otp_expires'] = (datetime.now() + timedelta(hours=2)).isoformat()

            # Nettoyage de l'email temporaire (plus besoin)
            session.pop('otp_email', None)

            return jsonify({
                'success': True,
                'message': 'Authentification réussie.',
                'redirect_url': url_for('home')  # URL de redirection pour le JavaScript
            }), 200
        else:
            # Étape 6b: Code incorrect → retour d'erreur avec message générique
            return jsonify({
                'success': False,
                'message': verify_result['message']  # Message sécurisé du gestionnaire
            }), 400

    except Exception as e:
        # Gestion des erreurs inattendues avec message générique
        return jsonify({
            'success': False, 
            'message': 'Erreur de service. Contactez l\'administrateur.'
        }), 500

@app.route("/api/session-status", methods=['GET'])
@limiter.limit("60 per hour")  # ← LIMITATION : 60 vérifications de session par heure par IP
def api_session_status():
    """
    API REST pour vérifier le statut actuel de la session OTP
    PROTECTION FLASK-LIMITER : 60/heure par IP
    Appelée par JavaScript lors des interactions utilisateur
    
    Fonctionnalités:
    - Renouvellement automatique de session si authentifié
    - Retour du temps restant avant expiration
    - Indication de warning si < 15 minutes restantes
    """
    # Étape 1: Renouvellement automatique à chaque interaction utilisateur
    if session.get('otp_authenticated'):
        renew_session()  # Reset du chrono à 2h

    # Étape 2: Calcul et retour du statut détaillé
    status = get_session_status()
    return jsonify(status), 200

# === ROUTES UTILITAIRES ===

@app.route("/logout")
def logout():
    """
    Déconnexion complète - suppression de toutes les données de session OTP
    Redirection vers la page d'authentification
    """
    # Suppression de toutes les clés de session liées à l'OTP
    session.pop('otp_authenticated', None)      # Flag d'authentification
    session.pop('otp_email_verified', None)    # Email vérifié
    session.pop('otp_expires', None)           # Timestamp d'expiration
    session.pop('otp_email', None)             # Email temporaire

    # Redirection vers la page d'authentification
    return redirect(url_for('auth_otp'))

@app.route("/status")
@limiter.limit("30 per hour")  # ← LIMITATION : 30 vérifications de statut par heure par IP
def status():
    """
    Route de diagnostic pour vérifier l'état de l'application
    PROTECTION FLASK-LIMITER : 30/heure par IP
    Utile pour le monitoring, les health checks et le debugging
    """
    return jsonify({
        'status': 'active',                    # Application fonctionnelle
        'session_valid': is_session_valid(),   # État de la session actuelle
        'timestamp': datetime.now().isoformat(), # Horodatage serveur
        'otp_storage_count': len(otp_manager.otp_storage),  # Nombre de codes en mémoire
        'limiter_enabled': True,               # Flask-Limiter actif
        'redis_connected': os.environ.get("REDIS_URL") is not None  # Connexion Redis
    })

# === GESTION DES ERREURS FLASK-LIMITER ===

@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Gestionnaire d'erreur pour les dépassements de rate limiting
    Retourne un message générique de sécurité (pas d'informations techniques)
    """
    return jsonify({
        'success': False,
        'message': 'Trop de tentatives. Contactez l\'administrateur.',
        'error_code': 'RATE_LIMIT_EXCEEDED'
    }), 429

# === NETTOYAGE AUTOMATIQUE ===

# Nettoyage automatique des données expirées (optimisation mémoire)
@app.before_request
def cleanup_expired_otps():
    """
    Hook Flask exécuté avant chaque requête
    Nettoyage périodique des codes OTP expirés pour éviter l'accumulation en mémoire
    Fréquence: 1 fois sur 100 requêtes (pour ne pas impacter les performances)
    """
    import random
    # Nettoyage probabiliste (1% de chance par requête)
    if random.randint(1, 100) == 1:
        cleaned_count = otp_manager.cleanup_expired_data()
        # En mode debug, on pourrait logger le nettoyage
        # print(f"Nettoyage automatique: {cleaned_count} éléments supprimés")

@app.route("/pdf")
def pdf():
    """
    Route protégée - PDF
    Nécessite une authentification OTP valide
    """
    if not is_session_valid():
        return redirect(url_for("auth_otp"))
    
    renew_session()
    session_status = get_session_status()
    
    return render_template("pdf.html", session_status=session_status)



if __name__ == "__main__":
    # Configuration pour le démarrage de l'application
    
    # Port d'écoute: variable Heroku ou 5001 par défaut pour développement local
    port = int(os.environ.get("PORT", 5001))
    
    # Mode debug activé si variable FLASK_ENV=development
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    # Démarrage du serveur Flask
    # host="0.0.0.0" permet l'accès depuis l'extérieur (nécessaire pour Heroku)
    app.run(host="0.0.0.0", port=port, debug=debug_mode)