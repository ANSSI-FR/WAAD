# ad-tree

ADTree library inspired from https://github.com/uraplutonium/adtree-py redesigned to suit ANSSI's and Sia Partners needs.


# Explanations:

/!\ Due to indices shift in the original library, meta_fields will map from 1 to number_attributes. But we managed
to get modalities back from 0 to number_modalities - 1 into `ContingencyTable.get_table()`. 
 