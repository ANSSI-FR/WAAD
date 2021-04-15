'''
Created on Sep 25, 2014
@author: Felix

Modified on Dec 29, 2020
@author: Alexandre
'''
from typing import List


from ad_tree.dataset import Dataset


class FileRecord:
    """This class defines a framework for input data coming from a text or csv file."""

    def __init__(self, path: str):
        self.data = Dataset(path)
        self.arity_list = self.data.get_arity_list()
        self.arity_length = len(self.arity_list)
        self.records_length = self.data.get_data_num()

    def get_record(self, row: int, column: int):
        return int(self.data.get_entry(row, column))

    def count(self, query: List):
        return self.data.count(query)
