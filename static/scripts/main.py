import nltk
import pickle
import requests
from static.scripts.sorts import quick_sort, radix_sort
import static.scripts.adt as adt
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from math import log
from flask import Markup
from docx import Document
import string
import pygal
import json
import PyPDF2

A = 0.4
# Special cases of
special_case = ['s', 'c', 't', 'p']
phonics = [["f", "ph"],
           ["n", "kn", "gn"],
           ["s", "ce", "ci", "cy"],
           ["r", "wr"],
           ["u", "eu"]]

# REQUEST:
# http://api.diffbot.com/v3/article?url=http://www.independent.co.uk/news/science/scientists-albert-einstein-light-universe-wrong-joao-magueijo-imperial-college-london-a7443136.html&token=bc6b3926127b4341c672dd62bcfbdc62

stops = set(stopwords.words('english'))
DIPHTHONG = ['ou', 'ie', 'ay', 'oi', 'oo', 'ea', 'ee', 'ai', 'ion']
TRIPHTHONG = ['iou', 'eau']
VOWELS = ['a', 'e', 'i', 'o', 'u', 'y']
punc = ["!", "?", "``", '*', '(', ')', '-', '{', '}', '[', ']', ':',
        ';', "'", ',', '.', '\\', '/', "''", '"', "”", "“", "–",
        "--", "—"]
contracted_words = ["'s", "'m", "n't", "'re", "it’s", "i’ve", "they’re", 'we’re']


def check_allit(current_word, top_item):
    """
    Checks if two words are alliterative
    """
    current_word_first = current_word.data[0].lower()
    current_word_first_two = current_word.data[:2].lower()
    top_item_first = top_item.data[0].lower()
    top_item_first_two = top_item.data[:2].lower()
    # Checks for first letter the same
    if current_word_first == top_item_first:
        if current_word_first in special_case:
            # Check for h's
            if current_word_first_two[1] == "h" and top_item_first_two[1] == "h":
                return True
            elif current_word_first_two[1] != "h" and top_item_first_two[1] != "h":
                return True
        else:
            return True
    else:
        # Checks for similar phonics
        for phonic in phonics:
            if top_item_first in phonic or top_item_first_two in phonic:
                if current_word_first in phonic or current_word_first_two in phonic:
                    return True
    return False


def loadAfinn():
    """
    Loads the words from the library of afinn words
    Adds each word to a dictionary with key as word, value as sentiment
    """
    afinnwords = {}
    with open('static/scripts/AFINN-111.txt', encoding="utf-8") as f:
        for line in f:
            split_line = line.split()
            joined = ''
            for w in range(0, len(split_line) - 1):
                joined += split_line[w]
            afinnwords[joined] = int(split_line[len(split_line) - 1])
    return afinnwords


def check_source(directory):
    """
    Returns the file type
    """
    eow = directory[-3:]
    sow = directory[:3]
    if eow == 'txt':
        return eow
    elif eow == 'pdf':
        return eow
    elif eow == "ocx":
        return "docx"
    elif sow == 'htt' or sow == 'www':
        return 'url'
    else:
        return None


def check_syl(word):
    """
    Approximates the number of sylables in a word, based on the number of vowels
    """
    count = 0
    # Count number of vowels
    for letter in word:
        if letter in VOWELS:
            count += 1
    # Subtracts 1 for double vowel sounds
    for di in DIPHTHONG:
        if di in word:
            count -= 1
    # Subtracts 2 for triple vowel sounds
    for tri in TRIPHTHONG:
        if tri in word:
            count -= 2
    # Subtracts 1 if a silent e is at the end of the word
    if count != 0 and word[len(word) - 1] == 'e':
        count -= 1
    return count


