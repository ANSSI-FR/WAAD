"""
Created on Jul 30, 2012
@author: Felix

Modified on Dec 29, 2020
@author: Alexandre

The following improvement methods are used:
1. Using tree structure instead of linear structure such like list or dict
2. Using one loop/iteration to build Contingency table instead of recursion
3. Using list of lists to represent tree structure instead of having a "Node" class
"""
from typing import List, Optional, Union

from ad_tree.sparse_ADTree import ADNode


class ContingencyTable(object):
    """This class defines a framework for contingency table. It implements some methods to interact with the table that is computed as a tree.

    Attributes:
        attribute_list (List[int]): List containing the attributes to gather in our ContingencyTable. They range from 1 to max_attribute_number.
        adtree (ADNode): ADTree we want to collect data from.
    """

    def __init__(self, attribute_list: List[int], ad_tree: ADNode):
        attribute_index = 0
        self.__attribute_list = attribute_list
        self.__arity_list: List[int] = [ad_tree.array_record.arity_list[i - 1] for i in attribute_list]
        self.__ctTree: List = [0] * ad_tree.array_record.arity_list[attribute_list[attribute_index] - 1]
        self.__dimension = len(attribute_list)
        stack: List[Union[List, Optional[int], ADNode]] = [self.__ctTree, None, ad_tree]

        while stack:
            ADN = stack.pop()
            if ADN == -1:  # make MCV
                MCV: int = stack.pop()
                ctTree: List[int] = stack.pop()
                if attribute_index > self.__dimension - 1:  # if the depth of whole ctTree is only 1
                    for each_attribute_value in range(1, ad_tree.array_record.arity_list[attribute_list[attribute_index - 1] - 1] + 1):
                        if each_attribute_value != MCV:
                            ctTree[MCV - 1] -= ctTree[each_attribute_value - 1]
                else:
                    for each_attribute_value in range(1, ad_tree.array_record.arity_list[attribute_list[attribute_index - 1] - 1] + 1):
                        if each_attribute_value != MCV:
                            is_result_zero = self.sub_in_tree(ctTree[MCV - 1], ctTree[each_attribute_value - 1], self.__dimension - attribute_index)
                            if is_result_zero:
                                ctTree[MCV - 1] = 0
                attribute_index -= 1
            elif ADN:  # expand AD-node
                if attribute_index < self.__dimension:  # AD-node that has Vary node children
                    atr_value = stack.pop()
                    ctTree: List = stack[-1]  # note it's not stack.pop()
                    VN = ADN.get_VN_child(attribute_list[attribute_index])
                    MCV = VN.get_MCV()
                    stack.append(MCV)
                    stack.append(-1)
                    for attribute_value in range(ad_tree.array_record.arity_list[attribute_list[attribute_index] - 1], 0, -1):
                        ADNToPush = None
                        if attribute_value != MCV:
                            ADNToPush = VN.get_child(attribute_value)
                        else:
                            ADNToPush = ADN
                        if ADNToPush:
                            if attribute_index + 1 < self.__dimension:  # if the depth of ctTree is larger than 1
                                ctTree[attribute_value - 1] = [0] * ad_tree.array_record.arity_list[attribute_list[attribute_index + 1] - 1]
                                stack.append(ctTree[attribute_value - 1])
                            else:
                                stack.append(ctTree)
                            stack.append(attribute_value)
                        stack.append(ADNToPush)
                    attribute_index += 1
                else:  # leaf AD-node
                    atr_value = stack.pop()
                    ctTree = stack.pop()
                    ctTree[atr_value - 1] = ADN.get_count()
            # else: zero AD-node with subtree or a single leaf

    def sub_in_tree(self, MCV_tree: ADNode, other_tree: ADNode, depth: int):
        if other_tree and MCV_tree:
            is_MCV_tree_zero = False
            for i, each_child in enumerate(MCV_tree):
                if depth <= 1:
                    MCV_tree[i] -= other_tree[i]
                    is_MCV_tree_zero = is_MCV_tree_zero or MCV_tree[i]
                else:
                    is_result_zero = self.sub_in_tree(MCV_tree[i], other_tree[i], depth - 1)
                    if is_result_zero:
                        MCV_tree[i] = 0
                    is_MCV_tree_zero = is_MCV_tree_zero or (not is_result_zero)
            is_MCV_tree_zero = not is_MCV_tree_zero
            return is_MCV_tree_zero

    def get_count(self, query: List[int]):
        CTN = self.__ctTree
        for each_num in query:
            CTN = CTN[each_num - 1]
            if not CTN:
                return 0
        return CTN

    def get_table(self):
        table = {}

        def get_tuples(L: List, prev_indices: List):
            for i, e in enumerate(L):
                if isinstance(e, int):
                    if e != 0:
                        table[tuple(prev_indices + [(i + 1) % self.__arity_list[len(prev_indices)]])] = e  # Due to the fact that attribute values start from 1 (NOT 0)
                else:
                    get_tuples(e, prev_indices + [(i + 1) % self.__arity_list[len(prev_indices)]])

        get_tuples(self.__ctTree, [])
        return table
