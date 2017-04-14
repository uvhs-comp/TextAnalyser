# IMPORT file dependancies
from flask import render_template, request, url_for, Flask, redirect, session, flash, Markup, make_response
from static.scripts.sorts import quick_sort, radix_sort
from static.scripts.form import Field, reg_form
from werkzeug.utils import secure_filename
from static.db.dbclass import Database
from passlib.hash import pbkdf2_sha256
from static.scripts.main import TF_IDF
from collections import defaultdict
from static.scripts import main
from functools import wraps
from math import log
import sqlite3
import pdfkit
import shutil
import pickle
import os
import re

# Defualt upload directory
UPLOAD_FOLDER = "./static/userfiles/"
# Filetypes the program allows
allowed_extensions = ("pdf", "txt", "docx")
# File currently being used
current_file = None

# Starting flask application
app = Flask(__name__)
# Setting specific upload folder - changes later based on session user
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def TextDelete(texttitle):
    """
    Deletes text object file, database records and any keywords in the graph.
    """

    path = app.config['UPLOAD_FOLDER'] + \
        '/objects/' + texttitle + '.txt'
    with Database() as database:
        database.deleteText(texttitle, session['id'])

    # Loads in the file to be deleted and the keyword graph
    with open(path, "rb") as objectfile:
        current_file = pickle.load(objectfile)
    keywords = current_file.stats['Key Words']
    with open("word_graph.txt", "rb") as graphfile:
        word_graph = pickle.load(graphfile)

    # Reduces each edge connected to the current file keywords
    for keyword in keywords:
        word_graph.add_node(keyword[0])
        for k in keywords:
            if k[0] != keyword[0]:
                word_graph.reduce_edge(keyword[0], k[0])

    # Rewrites the graph object file
    with open("word_graph.txt", "wb") as graphfile:
        pickle.dump(word_graph, graphfile)

    # Deletes the object file
    os.remove(path)


def formatTexts(owned, shared):
    """
    Formats the texts recived from a database search to the format used to
    display them in the users profile page.
    """
    owned_texts = []
    shared_texts = []
    # Catches error if there is no score from the databse search
    try:
        for text in range(len(owned)):
            owned_texts.append(
                {'title': owned[text][0], 'body': owned[text][1], 'score': owned[text][2]})
        for text in range(len(shared)):
            shared_texts.append(
                {'title': shared[text][0], 'body': shared[text][1], 'score': shared[text][2]})
    except:
        for text in range(len(owned)):
            owned_texts.append(
                {'title': owned[text][0], 'body': owned[text][1]})
        for text in range(len(shared)):
            shared_texts.append(
                {'title': shared[text][0], 'body': shared[text][1]})
    # Adds False if the either of the text arrays are empty
    if len(owned_texts) == 0:
        owned_texts.append(False)
    if len(shared_texts) == 0:
        shared_texts.append(False)
    return owned_texts, shared_texts


def check_extension(f):
    """
    Gets the extension of the submitted file
    """
    parts = f.split('.')
    last = parts[len(parts) - 1]
    return last in allowed_extensions


def login_required(f):
    """
    Wrapper for function that require the user to be logged in to access the function
    """
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
    return wrap


def check_pass(password, confirmed):
    """
    Checks the passwords entered are the same
    Checks they meet the complexity criteria
    """
    # Requires at least one digit, a lower case letter,
    # an upper case letter and has at least 6 characters
    password_regex = r"^(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])[a-zA-Z\d]{6,}$"
    regex = re.compile(password_regex)
    if password == confirmed:
        if regex.match(pas):
            return "Passed"
        else:
            return "Password needs to have an upper and lowercase letter and a number."
    else:
        return "Passwords do not match."