class TF_IDF():
    """
    Algorithm to calculate the significance of a word in a text

    Properties:
        document_frequency - has a record for each text trained and holds the
                             number of occurences of each word in that text

    Methods:
        count_words - given a text counts the instances of each word
        train_frequencies - adds a new text to the document_frequency
        normalise_frequency - defines the frequency of a word in relation to the
                              frequencies of other words
        find_idf - finds the inverse document frequnecy of a word based on the
                   number of texts that word appears in
        check_new_text - Calculates the tf-idf of a new text and sorts the list
                         to find the top 5 most significant words in that text
    """

    def __init__(self):
        self.number_of_documents = 0
        self.document_frequency = {}

    def count_words(self, text):
        words = word_tokenize(text)
        text_words = {}
        for word in words:
            word = word.lower()
            if word not in stops and word not in punc and word not in contracted_words:
                current_words = list(text_words.keys())
                if word in current_words:
                    text_words[word] += 1
                else:
                    text_words[word] = 1
        return text_words

    def train_frequencies(self, text):
        text_words = word_tokenize(text)
        unique_words = set(text_words)
        for word in unique_words:
            try:
                self.document_frequency[word] += 1
            except:
                self.document_frequency[word] = 1
        self.number_of_documents += 1

    def normalise_frequency(self, word_count, highest_raw):
        # Formula to normalise the frequency
        normalise_frequency = A + ((1 - A) * (word_count / highest_raw))
        return normalise_frequency

    def find_idf(self, word):
        try:
            documents_containing = self.document_frequency[word] + 1
        except:
            documents_containing = 1
        idf = log((self.number_of_documents / (documents_containing)), 10)
        return idf

    # returns the top five word in the new text
    def check_new_text(self, text):
        words = set(word_tokenize(text))
        word_count = self.count_words(text)
        highest_raw = word_count[max(word_count, key=lambda i: word_count[i])]
        tf_idfs = {}
        for word in words:
            word = word.lower()
            if word not in stops and word not in punc and word not in contracted_words:
                ntf = self.normalise_frequency(word_count[word], highest_raw)
                idf = self.find_idf(word)
                tf_idf = str(ntf * idf)
                # converts in to format that is sortable by radix Algorithm
                if float(tf_idf) >= 0:
                    tf_idfs[word] = tf_idf[0] + tf_idf[2:5]
        lst = []
        if len(tf_idfs) == 0:
            return []
        for word, ti in tf_idfs.items():
            lst.append(tuple([word, ti.zfill(4)]))
        print(lst)
        print(radix_sort(lst))
        # Gets 5 words with the highest tf-idf
        self.train_frequencies(text)
        return radix_sort(lst)[-5:]


