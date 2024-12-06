from app import app, db, User, Transaction  # Assure-toi que tu importes aussi la classe Transaction

# Crée un contexte d'application Flask
with app.app_context():
    # Récupérer les utilisateurs "test"
    users_to_delete = User.query.filter_by(name='test').all()

    # Supprimer les transactions liées à ces utilisateurs
    for user in users_to_delete:
        transactions_to_delete = Transaction.query.filter_by(user_id=user.id).all()
        for transaction in transactions_to_delete:
            db.session.delete(transaction)  # Supprimer chaque transaction

    # Supprimer les utilisateurs "test"
    for user in users_to_delete:
        db.session.delete(user)

    # Sauvegarder les modifications dans la base de données
    db.session.commit()

    print("Utilisateurs 'test' et leurs transactions supprimés.")
