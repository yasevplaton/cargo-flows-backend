''' Additional functions'''

import pandas as pd
from shapely.geometry import LineString
import networkx as nx

'''

Block of functions to convert initial data from long form to form of array of correspondence matrixes

'''


# function to find node id by its name
def find_node_id(look_up_table, node_name):
    node_id = look_up_table[look_up_table.name_rus == node_name].index.values[0]
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


# function to bind points to lines
def bind_points_to_lines(points, lines):
    binded_lines = lines
    i = 0
    while i < len(binded_lines):
        var = points.geometry.intersects(binded_lines.loc[i, 'geometry'])
        nodes = points.OBJECTID[var.values]
        binded_lines.loc[i, "src"] = nodes.iloc[0]
        binded_lines.loc[i, "dest"] = nodes.iloc[1]
        i += 1

    return binded_lines


# function to collect types of goods
def collect_goods_types(matrix_array):
    goods_array = []
    for good in matrix_array:
        goods_array.append(good['type'])

    return goods_array


# function to create oriented multigraph
def create_graph(goods_array, lines):
    MG = nx.MultiGraph()

    for g, ord in zip(goods_array, range(len(goods_array))):
        temp_graph = nx.from_pandas_edgelist(lines, source="src", target="dest", edge_attr=["ID_line", "length"])
        nx.set_edge_attributes(temp_graph, 0, g)
        nx.set_edge_attributes(temp_graph, ord, 'ORD')
        MG.add_edges_from(temp_graph.edges.data())
        temp_graph.clear()

    net = MG.to_directed()

    return net


# function to add attribute of affiliation of a node to a city
def add_city_affiliation_attr(points, graph):
    values = {}
    for n in range(len(points)):
        values[points.OBJECTID[n]] = points.NAME[n]

    nx.set_node_attributes(graph, values, 'city')

    return graph


# function to distribute values of flows on graph
def distribute_values_on_graph(graph, goods_array, matrix_array):
    for s, ds in graph.nodes.items():
        # if source and destination nodes are not junctions
        if ds['city'] != 'junction':
            for t, dt in graph.nodes.items():
                if dt['city'] != 'junction':
                    # if source node is not destination node
                    if s != t:
                        # create the shortest path between source and destination
                        route = nx.shortest_path(graph, source=s, target=t, weight="length")
                        # create path graph from found nodes
                        path_graph = nx.path_graph(route)
                        for e in path_graph.edges:
                            # set counter for edge
                            j = 0
                            for g, m in zip(goods_array, matrix_array):
                                # increase value of specific type of good by value from matrix of this type of good
                                graph.edges[e[0], e[1], j][g] = graph.edges[e[0], e[1], j][g] + m['data'].loc[s, t]
                                # increment counter
                                j += 1
                        path_graph.clear()

    return graph


# function to create frame from filled graph
def create_dataframe_from_graph(graph, goods_array):
    sources = []
    destination = []
    id_line = []
    types = []
    values = []
    order = []

    for n1, n2, dattr in graph.edges.data():
        sources.append(n1)
        destination.append(n2)
        id_line.append(dattr['ID_line'])
        order.append(dattr['ORD'])
        for k, v in dattr.items():
            if k in goods_array:
                types.append(k)
                values.append(v)

    datastore = {'src': sources,
                 'dest': destination,
                 'ID_line': id_line,
                 'type': types,
                 'value': values,
                 'order': order}

    dataframe = pd.DataFrame(datastore, columns=['src', 'dest', 'ID_line', 'type', 'value', 'order'])
    dataframe = dataframe.sort_values(by=['ID_line', 'src', 'dest']).copy()
    dataframe.index = range(len(dataframe))
    dataframe['dir'] = 0
    dataframe = dataframe[['src', 'dest', 'ID_line', 'type', 'value', 'dir', 'order']].copy()

    # fill direction column with ids of direction
    for s in dataframe.index:
        var = dataframe.src[s] - dataframe.dest[s]
        if var < 0:
            dataframe.loc[s, 'dir'] = 1
        else:
            dataframe.loc[s, 'dir'] = -1

    return dataframe


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


# function to reverse order of nodes in line
def reverse_nodes_order(geodataframe, points):
    for edge in range(len(geodataframe)):
        src_id = geodataframe.src[edge]
        src = points[(points.OBJECTID == src_id)]
        src_geom = src.geometry.iloc[0]
        x_src = src_geom.x
        y_src = src_geom.y
        line_geom = geodataframe.geometry.iloc[edge]
        first_node = line_geom.coords[0]
        if first_node[0] != x_src or first_node[1] != y_src:
            geodataframe.loc[edge, 'geometry'] = reverse_geometry_line(line_geom)

    return geodataframe
