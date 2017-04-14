import sqlite3
import re
DATABASE = '/home/dylan/Documents/TextAnalyser/static/db/user_text.sqlite'


class Field:
    """
    Class to store data about the fields in a form

    Properties:
        data - value of data stored
        length - length of the data
        validate - whether the field has been validated
    """
    def __init__(self, value):
        self.data = value
        self.length = len(value)
        self.validate = "Not"


class reg_form:
    """
    Handles data from the registration form

    Properties:
        dbconn - connection to the database
        dbcur - database cursor
        username - username entered
        password - password entered
        password_confirm - re-entry of the password
        email - email entered

    Method:
        validate - checks all the fields have been validated
        email_validate - checks that the email is of the required form and is not already used
        username_validate - checks that the username is not already used and is of a required length
        pass_validate - checks that the password matches the confirm password and that it meets target complexity
    """
    def __init__(self, form):
        self.dbconn = sqlite3.connect(DATABASE)
        self.dbconn.row_factory = lambda cursor, row: row[0]
        self.dbcur = self.dbconn.cursor()
        self.username = Field(form['username'])
        self.email = Field(form['email'])
        self.password = Field(form['password'])
        self.password_confirm = Field(form['confirm'])

    def validate(self):
        us_val = self.username_validate()
        em_val = self.email_validate()
        pass_val = self.pass_validate()
        if self.username.validate == "Passed":
            if self.email.validate == "Passed":
                if self.password.validate == "Passed":
                    return "Passed"
                else:
                    return pass_val
            else:
                return em_val
        else:
            return us_val

    def email_validate(self):
        query = """SELECT Email FROM User"""
        all_emails = self.dbcur.execute(query).fetchall()
        email_regex = r"(^[a-zA-Z0-9_.]+@[a-zA-Z0-9]+\.[a-zA-z0-9]+$)"
        regex = re.compile(email_regex)
        if self.email.data in all_emails:
            return "This email has already been used."
        elif regex.match(self.email.data):
            self.email.validate = "Passed"
        else:
            return "Not a valid email address."

    def username_validate(self):
        query = "SELECT UserName FROM User"
        all_names = self.dbcur.execute(query).fetchall()
        if self.username.data in all_names:
            return "Username is already taken."
        elif self.username.length in range(4, 21):
            self.username.validate = "Passed"
        else:
            return "Username is too long/short"

    def pass_validate(self):
        password_regex = r"^(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])[a-zA-Z\d]{6,}$"
        regex = re.compile(password_regex)
        if self.password.data != self.password_confirm.data:
            return "Passwords do not match."
        elif regex.match(self.password.data):
            self.password.validate = "Passed"
        else:
            return "Password needs to have an upper and lowercase letter and a number."
