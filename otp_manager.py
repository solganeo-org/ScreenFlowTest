# otp_manager.py - Version simplifiée avec Flask-Limiter
import os
import random
import string
import smtplib
import hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class OTPManager:
    def __init__(self):
        """
        Initialisation du gestionnaire OTP simplifié
        Rate limiting géré par Flask-Limiter (suppression de 100+ lignes de code)
        """
        # Stockage temporaire des codes OTP (dictionnaire en mémoire)
        self.otp_storage = {}
        
        # Configuration de sécurité (rate limiting supprimé - géré par Flask-Limiter)
        self.ALLOWED_DOMAINS = ['solganeo.com', 'experts-comptables.org']  # Domaines autorisés
        self.OTP_LENGTH = 6                    # Longueur du code OTP
        self.OTP_VALIDITY_MINUTES = 5          # Validité en minutes
        self.MAX_ATTEMPTS = 3                  # Tentatives maximum par code

    def _hash_email(self, email):
        """
        Crée un hash SHA256 de l'email pour la sécurité
        Args:
            email (str): Adresse email à hasher
        Returns:
            str: Hash SHA256 de l'email en minuscules
        """
        return hashlib.sha256(email.lower().encode()).hexdigest()

    def _is_email_allowed(self, email):
        """
        Vérifie si le domaine de l'email est dans la liste autorisée
        Args:
            email (str): Adresse email à vérifier
        Returns:
            bool: True si domaine autorisé, False sinon
        """
        # Extraction du domaine après le @
        domain = email.split('@')[-1].lower()
        # Vérification dans la liste des domaines autorisés
        return domain in self.ALLOWED_DOMAINS

    def generate_otp(self):
        """
        Génère un code OTP numérique aléatoire
        Returns:
            str: Code OTP de 6 chiffres
        """
        # Génération d'un code numérique aléatoire
        return ''.join(random.choices(string.digits, k=self.OTP_LENGTH))

    def send_otp_email(self, email, otp_code):
        """
        Envoie le code OTP par email avec template HTML CNOEC
        Rate limiting géré automatiquement par Flask-Limiter
        Args:
            email (str): Adresse email destinataire
            otp_code (str): Code OTP à 6 chiffres
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Récupération des variables d'environnement Gmail
            gmail_user = os.environ.get('GMAIL_USER')      # noreply@solganeo.com
            gmail_password = os.environ.get('GMAIL_PASSWORD')  # Mot de passe application

            # Vérification de la configuration email
            if not gmail_user or not gmail_password:
                return {
                    'success': False, 
                    'message': 'Erreur de service. Contactez l\'administrateur.'
                }

            # Création du message email MIME
            msg = MIMEMultipart('alternative')  # Support texte + HTML
            msg['From'] = gmail_user            # Expéditeur
            msg['To'] = email                   # Destinataire
            msg['Subject'] = "Code de vérification - Portail CNOEC"  # Sujet

            # Template HTML avec design CNOEC (couleurs et structure institutionnelles)
            html_template = f"""
            <table width="100%" align="center" border="0" cellspacing="0" cellpadding="0" style="min-width: 600px">
                <tbody>
                <tr>
                    <td align="center" valign="top" style="min-width: 600px">
                    
                    <!-- Header avec couleurs CNOEC -->
                    <table width="600" align="center" border="0" cellspacing="0" cellpadding="0" style="box-shadow: 0 5px 10px rgba(0, 46, 95, 0.15)">
                        <tbody>
                        <tr>
                            <td align="center" style="padding: 25px 0; background: linear-gradient(135deg, #002e5f 0%, #0054a6 100%);">
                            <!-- Logo CNOEC en texte (évite problèmes d'images dans emails) -->
                            <div style="color: white; font-family: 'Montserrat', Arial, sans-serif; font-size: 24px; font-weight: 700;">
                                CONSEIL NATIONAL DE L'ORDRE<br>
                                <span style="color: #c89d51;">DES EXPERTS-COMPTABLES</span>
                            </div>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    
                    <!-- Contenu principal -->
                    <table width="600" align="center" border="0" cellspacing="0" cellpadding="0">
                        <tbody>
                        <!-- Titre principal -->
                        <tr>
                            <td align="center" valign="middle" style="font-family: 'Montserrat', Arial, Helvetica, sans-serif; font-size: 28px; color: #002e5f; line-height: 34px; font-weight: 600; letter-spacing: 0; padding-top: 30px">
                            Authentification Sécurisée
                            <br>
                            <hr style="width: 15%; border: 2px solid #c89d51; border-radius: 2px; margin: 15px auto;">
                            </td>
                        </tr>
                        
                        <!-- Description -->
                        <tr>
                            <td align="center" valign="top" bgcolor="#ffffff" style="font-family: 'Montserrat', Arial, Helvetica, sans-serif; font-size: 16px; line-height: 24px; color: #283747; padding: 20px 30px;">
                            Voici votre code de vérification<br>
                            pour accéder au <strong>Portail Sécurisé</strong><br>
                            du <strong>Conseil National de l'Ordre des Experts-Comptables</strong>
                            </td>
                        </tr>
                        
                        <!-- Code OTP avec style CNOEC -->
                        <tr>
                            <td style="padding: 0 0 20px">
                            <table bgcolor="#f8fafd" border="0" align="center" cellpadding="0" cellspacing="0" style="border-radius: 12px; border: 2px solid #002e5f;">
                                <tbody>
                                <tr>
                                    <!-- Icône de sécurité -->
                                    <td valign="middle" style="font-family: 'Montserrat', Arial, Helvetica, sans-serif; padding: 15px 20px;">
                                    <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #002e5f 0%, #0054a6 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                        <span style="color: white; font-size: 20px;">🔒</span>
                                    </div>
                                    </td>
                                    <!-- Code OTP principal -->
                                    <td valign="middle" style="font-family: 'Montserrat', Arial, Helvetica, sans-serif; font-size: 42px; line-height: 48px; color: #002e5f; font-weight: 700; letter-spacing: 8px; padding: 15px 20px 15px 0;">
                                    {otp_code}
                                    </td>
                                </tr>
                                </tbody>
                            </table>
                            </td>
                        </tr>
                        
                        <!-- Information de validité -->
                        <tr>
                            <td align="center" valign="top" bgcolor="#ffffff" style="font-family: 'Montserrat', Arial, Helvetica, sans-serif; font-size: 18px; line-height: 24px; color: #c89d51; font-weight: 600; padding: 0 25px 25px">
                            ⏱️ Ce code expire dans 5 minutes
                            </td>
                        </tr>
                        
                        <!-- Instructions de sécurité -->
                        <tr>
                            <td align="center" valign="top" bgcolor="#ffffff" style="font-family: 'Montserrat', Arial, Helvetica, sans-serif; font-size: 14px; line-height: 22px; color: #5d6c7b; padding: 0 30px 30px">
                            Saisissez ce code dans le portail pour accéder à vos services.<br>
                            <strong>Pour votre sécurité :</strong> Ne partagez jamais ce code.<br>
                            Si vous n'avez pas demandé ce code, ignorez cet email.
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    
                    <!-- Footer institutionnel CNOEC -->
                    <table width="600" align="center" border="0" cellspacing="0" cellpadding="0">
                        <tbody>
                        <tr>
                            <td bgcolor="#002e5f" valign="middle" style="font-family: 'Montserrat', Arial, Helvetica, sans-serif; font-size: 13px; line-height: 18px; text-align: center; color: white; padding: 20px;">
                            <strong>Conseil National de l'Ordre des Experts-Comptables</strong><br>
                            153 rue de Courcelles - 75017 Paris<br>
                            <span style="color: #c89d51;">www.experts-comptables.fr</span>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    
                    </td>
                </tr>
                </tbody>
            </table>
            """

            # Création de la partie HTML du message
            html_part = MIMEText(html_template, 'html', 'utf-8')
            msg.attach(html_part)  # Attachement au message principal

            # Connexion et envoi via serveur Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)    # Serveur Gmail port 587
            server.starttls()                               # Activation chiffrement TLS
            server.login(gmail_user, gmail_password)        # Authentification Gmail
            server.send_message(msg)                        # Envoi du message
            server.quit()                                   # Fermeture propre connexion

            # Retour de succès avec message générique de sécurité
            return {
                'success': True, 
                'message': 'Si l\'adresse email est valide, un code a été envoyé.'
            }

        except smtplib.SMTPAuthenticationError:
            # Erreur d'authentification Gmail - message générique pour sécurité
            return {
                'success': False, 
                'message': 'Erreur de service. Contactez l\'administrateur.'
            }
        except smtplib.SMTPException as e:
            # Autres erreurs SMTP - message générique
            return {
                'success': False, 
                'message': 'Erreur de service. Contactez l\'administrateur.'
            }
        except Exception as e:
            # Toute autre erreur - message générique
            return {
                'success': False, 
                'message': 'Erreur de service. Contactez l\'administrateur.'
            }

    def verify_otp(self, email, provided_code):
        """
        Vérifie si le code OTP fourni est valide pour cet email
        Rate limiting des tentatives géré par Flask-Limiter
        Args:
            email (str): Adresse email de l'utilisateur
            provided_code (str): Code OTP saisi par l'utilisateur
        Returns:
            dict: {'success': bool, 'message': str}
        """
        # Message générique pour toutes les erreurs (sécurité)
        generic_error = 'Code invalide. Contactez l\'administrateur.'

        # Vérification du domaine email autorisé
        if not self._is_email_allowed(email):
            return {'success': False, 'message': generic_error}

        # Hash de l'email pour retrouver les données
        email_hash = self._hash_email(email)

        # Vérification de l'existence du code OTP
        if email_hash not in self.otp_storage:
            return {'success': False, 'message': generic_error}

        # Récupération des données OTP stockées
        otp_data = self.otp_storage[email_hash]
        current_time = datetime.now()

        # Vérification de l'expiration
        if current_time > otp_data['expires']:
            del self.otp_storage[email_hash]  # Nettoyage des données expirées
            return {'success': False, 'message': generic_error}

        # Vérification du nombre de tentatives
        if otp_data['attempts'] >= self.MAX_ATTEMPTS:
            del self.otp_storage[email_hash]  # Nettoyage après échecs multiples
            return {'success': False, 'message': generic_error}

        # Vérification du code OTP
        if otp_data['otp'] == provided_code.strip():
            # Code correct - suppression immédiate (usage unique)
            del self.otp_storage[email_hash]
            return {
                'success': True,
                'message': 'Authentification réussie.'
            }
        else:
            # Code incorrect - incrémentation du compteur
            otp_data['attempts'] += 1
            return {'success': False, 'message': generic_error}

    def store_otp(self, email, otp_code):
        """
        Stocke le code OTP avec timestamp d'expiration (version simplifiée)
        Rate limiting géré par Flask-Limiter (suppression de la gestion manuelle)
        Args:
            email (str): Adresse email
            otp_code (str): Code OTP généré
        Returns:
            dict: {'success': bool, 'message': str}
        """
        # Hash de l'email pour la sécurité
        email_hash = self._hash_email(email)

        # Calcul du timestamp d'expiration
        expires_at = datetime.now() + timedelta(minutes=self.OTP_VALIDITY_MINUTES)

        # Stockage des données OTP en mémoire (simplifié - plus de rate limiting manuel)
        self.otp_storage[email_hash] = {
            'otp': otp_code,                # Code OTP
            'expires': expires_at,          # Timestamp d'expiration
            'attempts': 0,                  # Compteur de tentatives
            'created_at': datetime.now()    # Timestamp de création
        }

        return {
            'success': True,
            'message': 'Code généré avec succès.'
        }

    def cleanup_expired_data(self):
        """
        Nettoie les données expirées du stockage (version simplifiée)
        Plus de nettoyage des rate limits (géré par Flask-Limiter)
        """
        current_time = datetime.now()
        expired_hashes = []

        # Identification des codes expirés
        for email_hash, otp_data in self.otp_storage.items():
            if current_time > otp_data['expires']:
                expired_hashes.append(email_hash)

        # Suppression des données expirées
        for email_hash in expired_hashes:
            del self.otp_storage[email_hash]

        return len(expired_hashes)  # Nombre d'éléments nettoyés