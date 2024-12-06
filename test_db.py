from app import app, db, User  # Assure-toi que tu importes app, db et User depuis ton fichier app.py

# Crée un contexte d'application Flask
with app.app_context():
    # Récupérer tous les utilisateurs
    users = User.query.all()
    for user in users:
        # Afficher le nom d'utilisateur et le solde actuel
        print(f"Nom: {user.name} {user.surname}, Solde actuel: {user.deposit} €")
