"""
Created on May 16, 2012
@author: Felix

Modified on Nov 29, 2020
@author: Alexandre
"""
from typing import List, Optional

from ad_tree.array_record import ArrayRecord


class ADNode(object):
    """The value of attribute this ADN is represented as the index of this ADN in its parent VN's children list
        eg. The index of this ADN in parent VN's children list is 2 (since the index starts from 0), if this ADN 
        is representing a3.
    """

    def __init__(
        self,
        start_attribute_num: int,
        record_nums: List[int],
        array_record: ArrayRecord,
    ):
        """Make a ADNode and its children nodes"""
        self.__count = len(record_nums)
        self.__children: List[Optional[VaryNode]] = [None] * (array_record.arity_length + 1 - start_attribute_num)
        for each_attribute_num in range(start_attribute_num, array_record.arity_length + 1):
            self.__children[each_attribute_num - start_attribute_num] = VaryNode(each_attribute_num, record_nums, array_record)
        self.array_record = array_record
        self.arity_length = array_record.arity_length

    def get_count(self):
        return self.__count

    def get_VN_child(self, attribute_num: int):
        """`attribute_num` ranges from 1 (NOT 0) to the max attribute number"""
        return self.__children[attribute_num + len(self.__children) - self.arity_length - 1]


class VaryNode(object):
    """The attribute number is represented as the index of this VN in its parent ADN's children list
        eg. The index of this VN in parent ADN's children list is 2 (since index starts from 0),
        if this VN is representing a3.
    """

    def __init__(self, attribute_num: int, record_nums: List[int], array_record: ArrayRecord):
        """Make a Vary Node and its children nodes"""
        self.__MCV = 0
        self.__children: List[Optional[ADNode]] = [None] * (array_record.arity_list[attribute_num - 1])

        # Initialises the child_num list for each attribute value
        child_nums: List[List] = [[] for each_attribute_value in range(array_record.arity_list[attribute_num - 1])]

        # This loop puts the amount for each attribute value into child_nums list from the recordsTable
        for each_record_num in record_nums:
            value = array_record.get_record(each_record_num - 1, attribute_num - 1)
            child_nums[value - 1].append(each_record_num)

        # Get the MCV from child_nums
        self.__MCV = child_nums.index(max(child_nums, key=len)) + 1

        # This loop creates AD-Nodes for each attribute value and attaches them to this Vary Node
        for each_attribute_value in range(1, array_record.arity_list[attribute_num - 1] + 1):
            if each_attribute_value != self.__MCV and child_nums[each_attribute_value - 1]:
                self.__children[each_attribute_value - 1] = ADNode(
                    attribute_num + 1,
                    child_nums[each_attribute_value - 1],
                    array_record,
                )

    def get_MCV(self):
        return self.__MCV

    def get_child(self, attribute_value: int):
        """attribute_value ranges from 1 (NOT 0) to the Record.arity_list[attribute_num]"""
        return self.__children[attribute_value - 1]
