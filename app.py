from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

# Initialiser l'application Flask
app = Flask(__name__)
app.secret_key = 'bddpascal'

# Configurer la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser SQLAlchemy
db = SQLAlchemy(app)

# Définir la table User pour la base de données
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    deposit = db.Column(db.Float, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)  # Relation avec les transactions

# Définir la table Transaction pour l'historique
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # "Dépôt" ou "Retrait"
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    balance_after = db.Column(db.Float, nullable=False)  # Solde après l'opération

# Définir la table Wallet pour la base de données
class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)

# Créer les tables si elles n'existent pas
with app.app_context():
    db.create_all()

# Page d'accueil
@app.route('/home/<int:user_id>')
def home(user_id):
    user = User.query.get(user_id)
    wallet = Wallet.query.filter_by(name=user.name, surname=user.surname, dob=user.dob).first()
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).limit(10).all()
    return render_template('home.html', user=user, wallet=wallet, transactions=transactions)

# Page d'inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        dob = request.form['dob']
        deposit = 0.0  # Le solde initial dans la banque est toujours 0
        password = request.form['password']
        wallet_id = request.form['wallet_id']

        wallet = Wallet.query.get(wallet_id)

        if not wallet:
            print(f"Wallet ID {wallet_id} introuvable.")
            error = "Informations du Wallet incorrectes."
            return render_template('register.html', error=error)

        if wallet.name != name or wallet.surname != surname or wallet.dob != dob:
            print("Les informations du Wallet ne correspondent pas.")
            error = "Les informations saisies ne correspondent pas au Wallet."
            return render_template('register.html', error=error)

        # Validation de la complexité du mot de passe
        import re
        password_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$')
        if not password_regex.match(password):
            error = "Le mot de passe ne respecte pas les critères de sécurité."
            return render_template('register.html', error=error)

        hashed_password = generate_password_hash(password)
        new_user = User(name=name, surname=surname, dob=dob, deposit=deposit, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        initial_transaction = Transaction(
            user_id=new_user.id,
            transaction_type="Dépôt initial",
            amount=deposit,
            balance_after=deposit
        )
        db.session.add(initial_transaction)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(name=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('verify_2fa'))  # Redirige vers la vérification 2FA
        else:
            error = "Nom utilisateur ou mot de passe incorrect."

    return render_template('login.html', error=error)

# Vérifier le code 2FA
@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if request.method == 'POST':
        entered_code = request.form['code']
        stored_code = session.get('2fa_code')
        user_id = session.get('user_id')

        if entered_code == str(stored_code):
            session.pop('2fa_code', None)  # Supprime le code après validation
            return redirect(url_for('home', user_id=user_id))
        else:
            error = "Code incorrect. Veuillez réessayer."
            return render_template('verify_2fa.html', error=error)

    return render_template('verify_2fa.html')

# Générer un code 2FA
@app.route('/generate_code', methods=['GET'])
def generate_code():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    code = random.randint(100000, 999999)
    session['2fa_code'] = code
    session['2fa_code_expiry'] = (datetime.utcnow() + timedelta(minutes=5)).timestamp()  # Durée de validité : 5 minutes
    return render_template('generate_code.html', code=code)

@app.route('/settings/<int:user_id>', methods=['GET', 'POST'])
def settings(user_id):
    user = User.query.get(user_id)
    wallet = Wallet.query.filter_by(name=user.name, surname=user.surname, dob=user.dob).first()
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        new_name = request.form['name']
        new_surname = request.form['surname']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Mise à jour du nom et prénom dans la table User
        user.name = new_name
        user.surname = new_surname

        # Mise à jour du mot de passe si les mots de passe correspondent
        if new_password:
            if new_password == confirm_password:
                user.password = generate_password_hash(new_password)
            else:
                return render_template(
                    'settings.html', 
                    user=user, 
                    error="Les mots de passe ne correspondent pas."
                )

        # Mise à jour des informations du Wallet
        if wallet:
            wallet.name = new_name
            wallet.surname = new_surname
            db.session.commit()

        # Sauvegarder les modifications dans la table User
        db.session.commit()

        # Rediriger vers la page d'accueil après succès
        return redirect(url_for('home', user_id=user.id))

    return render_template('settings.html', user=user)

@app.route('/update_balance/<int:user_id>', methods=['POST'])
def update_balance(user_id):
    user = User.query.get(user_id)
    wallet = Wallet.query.filter_by(name=user.name, surname=user.surname, dob=user.dob).first()

    # Récupérer les informations du formulaire
    action = request.form['action']
    amount = float(request.form['amount'])

    if action == 'add':  # Ajouter de l'argent
        user.deposit += amount
        wallet.amount -= amount
        transaction_type = "Transfert vers Banque"
    elif action == 'subtract':  # Retirer de l'argent
        if amount > user.deposit:
            return "Montant insuffisant sur le compte bancaire.", 400
        user.deposit -= amount
        wallet.amount += amount
        transaction_type = "Transfert vers Wallet"

    # Enregistrer la transaction
    new_transaction = Transaction(
        user_id=user.id,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=user.deposit
    )
    db.session.add(new_transaction)
    db.session.commit()

    return redirect(url_for('home', user_id=user.id))

# Page de déconnexion
@app.route('/logout')
def logout():
    return redirect(url_for('login'))

# Exécuter l'application
if __name__ == '__main__':
    app.run(debug=True)