class Graph:
    """
    Graph data structure used to map links between keywords

    Properties:
        nodes(set) - set of nodes in the Graph
        edges(dict: values are set to be lists) - connection between nodes
        distances(dict) - stores the weightings for each edge

    Methods:
        add_node - adds another node to the node set
        add_edge - if edge exists. increases the weight by 1, otherwise adds
                   edge and sets weight to 1
        reduce edge - reduces a edges weight by 1, if weight is then 0,
                      removes edge
    """

    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(list)
        self.distances = {}

    def add_node(self, value):
        self.nodes.add(value)

    def add_edge(self, from_node, to_node):
        if to_node in self.edges[from_node]:
            self.distances[(from_node, to_node)] += 1
        else:
            self.edges[from_node].append(to_node)
            self.distances[(from_node, to_node)] = 1

    def reduce_edge(self, from_node, to_node):
        if self.distances[(from_node, to_node)] > 1:
            self.distances[(from_node, to_node)] -= 1
        else:
            self.edges[from_node].remove(to_node)
            if len(self.edges[from_node]) == 0:
                self.edges.pop(from_node)
            self.distances.pop((from_node, to_node))


def dijsktra(graph, initial):
    """
    Performs dijsktras algorithm from a certain node
    """
    # Sets initial node score to 10
    visited = {initial: 10}

    nodes = set(graph.nodes)
    max_weight = graph.distances[max(graph.distances, key=graph.distances.get)]
    min_weight = graph.distances[min(graph.distances, key=graph.distances.get)]

    # Defines the number of nodes to explore as the number of conected nodes
    nodes_to_explore = len(graph.edges[initial]) + 2
    explored = 1
    while explored < nodes_to_explore:
        # Finds nodes with maximum value that has not yet been explored
        max_node = None
        for node in nodes:
            if node in visited:
                if max_node is None:
                    max_node = node
                elif visited[node] > visited[max_node]:
                    max_node = node

        if max_node is None:
            break

        nodes.remove(max_node)
        current_weight = visited[max_node]

        # Finds score of the next node if node has already been visited
        # changes score if it is greater
        for edge in graph.edges[max_node]:
            weight = graph.distances[(max_node, edge)]
            if max_weight - min_weight == 0:
                normalised = 1
            else:
                normalised = ((weight - min_weight) / (max_weight - min_weight)) + 1
            weight = current_weight - (1 / normalised)
            if edge not in visited or weight > visited[edge]:
                visited[edge] = round(weight, 2)
        explored += 1

    return visited


# Error Handler Methods
@app.errorhandler(404)
def page_not_found(e):
    """
    Serves '404:Page Not Found' error page
    """
    return render_template('404.html'), 404


@app.errorhandler(405)
def method_not_allowed(e):
    """
    Serves '405:Method Not Allowed' error page
    """
    return render_template('405.html'), 405


@app.errorhandler(500)
def internal_server_error(e):
    """
    Serves '500:Internal Server Error' error page
    """
    return render_template('500.html'), 500


@app.route('/')
def index():
    """
    Serves the home page at the '/' route
    Loads notifications for the logged in user
    """
    try:
        with Database() as db:
            notifs = db.getNotifs(session['username'])
            b_notifs = []
            for i in range(len(notifs) - 1, -1, -1):
                b_notifs.append(notifs[i])
            session['notifs'] = b_notifs
        return render_template(
            'index.html',
            notifs=notifs
        )
    except:
        return render_template(
            'index.html')


