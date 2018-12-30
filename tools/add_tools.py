''' Block of auxiliary functions and operations to convert initial data about flow of
    goods from matrix form to long form


# function to find node name by its id
def find_node_name(look_up_table, node_id):
    node_name = look_up_table.loc[node_id, 'NAME']

    return node_name


# function to convert matrix to long table (with ids of nodes)
def to_long_table(matrix, matrix_name):
    src_ids = []
    dest_ids = []
    values = []
    types = []

    for src, dest_dic in matrix.iterrows():
        for dest, value in dest_dic.iteritems():
            src_ids.append(src)
            dest_ids.append(int(dest))
            types.append(matrix_name)
            values.append(value)

    datastore = {
        'src': src_ids,
        'dest': dest_ids,
        'type': types,
        'value': values
    }

    long_table_with_id = pd.DataFrame(datastore, columns=['src', 'dest', 'type', 'value'])
    long_table_with_id = long_table_with_id.sort_values(by=['src', 'dest']).copy()
    long_table_with_id = long_table_with_id[long_table_with_id.value > 0].reset_index(drop=True).copy()

    return long_table_with_id


# function to convert long table with ids to long table with names of nodes
def create_long_table_with_name(long_table_with_id, look_up_table):
    long_table_with_name = long_table_with_id.copy()

    for index in range(len(long_table_with_name)):
        src_id = long_table_with_name.loc[index, 'src']
        src_name = find_node_name(look_up_table, src_id)
        long_table_with_name.loc[index, 'src'] = src_name
        dest_id = long_table_with_name.loc[index, 'dest']
        dest_name = find_node_name(look_up_table, dest_id)
        long_table_with_name.loc[index, 'dest'] = dest_name

    return long_table_with_name

import os
import pandas as pd

work_dir = os.getcwd()
cargo1 = pd.read_csv(os.path.join(work_dir, "data/cargo1.csv"), sep=';', index_col='nodeID')
cargo2 = pd.read_csv(os.path.join(work_dir, "data/cargo2.csv"), sep=';', index_col='nodeID')
cargo3 = pd.read_csv(os.path.join(work_dir, "data/cargo3.csv"), sep=';', index_col='nodeID')
lut = pd.read_csv(os.path.join(work_dir, "data/look_up_table_Volga.csv"), sep=',', index_col='OBJECTID')

cargos = [
    {
        'id': 0,
        'name': 'cargo1',
        'matrix': cargo1
    },
    {
        'id': 1,
        'name': 'cargo2',
        'matrix': cargo2
    },
    {
        'id': 2,
        'name': 'cargo3',
        'matrix': cargo3
    }
]

cargo_data_frames_array = []

for cargo in cargos:
    matrix = cargo['matrix']
    matrix_name = cargo['name']
    cargo_long_table = to_long_table(matrix, matrix_name)
    cargo_data_frames_array.append(cargo_long_table)
    long_table = pd.concat(cargo_data_frames_array, ignore_index=True).sort_values(by=['src', 'dest']).copy()
    long_table = create_long_table_with_name(long_table, lut).reset_index(drop=True)


long_table.to_csv(os.path.join(work_dir, "data/long_table_Volga.csv"), index=False) '''








''' Code to generate random correspondence matrixes'''

'''
import pandas as pd
import os
import random

work_dir = os.getcwd()
cargo_3 = pd.read_excel(os.path.join(work_dir, 'data/cargo_test.xlsx'), sheet_name='cargo_test', index_col=0)

for index, row in cargo_3.iterrows():
    for col in cargo_3.columns.values:
        if index == col:
            row[col] = 0
        else:
            row[col] = random.randint(0, 10000)

cargo_3.to_excel(os.path.join(work_dir, 'data/cargo3.xlsx'), 'cargo3')

'''