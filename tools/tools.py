import pandas as pd
import geopandas as gpd

data_dir = "C:\\My_work\\dissertation\\github\\linear-cartodiagram-backend\\data\\"


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
    long_table

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

chocolate = pd.read_csv(data_dir + "chocolateReal.csv", sep=';', index_col='nodeID')
bananas = pd.read_csv(data_dir + "bananasReal.csv", sep=';', index_col='nodeID')
oranges = pd.read_csv(data_dir + "orangesReal.csv", sep=';', index_col='nodeID')
lut = pd.read_csv(data_dir + 'nodesID.csv', sep=',', index_col='OBJECTID')

goods = [
    {
        'id': 0,
        'name': 'chocolate',
        'matrix': chocolate
    },
    {
        'id': 1,
        'name': 'bananas',
        'matrix': bananas
    },
    {
        'id': 2,
        'name': 'oranges',
        'matrix': oranges
    }
]

good_data_frames_array = []

for good in goods:
    matrix = good['matrix']
    matrix_name = good['name']
    good_long_table = to_long_table(matrix, matrix_name)
    good_data_frames_array.append(good_long_table)
    long_table = pd.concat(good_data_frames_array, ignore_index=True).sort_values(by=['src', 'dest']).copy()
    long_table = create_long_table_with_name(long_table, lut).reset_index(drop=True)
    

long_table.to_csv(data_dir + 'long_table.csv', index=False)
-
-
-


'''

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


# function to convert long table (with ids of nodes to array of matrixes)
def to_matrix_array(long_table_with_id):
    matrix_array = []
    return matrix_array

def get_unique_values(column):

    return unique_array

def create_empty_matrix(src_id_array, dest_id_array):

    return empty_matrix

def fill_matrix():

    return filled_matrix


# read data
lut = pd.read_csv(data_dir + 'look_up_table.csv', sep=',', index_col='OBJECTID')
long_table = pd.read_csv(data_dir + 'long_table.csv', sep=',')

# match node name with node id
long_table_with_id = create_long_table_with_id(long_table, lut)