class Analyser:
    """
    Class that performs and stores the analyses as well as the statistics
    about the text

    Properties:
        path - path to the text
        title - text title, name of file or user defined title
        category - category of the text
        text - reader object that stores the text
        tf - holds the trained tf-idf object from the file
        has_features - holds boolean values as to whether a text contains a
                       certain type of analysis
        stats - dictionary holding the statistics about the text
        analysed_texts - dictionary holding the analysed version of the text

    Methods:
        open_tf  - opens and returns the trained tf-idf object
        get_facts - calls all the functions that return text facts and stores them
        get_keywords - gets the keywords using the check_new_text in tf-idf class
        number_of_words - counts the number of words in the text
        __get_words - counts the number of occurences of each word in the text
        sorted_words - sorts the words from __get_words and takes the top ten
                       and creates bar graph
        __get_punctuation - counts the number of occurences of each type of
                            punctuation in the text
        sorted_words - sorts the results from __get_punctuation and creates bar graph
        total_syl - calculates the total number of sylables
        find_reading_age - calculates the reading age using the flesch-kincaid formula
        get_sentiment - finds the average sentiment of all words in the text
        analyse_all - calls all the functions that return new analyses and stores them
        find_allit - finds all the instances of alliteration and marks them
        antithesis -  finds all the instances of antithesis and marks them
        juxtaposition -  finds all the instances of juxtaposition and marks them
    """
    def __init__(self, directory, title=''):
        self.path = directory
        self.title = title
        self.category = ''
        file_type = check_source(directory)
        if file_type == 'txt':
            self.text = TextFile(directory)
        elif file_type == 'url':
            self.text = WebPage(directory)
            self.title = self.text.title
        elif file_type == 'pdf':
            self.text = PDFFile(directory)
        elif file_type == "docx":
            self.text = DOCXFile(directory)
        self.tf = self.open_tf()
        self.has_features = []
        self.stats = self.get_facts()
        self.analysed_texts = self.analyse_all()

    def open_tf(self):
        with open("static/scripts/tf.txt", "rb") as f:
            tf = pickle.load(f)
        return tf

    def get_facts(self):
        facts = {}
        facts['Number of Words'] = self.number_of_words()
        facts['Reading Age'] = round(self.find_reading_age(), 2)
        facts['Punctuation'] = self.sorted_punctuation()
        facts['Words'] = self.sorted_words()
        facts['Sentiment'] = round(self.get_sentiment(), 2)
        facts['Key Words'] = self.get_keywords()
        self.has_features.append(facts['Reading Age'])
        self.has_features.append(facts['Sentiment'])
        return facts

    def get_keywords(self):
        text = self.text.content
        keywords = self.tf.check_new_text(text)
        return keywords

    def number_of_words(self):
        total = 0
        for word in self.text.word_tok():
            if word not in punc or word not in contracted_words:
                total += 1
        return total

    def analyse_all(self):
        analysed_texts = {}
        analysed_texts['Regular'] = self.text.content
        analysed_texts['Alliteration'], has_allit = self.find_allit()
        analysed_texts['Antithesis'], has_anti = self.antithesis()
        analysed_texts['Juxtaposition'], has_juxta = self.juxtaposition()
        self.has_features.append(has_allit)
        self.has_features.append(has_anti)
        self.has_features.append(has_juxta)
        return analysed_texts

    def sorted_punctuation(self):
        tally = self.__get_punctuation()
        if len(tally) > 0:
            sorted_tally = quick_sort(tally)
            for x in range(len(sorted_tally)):
                sorted_tally[x] = (sorted_tally[x][0], int(sorted_tally[x][1]))
            punc_chart = pygal.HorizontalBar()
            punc_chart.title = 'Most Used Punctuation in Text'
            for punc in reversed(sorted_tally):
                punc_chart.add(punc[0], punc[1])
        else:
            punc_chart = pygal.HorizontalBar()
            punc_chart.title = 'Most Used Punctuation in Text'
        return punc_chart.render_data_uri()

    def __get_punctuation(self):
        words = self.text.word_tok()
        text_punc = [w for w in words if w in punc]
        punc_tally = list(tuple((p, str(text_punc.count(p)).zfill(5))
                                for p in punc if text_punc.count(p) > 0))
        return punc_tally

    def sorted_words(self):
        tally = self.__get_words()
        if len(tally) != 0:
            sorted_tally = radix_sort(tally)
            for x in range(len(sorted_tally)):
                sorted_tally[x] = (sorted_tally[x][0], int(sorted_tally[x][1]))
            top_ten = sorted_tally[-10:]
            word_chart = pygal.HorizontalBar()
            word_chart.title = 'Most Used Words in Text'
            for word in reversed(top_ten):
                word_chart.add(word[0], word[1])
        else:
            word_chart = pygal.HorizontalBar()
            word_chart.title = 'Most Used Words in Text'
        return word_chart.render_data_uri()

    def __get_words(self):
        words = self.text.no_stops_words()
        words_used = []
        for w in words:
            if w not in words_used and w not in punc and w not in contracted_words:
                words_used.append(w)
        word_tally = list(tuple((w, str(words.count(w)).zfill(5))
                                for w in words_used if words.count(w) > 0))
        return word_tally

    def find_reading_age(self):
        words = self.text.word_tok()
        words = [w for w in words if (
            w not in punc and w not in contracted_words)]
        words = len(words)
        sents = len(self.text.sent_tok())
        syls = self.total_syl()
        grade_flesch = (0.39 * (words / (sents + 1))) + (11.8 * (syls / (words + 1))) - 10
        flesch = 206.835 - (1.015 * (words / (sents + 1))) - (84.6 * (syls / (words + 1)))
        if grade_flesch < 0:
            return 0
        return grade_flesch

    def total_syl(self):
        counts = []
        words = self.text.word_tok()
        for word in words:
            counts.append(check_syl(word))
        return sum(counts)

    def find_allit(self):
        has = 0
        text = self.text.word_tok()
        non_words = punc + contracted_words
        text_stack = adt.word_stack()
        for index, word in enumerate(text):
            if word not in non_words and word not in stops:
                current_word = adt.DataPos(word, index)
                top_item = text_stack.peek()
                if top_item is False:
                    text_stack.add(current_word)
                elif check_allit(current_word, top_item):
                    text_stack.add(current_word)
                else:
                    if text_stack.get_height() > 1:
                        last_item = text_stack.pop()
                        while not text_stack.is_empty():
                            first_item = text_stack.pop()
                        first_item_index = first_item.position
                        last_item_index = last_item.position
                        text[first_item_index] = "<mark>" + \
                            text[first_item_index]
                        text[last_item_index] = text[
                            last_item_index] + "</mark>"
                        has = 1
                    while not text_stack.is_empty():
                        text_stack.pop()
                    text_stack.add(current_word)
                if index == len(text) - 1:
                    if text_stack.get_height() > 1:
                        last_item = text_stack.pop()
                        while not text_stack.is_empty():
                            first_item = text_stack.pop()
                        first_item_index = first_item.position
                        last_item_index = last_item.position
                        text[first_item_index] = "<mark>" + \
                            text[first_item_index]
                        text[last_item_index] = text[
                            last_item_index] + "</mark>"
                        has = 1
                    while not text_stack.is_empty():
                        text_stack.pop()
                    text_stack.add(current_word)

        result = ''
        for w in text:
            if w in punc or w in contracted_words:
                result += w
            else:
                result += " " + w

        return Markup(result), has

    def get_sentiment(self):
        afinnwords = loadAfinn()
        sentiment = 0
        no = 0
        words = self.text.word_tok()
        for w in words:
            w = w.lower()
            try:
                sentiment += afinnwords[w]
                no += 1
            except:
                pass
        if no > 0:
            sentiment = sentiment / no
        return sentiment

    def antithesis(self):
        has = 0
        afinnwords = loadAfinn()
        non_words = punc + contracted_words
        words = self.text.word_tok()
        comparison_stack = adt.sentiment_queue()
        for index, word in enumerate(words):
            word = word.lower()
            if word not in non_words and word not in stops:
                try:
                    word_info = {"sentiment": afinnwords[word]}
                except:
                    word_info = {"sentiment": 0}
                new_word = adt.DataPos(word, index, word_info)
                comparison_stack.enqueue(new_word)
                first, second = comparison_stack.check_sentiments()
                if first is not False:
                    words[first.position] = "<mark>" + words[first.position]
                    words[second.position] = words[second.position] + "</mark>"
                    has = 1
        result = ''
        for w in words:
            if w in punc or w in contracted_words:
                result += w
            else:
                result += " " + w

        return Markup(result), has

    def juxtaposition(self):
        has = 0
        afinnwords = loadAfinn()
        sentences = self.text.sent_tok()
        sentiments = []
        output_text = ''
        for sentence in sentences:
            sentiment_total = 0
            words_checked = 0
            sentence_words = word_tokenize(sentence)
            for word in sentence_words:
                try:
                    sentiment_total += afinnwords[word.lower()]
                    words_checked += 1
                except:
                    pass
            if words_checked != 0:
                sentence_sentiment = sentiment_total / words_checked
                sentiments.append(sentence_sentiment)
            else:
                sentiments.append(0)
        if len(sentences) == 2:
            if abs(sentiments[0] - sentiments[1]) > 3:
                sentences[0] = "<mark>" + sentences[0]
                sentences[1] = sentences[1] + "</mark>"
                has = 1
        else:
            for sent in range(0, len(sentences) - 2):
                if abs(sentiments[sent] - sentiments[sent + 1]) > 3:
                    sentences[sent] = "<mark>" + sentences[sent]
                    sentences[sent + 1] = sentences[sent + 1] + "</mark>"
                    has = 1
        output_text = ' '.join(s for s in sentences)
        return Markup(output_text), has


