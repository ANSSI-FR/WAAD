"""
Created on Jun 23, 2012
@author: Felix

Modified on Nov 9, 2020
@author: Alexandre
"""
from typing import List


class ArrayRecord:
    """This class defines a framework for input data. It implements some methods to interact with the table.

    Attributes:
        arity_list (List[int]): List containing the arities of all meta-fields.
        records_table (List[int]): Table of records in categories format.
        arity_length (int) : Length of arity_list.
        records_length (int) : Number of records.
    """
    def __init__(self, arity_list: List[int], records_table: List[int]):
        self.arity_list = arity_list
        self.records_table = records_table
        self.arity_length = len(self.arity_list)
        self.records_length = len(self.records_table)

    def get_record(self, row: int, column: int):
        return self.records_table[row][column]

    def count(self, query: List[int]):
        return self.records_table.tolist().count(query)
