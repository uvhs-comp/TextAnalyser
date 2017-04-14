import sqlite3
FILE = "user_text.sqlite"


class Create_Database:

    def __init__(self):
        self.connection = sqlite3.connect(FILE)
        self.cursor = self.connection.cursor()

    def create(self):
        self.users()
        self.texts()
        self.user_text()
        self.notifcations()
        self.categories()
        self.keywords()
        self.word_text()

    def users(self):
        self.cursor.execute("""CREATE TABLE User (UID INTEGER PRIMARY KEY AUTOINCREMENT,
                               UserName VARCHAR(30) NOT NULL,
                               Email VARCHAR(50),
                               Password  VARCHAR(100) NOT NULL);""")

    def texts(self):
        self.cursor.execute("""CREATE TABLE Text (TID INTEGER PRIMARY KEY AUTOINCREMENT,
                               UID INTEGER,
                               TextTitle VARCHAR(100) NOT NULL,
                               FHC  VARCHAR(100),
                               CID INTEGER,
                               ReadingAge REAL,
                               Sentiment REAL,
                               Alliteration INTEGER(1),
                               Antithesis INTEGER(1),
                               Juxtaposition INTEGER(1),
                               FOREIGN KEY(UID) REFERENCES User(UID)
                               FOREIGN KEY(CID) REFERENCES Categories(CID));""")

    def user_text(self):
        self.cursor.execute("""CREATE TABLE User_Text(
                               UID INTEGER,
                               TID INTEGER,
                               FOREIGN KEY(UID) REFERENCES User(UID),
                               FOREIGN KEY(TID) REFERENCES Text(TID),
                               PRIMARY KEY (UID, TID));
                               """)

    def categories(self):
        self.cursor.execute("""CREATE TABLE Categories(
                               CID INTEGER PRIMARY KEY AUTOINCREMENT,
                               Cat VARCHAR(50));""")

    def notifcations(self):
        self.cursor.execute("""CREATE TABLE Notifications(
                               UID INTEGER,
                               MESSAGE VARCHAR(140),
                               FOREIGN KEY(UID) REFERENCES User(UID));
                               """)

    def keywords(self):
        self.cursor.execute("""CREATE TABLE Keywords(
                               WID INTEGER PRIMARY KEY AUTOINCREMENT,
                               Word VARCHAR(50));""")

    def word_text(self):
        self.cursor.execute("""CREATE TABLE text_word(
                               TID INTEGER,
                               WID INTEGER,
                               Score INTEGER,
                               FOREIGN KEY(TID) REFERENCES Text(TID),
                               FOREIGN KEY(WID) REFERENCES Keywords(WID),
                               PRIMARY KEY (WID, TID));""")

db = Create_Database()
db.create()
