"""
Created on Sep 21, 2014
@author: Felix

Modified on Dec 29, 2020
@author: Alexandre
"""

from typing import List


class Dataset:
    """Defines a framework to use a raw dataset and convert it to symbolic."""

    def __init__(self, file_path: str, symbolic=False):
        self.__arity_name_list = []
        self.__arity_list: List[int] = []
        self.__data: List = []
        self.__arity_length = 0
        self.__data_num = 0
        self.__arities: List = []

        file = open(file_path)
        for i, eachline in enumerate(file):
            if i == 0:
                # the first line
                self.__arity_name_list = eachline[:-1].split(",")
                self.__arity_length = len(self.__arity_name_list)
                for i in range(0, self.__arity_length):
                    self.__arities.append(set())
            else:
                # the data field
                self.__data.append(eachline[:-1].split(","))
                for j, each_value in enumerate(self.__data[-1]):
                    self.__arities[j].add(each_value)

        self.__data_num = len(self.__data)
        for each_arity in self.__arities:
            self.__arity_list.append(len(each_arity))

        # convert __data and __arities to symbolic
        if symbolic:
            for i, each_entry in enumerate(self.__data):
                for j, each_value in enumerate(each_entry):
                    self.__data[i][j] = list(self.__arities[j]).index(each_value) + 1
            for j in range(0, self.__arity_length):
                self.__arities[j] = range(1, self.__arity_list[j] + 1)

    def get_arity_list(self):
        return self.__arity_list

    def get_type_list(self):
        return self.__typeList

    def count(self, query: List[int]):
        if "*" not in query:
            return self.__full_count(query)
        else:
            for i, each_attribute in enumerate(query):
                if each_attribute != "*":
                    continue
                else:
                    c = 0
                    for each_value in self.__arities[i]:
                        tmpQuery = query[:i] + [each_value] + query[i + 1 :]
                        c = c + self.count(tmpQuery)
                    return c

    def __full_count(self, query):
        return self.__data.count(query)

    def get_arity_length(self):
        return self.__arity_length

    def get_entry(self, row: int, column: int):
        return self.__data[row][column]

    def get_arity_names(self):
        return self.__arity_name_list

    def get_data_num(self):
        return self.__data_num

    def get_arities(self):
        return self.__arities

    def display_all(self):
        print("================================")
        print("====self.__arity_name_list")
        print(self.__arity_name_list)
        print("====self.__arity_list")
        print(self.__arity_list)
        print("\n====self.__arity_length")
        print(self.__arity_length)
        print("\n====self.__data_num")
        print(self.__data_num)
        print("\n====self.__arities")
        for each_arity in self.__arities:
            print(each_arity)
        print("================================")

    def print_data(self):
        print("\n====self.__data")
        print(self.__data)
