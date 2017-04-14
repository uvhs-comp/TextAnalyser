import sqlite3
FILE = "static/db/user_text.sqlite"


class Database:

    def __init__(self):
        self.connection = sqlite3.connect(FILE)
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def addUser(self, data):
        insert_query = """INSERT INTO User (UserName, Email, Password)
                          VALUES (?,?,?);"""
        self.cursor.execute(insert_query, data)
        self.connection.commit()

    def getID(self, username):
        id_query = """SELECT UID
                   FROM User
                   WHERE UserName = ?;"""
        user_id = self.cursor.execute(id_query, [username]).fetchall()[0][0]
        return user_id

    def getTextID(self, title, user_id):
        id_query = """SELECT TID
                      FROM Text
                      WHERE TextTitle = ?
                      AND UID = ?;"""
        return self.cursor.execute(id_query, [title, user_id]).fetchall()[0][0]

    def getAllKeywords(self):
        query = """SELECT Word
                   FROM Keywords;"""
        return [x[0] for x in self.cursor.execute(query)]

    def addKeyword(self, word):
        query = """INSERT INTO Keywords(Word)
                   VALUES(?)"""
        self.cursor.execute(query, [word])
        self.connection.commit()

    def getKeywordID(self, word):
        query = """SELECT WID
                   FROM Keywords
                   WHERE Word = ?;"""
        return self.cursor.execute(query, [word]).fetchall()[0][0]

    def addToTextWords(self, tid, wid, score):
        query = """INSERT INTO text_word(TID, WID, Score)
                   VALUES(?, ?, ?);"""
        self.cursor.execute(query, [tid, wid, score])
        self.connection.commit()

    def addKeyWords(self, tid, keywords):
        current_keywords = self.getAllKeywords()
        for keyword in keywords:
            word = keyword[0]
            if word not in current_keywords:
                self.addKeyword(word)
            wid = self.getKeywordID(word)
            self.addToTextWords(tid, wid, keyword[1])

    def addText(self, data, keywords):
        query = """INSERT INTO Text(UID, TextTitle, FHC, CID, ReadingAge,
                                    Sentiment, Alliteration, Antithesis, Juxtaposition)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        self.cursor.execute(query, data)
        self.connection.commit()
        tid = self.getTextID(data[1], data[0])
        self.addKeyWords(tid, keywords)

    def clearShares(self, text_id):
        query = """DELETE FROM User_Text
                   WHERE TID = ?;"""
        self.cursor.execute(query, [text_id])
        self.connection.commit()

    def clearKeywords(self, text_id):
        query = """DELETE FROM text_word
                   WHERE TID = ?;"""
        self.cursor.execute(query, [text_id])
        self.connection.commit()

    def deleteText(self, title, user_id):
        text_id = self.getTextID(title, user_id)
        self.clearShares(text_id)
        self.clearKeywords(text_id)
        query = """DELETE FROM Text
                   WHERE TID = ?;"""
        self.cursor.execute(query, [text_id])
        self.connection.commit()

    def getOwner(self, title, user_id):
        query = """SELECT User.UserName
                   FROM User, Text, User_Text
                   WHERE Text.UID = User.UID
                   AND TextTitle = ?
                   AND User_Text.TID = Text.TID
                   AND User_Text.UID = ?;"""
        return self.cursor.execute(query, [title, user_id]).fetchall()[0][0]

    def getTextOwner(self, title, username):
        user_id = self.getID(username)
        owned_texts = [x[0] for x in self.getOwnedTexts(user_id)]
        if title in owned_texts:
            return username
        owner = self.getOwner(title, user_id)
        return owner

    def getOwnedTexts(self, user_id, search_string=""):
        search_string = "%" + search_string + "%"
        query = """SELECT TextTitle, FHC
                   FROM Text
                   WHERE UID = ?
                   AND TextTitle like ?;"""
        return self.cursor.execute(query, [user_id, search_string]).fetchall()

    def getSharedTexts(self, user_id, search_string=""):
        search_string = "%" + search_string + "%"
        query = """SELECT Text.TextTitle, Text.FHC
                   FROM Text, User_Text
                   WHERE User_Text.UID = ?
                   AND Text.TID = User_Text.TID
                   AND Text.TextTitle like ?;"""
        return self.cursor.execute(query, [user_id, search_string]).fetchall()

    def getUsersTexts(self, user_id, search_string=""):
        return self.getOwnedTexts(user_id, search_string), self.getSharedTexts(user_id, search_string)

    def checkDelete(self, title, user_id):
        owned_texts = [text[0] for text in self.getOwnedTexts(user_id)]
        if title in owned_texts:
            return True
        return False

    def updateUserPassword(self, data):
        query = """UPDATE User
                   SET Password=?
                   WHERE UserName=?
                   AND Password=?;"""

        self.cursor.execute(query, data)
        self.connection.commit()

    def checkForUser(self, username):
        query = """SELECT UserName
                   FROM User
                   WHERE UserName = ?;"""
        matched_user = self.cursor.execute(query, [username]).fetchall()[0][0]
        return matched_user

    def checkPass(self, username):
        query = """SELECT Password
                   FROM User
                   WHERE UserName = ?;"""
        return self.cursor.execute(query, [username]).fetchall()

    def searchOwnedTexts(self, data, extra_query):
        query = """SELECT Text.TextTitle, Text.FHC
                   FROM Text
                   WHERE Text.UID = ?
                   AND Text.ReadingAge > ?
                   AND Text.Sentiment > ?
                   AND Text.Sentiment < ?"""
        query += extra_query
        return self.cursor.execute(query, data).fetchall()

    def searchSharedTexts(self, data, extra_query):
        query = """SELECT Text.TextTitle, Text.FHC
                   FROM Text, User_Text
                   WHERE User_Text.UID = ?
                   AND Text.TID = User_Text.TID
                   AND Text.ReadingAge > ?
                   AND Text.Sentiment > ?
                   AND Text.Sentiment < ?"""
        query += extra_query
        return self.cursor.execute(query, data).fetchall()

    def searchTexts(self, data, extra_query):
        return self.searchOwnedTexts(data, extra_query), self.searchSharedTexts(data, extra_query)

    def getUsers(self):
        query = """SELECT UID, UserName
                   FROM User;"""
        users = self.cursor.execute(query).fetchall()
        return users

    def share_text(self, title, username, current_user):
        query = """INSERT INTO User_Text(UID, TID)
                   VALUES (?, ?);"""
        uid = self.getID(username)
        tid = self.getTextID(title, self.getID(current_user))
        self.cursor.execute(query, [uid, tid])
        self.connection.commit()

    def getUsername(self, UID):
        query = """SELECT UserName
                   FROM User
                   WHERE UID = ?;"""
        username = self.cursor.execute(query, [UID]).fetchall()[0][0]
        return username

    def getTextUsers(self, title):
        valid_users = []
        user_ids = [x[0] for x in self.getUsers()]
        for uid in user_ids:
            owned_texts = [x[0] for x in self.getOwnedTexts(uid)]
            shared_texts = [x[0] for x in self.getSharedTexts(uid)]
            texts = owned_texts + shared_texts
            if title not in texts:
                valid_users.append({'username': self.getUsername(uid)})
        return valid_users

    def sendNotif(self, username, text):
        query = """INSERT INTO Notifications(UID, MESSAGE)
                   VALUES (?, ?);"""
        uid = self.getID(username)
        self.cursor.execute(query, [uid, text])
        self.connection.commit()

    def getNotifs(self, username):
        query = """SELECT MESSAGE
                   FROM Notifications
                   WHERE UID = ?;"""
        uid = self.getID(username)
        notifications = [x[0] for x in self.cursor.execute(query, [uid]).fetchall()]
        return notifications

    def loadCategories(self):
        query = """SELECT Cat
                   FROM Categories"""
        thing = [x[0] for x in self.cursor.execute(query)]
        return thing

    def getCatID(self, cat):
        query = """SELECT CID
                   FROM Categories
                   WHERE Cat = ?;"""
        return self.cursor.execute(query, [cat]).fetchall()[0][0]

    def addNewCategory(self, cat):
        query = """INSERT INTO Categories(Cat)
                   VALUES (?);"""
        self.cursor.execute(query, [cat])
        self.connection.commit()

    def getCategory(self, category):
        cats = self.loadCategories()
        if category not in cats:
            self.addNewCategory(category)
        return self.getCatID(category)

    def searchOwnedCategories(self, category, user_id):
        query = """SELECT Text.TextTitle, Text.FHC
                   FROM Text, Categories
                   WHERE Categories.Cat = ?
                   AND Categories.CID = Text.CID
                   AND Text.UID = ?"""
        return self.cursor.execute(query, [category, user_id]).fetchall()

    def searchSharedCategories(self, category, user_id):
        query = """SELECT Text.TextTitle, Text.FHC
                   FROM Text, Categories, User_Text
                   WHERE User_Text.UID = ?
                   AND User_Text.TID = Text.TID
                   AND Text.CID = Categories.CID
                   AND Categories.Cat = ?;"""
        return self.cursor.execute(query, [user_id, category]).fetchall()

    def searchCategories(self, category, user_id):
        return self.searchOwnedCategories(category, user_id), self.searchSharedCategories(category, user_id)

    def searchOwnedKeywords(self, keyword, user_id):
        query = """SELECT Text.TextTitle, Text.FHC, text_word.Score
                   FROM Text, Keywords, text_word
                   WHERE Keywords.Word = ?
                   AND Keywords.WID = text_word.WID
                   AND text_word.TID = Text.TID
                   AND Text.UID = ?;"""
        return self.cursor.execute(query, [keyword, user_id]).fetchall()

    def searchSharedKeywords(self, keyword, user_id):
        query = """SELECT Text.TextTitle, Text.FHC, text_word.Score
                   FROM Text, Keywords, text_word, User_Text
                   WHERE Keywords.Word = ?
                   AND Keywords.WID = text_word.WID
                   AND text_word.TID = User_Text.TID
                   AND User_Text.TID = Text.TID
                   AND User_Text.UID = ?;"""
        return self.cursor.execute(query, [keyword, user_id]).fetchall()

    def searchKeyword(self, keyword, user_id):
        return self.searchOwnedKeywords(keyword, user_id), self.searchSharedKeywords(keyword, user_id)

    def deleteNotifs(self, user_id):
        query = """DELETE FROM Notifications
                   WHERE UID = ?"""
        self.cursor.execute(query, [user_id])
        self.connection.commit()

    def deleteShares(self, user_id):
        query = """DELETE FROM User_Text
                   WHERE UID = ?"""
        self.cursor.execute(query, [user_id])
        self.connection.commit()

    def deleteUser(self, user_id):
        self.deleteNotifs(user_id)
        self.deleteShares(user_id)
        query = """DELETE FROM User
                   WHERE UID = ?"""
        self.cursor.execute(query, [user_id])
        self.connection.commit()