@app.route('/uploadfile', methods=["POST", "GET"])
@login_required
def upload_file():
    """
    Upload link for files
    Creates analyser object
    Serves upload text display page.
    """
    try:
        global current_file
        if request.method == "POST":
            # Validates a file has been uploaded
            if 'file' not in request.files:
                flash("No file submitted")
                return redirect(url_for('index'))

            f = request.files['file']
            if f.filename == '':
                flash("No file submitted")
                return redirect(url_for('index'))

            if app.config['UPLOAD_FOLDER'] == UPLOAD_FOLDER:
                app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + \
                    session['username']

            if check_extension(f.filename):
                # Makes sure filename is safe
                filename = secure_filename(f.filename)
                filepath = app.config['UPLOAD_FOLDER'] + '/files/' + filename
                # Saves the uploaded file
                f.save(filepath)
                # Removes extension from filename
                filename = filename.replace('.txt', '')
                filename = filename.replace('.pdf', '')
                filename = filename.replace('.docx', '')

                current_file = main.Analyser(filepath, filename)
                analysed_texts = current_file.analysed_texts
                text_facts = current_file.stats
                with Database() as db:
                    categories = db.loadCategories()
                keywords = ''
                for word in text_facts['Key Words']:
                    keywords += word[0] + ", "
                keywords = keywords[:-2]
                return render_template('textdisplay.html',
                                       title=current_file.title,
                                       texts=analysed_texts,
                                       text=analysed_texts['Regular'],
                                       facts=text_facts,
                                       ext=current_file.text.ext,
                                       categories=categories,
                                       keywords=keywords,
                                       upload=True)

            else:
                flash("File type not allowed")
                return redirect(url_for('index'))

        else:
            return redirect(url_for('index'))
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route('/raw_text/', methods=["POST", "GET"])
@login_required
def raw_text_upload():
    """
    Upload path for raw text, creates a text file with the text in
    Creates analyser object
    """
    try:
        global current_file
        if request.method == "POST":
            raw_text = request.form['raw_text']
            # Checks text is not empty
            raw_text = raw_text.strip('<>')
            if raw_text != '':
                if app.config['UPLOAD_FOLDER'] == UPLOAD_FOLDER:
                    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + \
                        session['username']
                filepath = filepath = app.config[
                    'UPLOAD_FOLDER'] + '/files/raw.txt'
                filename = 'raw'
                # Writes file with raw text in
                with open(filepath, 'w') as f:
                    f.write(raw_text)

                # Makes actual analyser object
                current_file = main.Analyser(filepath, filename)
                analysed_texts = current_file.analysed_texts
                text_facts = current_file.stats
                with Database() as db:
                    categories = db.loadCategories()
                keywords = ''
                for word in text_facts['Key Words']:
                    keywords += word[0] + ", "
                keywords = keywords[:-2]
                return render_template('textdisplay.html',
                                       title=current_file.title,
                                       texts=analysed_texts,
                                       text=analysed_texts['Regular'],
                                       facts=text_facts,
                                       keywords=keywords,
                                       categories=categories,
                                       ext=current_file.text.ext,
                                       upload=True)
    except Exception as e:
        flash(e)
        return redirect(url_for('index'))


@app.route('/changepassword/', methods=["POST", "GET"])
@login_required
def changepassword():
    """
    Allows the user to change their password, changes password in database
    """
    try:
        if request.method == 'POST':
            # Makes sure the passwords match and that it meets complexity
            validate = check_pass(
                request.form['newpass'], request.form['connewpass'])
            if validate == "Passed":
                data = [request.form['newpass'], session[
                    'username'], request.form['oldpass']]
                with Database() as database:
                    database.updateUserPassword(data)
                return redirect(url_for('profile', username=session['username']))
            else:
                flash(validate)
                return render_template('changepass.html')

        else:
            return render_template('changepass.html')

    except Exception as e:
        flash("Oops, something went wrong... Try again.")
        return render_template('changepass.html')


