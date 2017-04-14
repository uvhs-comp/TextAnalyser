class DataPos:
    """
    Class to act as a node in the stack

    Properties:
        data - holds the information about that node
        position - holds the posititon of the data in the external structure
        extra_info - any extra data that needs to persist
    """
    def __init__(self, data, position, extra_info={}):
        self.data = data
        self.position = position
        self.extra_info = extra_info


class word_stack:
    """
    Stack used when doing operation with the texts

    Properties:
        __stack - list used to hold the nodes
        __top_of_stack - pointer to the most recent list element
        __size - maximum size of the stack

    Methods:
        is_empty - returns True if stack is empty, False if not
        __is_full - returns True if stack is full, False if not
        get_height - returns the current height of the stack
        peek - returns the top item of the stack
        pop - returns and removes the top item of the stack
        add - inserts an item at the top of the stack
    """
    def __init__(self, size=5):
        self.__stack = [None] * size
        self.__top_of_stack = -1
        self.__size = size

    def is_empty(self):
        return self.__top_of_stack == -1

    def __is_full(self):
        return self.__top_of_stack == self.__size - 1

    def get_height(self):
        return self.__top_of_stack + 1

    def peek(self):
        if not self.is_empty():
            return self.__stack[self.__top_of_stack]
        return False

    def pop(self):
        if not self.is_empty():
            top_item = self.__stack[self.__top_of_stack]
            self.__stack[self.__top_of_stack] = None
            self.__top_of_stack -= 1
            return top_item
        return False

    def add(self, data):
        if not self.__is_full():
            self.__top_of_stack += 1
            self.__stack[self.__top_of_stack] = data


class circular_queue:
    """
    Circular queue to compare words
    Size can be increased to compare words that are a further distance apart

    Properties:
        max_size - maximum size of the queue
        current_size - current number of items in the queue
        queue - list used to hold the data nodes
        front_pointer - start of the queue
        end_pointer - end of the queue

    Methods:
        is_empty - returns True if queue is empty, False if not
        __is_full - returns True if queue is full, False if not
        peek_at_end - returns the last item of the queue
        dequeue - removes and return the item at the start of the queue
        enqueue - inserts an item at the end of the queue
    """
    def __init__(self, size=2):
        self.max_size = size
        self.current_size = 0
        self.queue = [None] * self.max_size
        self.front_pointer = 0
        self.rear_pointer = -1

    def is_empty(self):
        return self.current_size == 0

    def __is_full(self):
        return self.current_size == self.max_size

    def peek_at_end(self):
        if self.is_empty():
            return False
        item = self.queue[self.rear_pointer]
        return item

    def enqueue(self, newItem):
        if self.__is_full():
            return False
        self.rear_pointer = (self.rear_pointer + 1) % self.max_size
        self.queue[self.rear_pointer] = newItem
        self.current_size += 1

    def dequeue(self):
        if self.is_empty():
            return False
        item = self.queue[self.front_pointer]
        self.front_pointer = (self.front_pointer + 1) % self.max_size
        self.current_size -= 1
        return item


class sentiment_queue(circular_queue):
    """
    Inherits from the circular queue and adds a method that compares the
    sentiment of the first and last items in the queue

    Methods:
        check_sentiments - Compares the sentiment of the last and first items in the queue
                           if the difference in sentiments is greater than 3, returns the items
                           if not then return False
    """

    def __init__(self):
        super().__init__()

    def check_sentiments(self):
        if self.current_size == 2:
            end = self.peek_at_end()
            start = self.dequeue()
            end_sent = end.extra_info['sentiment']
            start_sent = start.extra_info['sentiment']
            if abs(end_sent - start_sent) > 3:
                return start, end
            return False, False
        return False, False
