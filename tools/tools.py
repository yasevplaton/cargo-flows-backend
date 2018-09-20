''' Additional functions'''

import pandas as pd
from shapely.geometry import LineString

'''

Block of functions to convert initial data from long form to form of array of correspondence matrixes

'''


# function to find node id by its name
def find_node_id(look_up_table, node_name):
    node_id = look_up_table[look_up_table.NAME == node_name].index.values[0]
    return node_id


# function to convert long table with names to long table with ids of nodes
def create_long_table_with_id(long_table_with_name, look_up_table):
    long_table_with_id = long_table_with_name.copy()

    for index in range(len(long_table_with_id)):
        src_name = long_table_with_id.loc[index, 'src']
        src_id = find_node_id(look_up_table, src_name)
        long_table_with_id.loc[index, 'src'] = src_id
        dest_name = long_table_with_id.loc[index, 'dest']
        dest_id = find_node_id(look_up_table, dest_name)
        long_table_with_id.loc[index, 'dest'] = dest_id

    return long_table_with_id


# function to create empty matrix on base of nodes' ids
def create_empty_matrix(long_table_with_id):
    src_id_array = long_table_with_id.src.unique()
    src_id_array.sort()
    dest_id_array = long_table_with_id.dest.unique()
    dest_id_array.sort()
    empty_matrix = pd.DataFrame(data=0, index=src_id_array, columns=dest_id_array)
    return empty_matrix


# function to fill empty matrix of good with values
def fill_matrix(good_table, empty_matrix):
    filled_matrix = empty_matrix.copy()
    for index, tuple in good_table.iterrows():
        filled_matrix.loc[tuple.src, tuple.dest] = tuple.value

    return filled_matrix


# function to convert long table to array of matrixes
def to_matrix_array(long_table_with_name, look_up_table):
    matrix_array = []
    long_table_with_id = create_long_table_with_id(long_table_with_name, look_up_table)
    empty_matrix = create_empty_matrix(long_table_with_id)
    goods_array = long_table_with_id.type.unique()

    good_id = 0
    for good in goods_array:
        good_table = long_table_with_id[long_table_with_id.type == good]
        good_matrix = fill_matrix(good_table, empty_matrix)
        matrix_array.append({
            'id': good_id,
            'type': good,
            'data': good_matrix
        })
        good_id += 1

    return matrix_array


''' 

Other functions

'''


# function to reverse line geometry
def reverse_geometry_line(line):
    coord_arr = []
    for i in line.coords:
        coord_arr.append(i)
    rev_arr = []
    for i in reversed(coord_arr):
        rev_arr.append(i)
    rev_line = LineString(rev_arr)
    return(rev_line)