@app.route('/profile/<username>')
@login_required
def profile(username):
    """
    Gets the users texts from the database and shows them on their profile page
    """
    try:
        with Database() as database:
            # Makes sure the user exists
            user = database.checkForUser(username)
            if user == session['username']:
                if session['username'] == username:
                    session['id'] = database.getID(session['username'])
                    owned_texts, shared_texts = formatTexts(*database.getUsersTexts(session['id']))
                    categories = database.loadCategories()
                    return render_template('profile.html',
                                           owned_texts=owned_texts,
                                           shared_texts=shared_texts,
                                           username=username,
                                           categories=categories)
                flash("You cannot view other users profiles")
                return redirect(url_for('index'))
            flash("User %s not found" % username)
            return redirect(url_for('index'))
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route('/profile/<username>/search_titles', methods=["POST", "GET"])
def search_titles(username):
    """
    Search through texts with titles that contain a specified string
    """
    try:
        with Database() as database:
            user = database.checkForUser(username)
            if user == session['username']:
                if session['username'] == username:
                    session['id'] = database.getID(session['username'])
                    search_string = request.form['title']
                    # Gets texts from db and formats them
                    owned_texts, shared_texts = formatTexts(*database.getUsersTexts(session['id'], search_string))
                    categories = database.loadCategories()
                    return render_template('profile.html',
                                           owned_texts=owned_texts,
                                           shared_texts=shared_texts,
                                           username=username,
                                           categories=categories)
                flash("You cannot view other users profiles")
                return redirect(url_for('index'))
            flash("User %s not found" % username)
            return redirect(url_for('index'))
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route('/profile/<username>/search_keywords', methods=["POST", "GET"])
def search_keywords(username):
    """
    Looks for texts with a certain keyword and similar keywords
    """
    try:
        with Database() as database:
            user = database.checkForUser(username)
            if user == session['username']:
                if session['username'] == username:
                    session['id'] = database.getID(session['username'])
                    search_string = request.form['keyword']
                    # Gets the graph from a file
                    with open("word_graph.txt", "rb") as f:
                        G = pickle.load(f)
                    owned_texts = []
                    shared_texts = []
                    if search_string in G.nodes:
                        # Gets all nodes that are connected to your current word
                        keywords = dijsktra(G, search_string)
                        owned_texts = []
                        shared_texts = []
                        owned_titles = []
                        for keyword, score in keywords.items():
                            owned, shared = database.searchKeyword(keyword, session['id'])
                            to_format_owned = []
                            to_format_shared = []
                            # Checks the text has not already been loaded
                            for text in owned:
                                if text[0] not in owned_titles:
                                    to_format_owned.append(text)
                                    owned_titles.append(text[0])
                            for text in shared:
                                if text[0] not in shared_titles:
                                    to_format_shared.append(text)
                                    shared_titles.append(text[0])
                            owned, shared = formatTexts(to_format_owned, to_format_shared)
                            owned_texts += owned
                            shared_texts += shared
                        # Makes sure there is only one false statement in array
                        owned_texts = [text for text in owned_texts if text is not False]
                        if len(owned_texts) == 0:
                            owned_texts.append(False)
                        shared_texts = [text for text in shared_texts if text is not False]
                        if len(shared_texts) == 0:
                            shared_texts.append(False)
                        categories = database.loadCategories()
                        return render_template('profile.html',
                                               owned_texts=owned_texts,
                                               shared_texts=shared_texts,
                                               username=username,
                                               categories=categories)
                    else:
                        flash("Keyword not found")
                        return redirect(request.referrer)
                flash("You cannot view other users profiles")
                return redirect(url_for('index'))
            flash("User %s not found" % username)
            return redirect(url_for('index'))
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route('/profile/<username>/search_category', methods=["POST", "GET"])
def search_category(username):
    """
    Gets texts within a certain category
    """
    try:
        with Database() as database:
            user = database.checkForUser(username)
            if user == session['username']:
                if session['username'] == username:
                    session['id'] = database.getID(session['username'])
                    category = request.args.get('category')
                    owned_texts, shared_texts = formatTexts(*database.searchCategories(category, session['id']))
                    categories = database.loadCategories()
                    return render_template('profile.html',
                                           owned_texts=owned_texts,
                                           shared_texts=shared_texts,
                                           username=username,
                                           categories=categories)
                flash("You cannot view other users profiles")
                return redirect(url_for('index'))
            flash("User %s not found" % username)
            return redirect(url_for('index'))
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route('/profile/<username>/search', methods=["POST", "GET"])
def search_values(username):
    """
    Search for texts that have a certain language feature
    Reading age and sentiment are in a certain range
    """
    try:
        with Database() as database:
            user = database.checkForUser(username)
            if user == session['username']:
                if session['username'] == username:
                    features = ["Alliteration", "Antithesis", "Juxtaposition"]
                    needs_feature = {}
                    for feature in features:
                        if request.form.get(feature) == "on":
                            needs_feature[feature] = 1
                        else:
                            needs_feature[feature] = 0
                    extra_query = ";"
                    for feature, has in needs_feature.items():
                        if has == 1:
                            extra = "AND Text." + feature + " = 1 "
                            extra_query = extra + extra_query
                    sentiment_above = float(request.form["SSA"])
                    sentiment_below = float(request.form["SSB"])
                    reading_age_above = float(request.form["RAS"])
                    if sentiment_above >= sentiment_below:
                        flash("Invalid Search...")
                        return redirect(request.referrer)
                    data = [session['id'], reading_age_above,
                            sentiment_above, sentiment_below]
                    owned_texts, shared_texts = formatTexts(*database.searchTexts(data, extra_query))
                    categories = database.loadCategories()
                    return render_template('profile.html',
                                           owned_texts=owned_texts,
                                           shared_texts=shared_texts,
                                           username=username,
                                           categories=categories)
                flash("You cannot view other users profiles")
                return redirect(url_for('index'))
            flash("User %s not found" % username)
            return redirect(url_for('index'))
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route('/uploadfile/<analysis>', methods=["POST", "GET"])
@login_required
def changeview(analysis):
    """
    Loads a different analysis of a certain text
    """
    try:
        analysed_texts = current_file.analysed_texts
        text_facts = current_file.stats
        with Database() as db:
            categories = db.loadCategories()
        keywords = ''
        for word in text_facts['Key Words']:
            keywords += word[0] + ", "
        keywords = keywords[:-2]
        return render_template('textdisplay.html',
                               title=current_file.title,
                               ext=current_file.text.ext,
                               texts=analysed_texts,
                               keywords=keywords,
                               text=analysed_texts[analysis],
                               categories=categories,
                               facts=text_facts,
                               upload=True)
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('profile', username=session['username']))


