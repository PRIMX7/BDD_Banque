#code pour lancer le serveur 
python -m flask run

#code pour lancer le script test_db
python test_db.py  

#compiler sur git 
git add .
git commit -m "Bdd Bank"
git pull
git push


********************************************************
#base de données 
cd instance
sqlite3 users.db

.tables

select * from user;
select * from Wallet;


#add wallet 
INSERT INTO Wallet (name, surname, dob, amount) VALUES ('Dupont', 'Jean', '1990-05-15', 5000.0);

#drop user
DELETE FROM user WHERE id=3;

#update wallet 
UPDATE Wallet SET amount = 2000.0 WHERE id=3;

#Voir les variables de la table Wallet ou user
PRAGMA table_info(Wallet);
PRAGMA table_info(user);

Valeurs : Type|NotNull(0)|ValeurParDefaut(0.0euros)|CléPrimaire(0=non)