class Reader:
    """
    Class that defines all the ways that the text can be tokenised

    Properties:
        content - raw text extracted from the file

    Methods:
        word_tok - returns an array containing all the words in the text
        sent_tok - returns an array containing all the sentences in the text
        no_stops - returns the raw text without any stop words
        no_stops_words - returns an array containing all the words in the text
                         without any stop words
        no_stops_sents - returns an array containing all the sentences in the text
                         without any stop words
    """
    def __init__(self):
        self.content = ''

    def word_tok(self):
        words = word_tokenize(self.content)
        return words

    def sent_tok(self):
        sents = sent_tokenize(self.content)
        return sents

    def no_stops(self):
        words = self.word_tok()
        no_stop = ''.join(w + ' ' for w in words if w not in stops)
        return no_stop

    def no_stops_words(self):
        text = self.no_stops()
        words = word_tokenize(text)
        return words

    def no_stops_sents(self):
        text = self.no_stops()
        sents = sent_tokenize(text)
        return sents

"""
Basic class overview for the following 4 classes
All get text from the specified file type

Properties:
    ext - extension of the file (if applicable)
    title - title, depends on file name or web page title
    content - raw text from the source

Methods:
    get_text - method used to extract the text from the source

"""


class WebPage(Reader):
    """
    Loads the text from a web page using the diffbot article api
    """
    def __init__(self, directory):
        super().__init__()
        self.ext = ''
        self.title = ''
        self.content = self.get_text(directory)

    def get_text(self, source):
        r = requests.get("http://api.diffbot.com/v3/article?url=" +
                         source + "&token=a38083295817ceee22404a79c7400b96")
        ro = json.loads(r.text)
        self.title = ro['objects'][0]['title']
        return ro['objects'][0]['text']


class TextFile(Reader):
    """
    Gets text from a text file_text
    """
    def __init__(self, directory):
        super().__init__()
        self.ext = ".txt"
        self.content = self.get_text(directory)

    def get_text(self, source):
        file_text = ''
        with open(source, encoding='utf-8') as f:
            for line in f:
                line = line.replace('\n', ' ')
                if line != ' ' or line != '':
                    file_text += line
        return Markup(file_text)


class DOCXFile(Reader):
    """
    Gets text from a docx file
    """
    def __init__(self, directory):
        super().__init__()
        self.ext = ".docx"
        self.content = self.get_text(directory)

    def get_text(self, source):
        text = ''
        document = Document(source)
        for p in document.paragraphs:
            text += p.text
        return text


class PDFFile(Reader):
    """
    Gets text from a pdf file
    """
    def __init__(self, directory):
        super().__init__()
        self.ext = ".pdf"
        self.content = self.get_text(directory)

    def get_text(self, source):
        text = ''
        pdfObject = open(source, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfObject)
        for page in range(0, pdfReader.numPages):
            pageObj = pdfReader.getPage(page)
            text += pageObj.extractText()
        return text