@app.route('/share/<texttitle>', methods=["POST", "GET"])
@login_required
def share(texttitle):
    try:
        """
        Loads the users who don't have a text with a specific name
        """
        with Database() as database:
            users = database.getTextUsers(texttitle)
            if len(users) == 0:
                users.append(False)
        return render_template('share.html',
                               title=texttitle,
                               users=users)
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(request.referrer)


@app.route('/download/<texttitle>', methods=["POST", "GET"])
@login_required
def download(texttitle):
    """
    Creates a pdf with the raw text in from a html template
    """
    try:
        body = current_file.analysed_texts['Regular']
        rendered = render_template('pdf_template.html', title=texttitle, body=body)
        options = {'encoding': "UTF-8"}
        pdf = pdfkit.from_string(rendered, False, options=options)
        response = make_response(pdf)
        response.headers["Content-Type"] = 'application/pdf'
        response.headers["Content-Disposition"] = 'attachment; filename=output.pdf'

        return response
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(request.referrer)


@app.route('/share_text/<texttitle>/<username>', methods=["POST", "GET"])
@login_required
def share_text(texttitle, username):
    """
    Shares the text with the user, by creating link in databse
    """
    message = session['username'] + \
        " shared the text " + texttitle + " with you."
    with Database() as database:
        database.share_text(texttitle, username, session["username"])
        database.sendNotif(username, message)
    flash("Text Shared")
    return redirect(url_for('index'))


