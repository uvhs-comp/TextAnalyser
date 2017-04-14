def quick_sort(numbers_to_sort):
    """
    Implementation of the quick sort algorithm
    """
    less = []
    greater = []
    equal = []

    if len(numbers_to_sort) > 1:
        pivot = int(numbers_to_sort[0][1])
        equal.append(numbers_to_sort[0])
        for x in range(1, len(numbers_to_sort)):
            if int(numbers_to_sort[x][1]) > pivot:
                greater.append(numbers_to_sort[x])
            elif int(numbers_to_sort[x][1]) < pivot:
                less.append(numbers_to_sort[x])
            else:
                equal.append(numbers_to_sort[x])
        return quick_sort(less) + equal + quick_sort(greater)
    else:
        return numbers_to_sort


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
