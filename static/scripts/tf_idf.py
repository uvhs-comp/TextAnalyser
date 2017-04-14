from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from math import log
import pickle
from nltk.corpus import gutenberg, brown, reuters, inaugural
A = 0.4

stops = set(stopwords.words('english'))
punc = ["!", "?", "``", '*', '(', ')', '-', '{', '}', '[', ']', ':',
        ';', "'", ',', '.', '\\', '/', "''", '"', "”", "“", "–",
        "--", "—"]
contracted_words = ["'s", "'m", "n't", "'re", "it’s", "i’ve", "they’re", 'we’re']


def radix_sort(numbers_to_sort):
    """
    Implementation of the radix sort algorithm
    """
    list_length = len(numbers_to_sort)
    length = len(numbers_to_sort[0][1])
    while length > 0:
        for x in range(0, length):
            buckets = [0 for i in range(10)]
            for tup in numbers_to_sort:
                num_str = tup[1]
                buckets[int(num_str[x])] += 1
        for x in range(1, 10):
            buckets[x] += buckets[x - 1]
        sort_list = [0 for i in range(list_length)]
        for tup in reversed(numbers_to_sort):
            num_str = tup[1]
            buckets[int(num_str[length - 1])] -= 1
            sort_list[buckets[int(num_str[length - 1])]] = tup
        length -= 1
        numbers_to_sort = sort_list
    return numbers_to_sort


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
                    if tf_idf[0] == "1":
                        tf_idfs[word] = "1" + tf_idf[2:5]
                    else:
                        tf_idfs[word] = "0" + tf_idf[2:5]
        lst = []
        if len(tf_idfs) == 0:
            return []
        for word, ti in tf_idfs.items():
            lst.append(tuple([word, ti.zfill(4)]))
        print(lst)
        # Gets 5 words with the highest tf-idf
        self.train_frequencies(text)
        return radix_sort(lst)[-5:]