@app.route('/textdisplay/<textTitle>/<analysis>')
@login_required
def textdisplay(textTitle, analysis):
    """
    Displays the text on upload and allows the analysis to be selected
    """
    try:
        global current_file
        with Database() as database:
            text_owner = database.getTextOwner(textTitle, session['username'])
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + text_owner
        path = app.config['UPLOAD_FOLDER'] + '/objects/' + textTitle + '.txt'
        with open(path, 'rb') as f:
            current_file = pickle.load(f)
        analysed_texts = current_file.analysed_texts
        text_facts = current_file.stats
        keywords = ''
        for word in text_facts['Key Words']:
            keywords += word[0] + ", "
        keywords = keywords[:-2]
        return render_template('textdisplay.html',
                               title=current_file.title,
                               texts=analysed_texts,
                               text=analysed_texts[analysis],
                               facts=text_facts,
                               keywords=keywords,
                               owner=text_owner,
                               user=session['username'])
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('profile', username=session['username']))


# Deletes the text from the database and from the upload folder
@app.route('/deletetext/<texttitle>')
@login_required
def deletetext(texttitle):
    """
    Deletes text file and wipes any records from the database
    """
    try:
        with Database() as database:
            canDelete = database.checkDelete(texttitle, session['id'])
            if canDelete:
                if app.config['UPLOAD_FOLDER'] == UPLOAD_FOLDER:
                    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + \
                        session['username']
                TextDelete(texttitle)
                flash("File Deleted")
                return redirect(url_for('profile', username=session['username']))
            else:
                flash("You do not have permission to delete this file")
                return redirect(url_for('profile', username=session['username']))
    except Exception as e:
        flash("Oops, something went wrong... Try again.")
        return redirect(url_for('profile', username=session['username']))


@app.route('/savetext/', methods=["POST", "GET"])
@login_required
def save_text():
    """
    Saves the text object in a text file and saves it in db
    """
    try:
        global current_file
        if request.method == "POST":
            current_file.title = request.form['title'].replace(' ', '')
            with Database() as database:
                category = database.getCategory(request.form['Category'])
                current_file.category = category
                session['id'] = database.getID(session['username'])
                owned, shared = database.getUsersTexts(session['id'])
                result = [x[0] for x in owned] + [x[0] for x in shared]
                # Checks that the user does not already have
                # access to a text with the same name
                if current_file.title not in result and current_file.title != "":
                    object_file_path = app.config[
                        'UPLOAD_FOLDER'] + '/objects/' + current_file.title + '.txt'
                    # Puts the object in the file
                    pickle.dump(current_file, open(object_file_path, 'wb'))
                    fhc = current_file.text.content[:97] + '...'
                    data = [session['id'], current_file.title, fhc,
                            current_file.category] + current_file.has_features
                    keywords = current_file.stats['Key Words']
                    # Saves to database
                    database.addText(data, keywords)
                    # Adds keywords to graph
                    with open("word_graph.txt", "rb") as f:
                        G = pickle.load(f)
                    for keyword in keywords:
                        G.add_node(keyword[0])
                        for k in keywords:
                            if k[0] != keyword[0]:
                                G.add_edge(keyword[0], k[0])
                    # Saves graph in file again
                    with open("word_graph.txt", "wb") as f:
                        pickle.dump(G, f)
                    current_file = None
                    return redirect(url_for('profile', username=session['username']))

                else:
                    print("LONEOWDBOFHNEROSFOEBFWEBFWOD")
                    flash("A file with this name already exists.")
                    categories = database.loadCategories()
                    analysed_texts = current_file.analysed_texts
                    text_facts = current_file.stats
                    keywords = ''
                    for word in text_facts['Key Words']:
                        keywords += word[0] + ", "
                    keywords = keywords[:-2]
                    return render_template('textdisplay.html',
                                           title=current_file.title,
                                           texts=analysed_texts,
                                           text=analysed_texts['Regular'],
                                           facts=text_facts,
                                           keywords=keywords,
                                           categories=categories,
                                           ext=current_file.text.ext,
                                           upload=True)
        else:
            flash("Page does not exist")
            return redirect(url_for('index'))

    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route("/webtext/<analysis>", methods=["POST", "GET"])
@login_required
def webtext(analysis):
    """
    Gets a text from the internet using an API
    """
    global current_file
    try:
        if request.form["url"] == "":
            flash("No URL given")
            return redirect(url_for('index'))
        url = request.form['url']
        current_file = main.Analyser(url)
        analysed_texts = current_file.analysed_texts
        text_facts = current_file.stats
        with Database() as database:
            categories = database.loadCategories()
        keywords = ''
        for word in text_facts['Key Words']:
            keywords += word[0] + ", "
        keywords = keywords[:-2]
        return render_template('textdisplay.html',
                               title=current_file.title,
                               texts=analysed_texts,
                               text=analysed_texts[analysis],
                               ext=current_file.text.ext,
                               keywords=keywords,
                               categories=categories,
                               facts=text_facts,
                               upload=True)

    except:
        flash("Web address not found!")
        return redirect(url_for('index'))


@app.route('/deleteaccount/')
@login_required
def deleteaccount():
    """
    Deletes the users account, their files and texts from the database
    """
    try:
        if app.config['UPLOAD_FOLDER'] == UPLOAD_FOLDER:
            app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + \
                session['username']
        with Database() as db:
            texts = db.getOwnedTexts(session['id'])
            for text in texts:
                TextDelete(text[0])
            db.deleteUser(session['id'])
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
            session.clear()
            app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
            flash("Account has been deleted")
            return redirect(url_for('index'))
    except Exception as e:
        flash("Something went wrong, please try again")
        return redirect(url_for('index'))


@app.route('/logout/')
@login_required
def logout():
    """
    Logs the user out
    """
    try:
        session.clear()
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        flash("You have been logged out")
        return redirect(url_for('index'))
    except Exception as e:
        flash("Oops, something went wrong... Try again.")
        return render_template('index.html')


@app.route('/login/', methods=["GET", "POST"])
def login_page():
    """
    Allows the user to login
    """
    try:
        if request.method == "POST":
            with Database() as database:
                db_password = database.checkPass(request.form['username'])
                if len(db_password) > 0:
                    db_password = db_password[0][0]
                    if pbkdf2_sha256.verify(request.form['password'], db_password):
                        session['logged_in'] = True
                        session['id'] = database.getID(request.form['username'])
                        session['username'] = request.form['username']
                        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + \
                            session['username']
                        return redirect(url_for('index'))
                    else:
                        flash("Invalid credentials, try again!")
                        return render_template("login.html")
                else:
                    flash("Invalid credentials, try again!")
                    return render_template("login.html")
        return render_template("login.html")

    except Exception as e:
        flash("Something went wrong, please try again")
        return render_template("login.html")


@app.route('/register/', methods=["GET", "POST"])
def register_page():
    """
    Allows the user to register
    """
    try:
        if request.method == "POST":
            form = reg_form(request.form)
            validation = form.validate()
            if validation == "Passed":
                # Hashes the passwords using sha256
                password_hash = pbkdf2_sha256.encrypt(form.password.data, rounds=200000, salt_size=16)
                data = [form.username.data,
                        form.email.data, password_hash]
                with Database() as database:
                    database.addUser(data)
                    session['logged_in'] = True
                    session['username'] = form.username.data
                    session['id'] = database.getID(session['username'])
                app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER + \
                    session['username']

                # Makes the users directory on the server
                os.mkdir(app.config['UPLOAD_FOLDER'])
                filedir = app.config['UPLOAD_FOLDER'] + '/files'
                objdir = app.config['UPLOAD_FOLDER'] + '/objects'
                os.mkdir(filedir)
                os.mkdir(objdir)

                flash("You have been logged in")
                return redirect(url_for('index'))
            else:
                flash(validation)
                return render_template('register.html')

        return render_template('register.html')

    except Exception as e:
        flash("Something went wrong, please try again")
        return render_template('register.html')


if __name__ == '__main__':
    # Super Secret shhhh...
    app.secret_key = 'howmuchwoodwouldawoodchuckchuckifawoodchuckcouldchuckwood?'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)
