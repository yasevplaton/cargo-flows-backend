
'''

The script for the distribution of data from the table of flows of goods through the transport network graph

'''


# import necessary modules
import pandas as pd
import geopandas as gpd
import networkx as nx
import os.path
from tools import tools

# set data directory
data_dir = "data/"

# read files
roads = gpd.read_file(os.path.join(data_dir, "shp/roads.shp"))
points = gpd.read_file(os.path.join(data_dir, "shp/citiesJunctions.shp"))
lut = pd.read_csv(os.path.join(data_dir, "look_up_table.csv"), sep=",", index_col="OBJECTID")
flow_table = pd.read_csv(os.path.join(data_dir, "long_table.csv"), sep=",")

# convert flow table to array of correspondence matrixes
matrix_array = tools.to_matrix_array(flow_table, lut)

# add additional fields to roads table
roads["src"] = 0
roads["dest"] = 0
roads["length"] = roads.length

# bind points and roads
i = 0
while i < len(roads):
    var = points.geometry.intersects(roads.loc[i, 'geometry'])
    nodes = points.OBJECTID[var.values]
    roads.loc[i, "src"] = nodes.iloc[0]
    roads.loc[i, "dest"] = nodes.iloc[1]
    i += 1

# collect types of goods
goods = []
for good in matrix_array:
    goods.append(good['type'])

# create oriented multigraph and fill it with edges from roads
MG = nx.MultiGraph()

for g, ord in zip(goods, range(len(goods))):
    G = nx.from_pandas_edgelist(roads, source="src", target="dest", edge_attr=["ID_line", "length"])
    nx.set_edge_attributes(G, 0, g)
    nx.set_edge_attributes(G, ord, 'ORD')
    MG.add_edges_from(G.edges.data())
    G.clear()

net = MG.to_directed()

# determine the affiliation of a node to a city
values = {}
for n in range(len(points)):
    values[points.OBJECTID[n]] = points.NAME[n]

nx.set_node_attributes(net, values, 'city')

# distribute values of flows of goods on graph's edges
for s, ds in net.nodes.items():
    # if source and destination nodes are not junctions
    if ds['city'] != 'junction':
        for t, dt in net.nodes.items():
            if dt['city'] != 'junction':
                # create the shortest path between source and destination
                route = nx.shortest_path(net, source=s, target=t, weight="length")
                # create path graph from found nodes
                H = nx.path_graph(route)
                for e in H.edges:
                    j = 0
                    for g, m in zip(goods, matrix_array):
                        # if source node is not destination node
                        if s != t:
                            # increase value of specific type of good by value from matrix of this type of good
                            net.edges[e[0], e[1], j][g] = net.edges[e[0], e[1], j][g] + m['data'].loc[s, t]
                            j += 1
                H.clear()

# create dataframe from multigraph
sources = []
destination = []
id_line = []
types = []
values = []
order = []

for n1, n2, dattr in net.edges.data():
    sources.append(n1)
    destination.append(n2)
    id_line.append(dattr['ID_line'])
    order.append(dattr['ORD'])
    for k, v in dattr.items():
        if k in goods:
            types.append(k)
            values.append(v)

datastore = {'src': sources,
             'dest': destination,
             'ID_line': id_line,
             'type': types,
             'value': values,
             'order': order}

edges_df = pd.DataFrame(datastore, columns=['src', 'dest', 'ID_line', 'type', 'value', 'order'])
edges_df = edges_df.sort_values(by=['ID_line', 'src', 'dest']).copy()
edges_df.index = range(len(edges_df))
edges_df['dir'] = 0
edges_df = edges_df[['src', 'dest', 'ID_line', 'type', 'value', 'dir', 'order']].copy()

# fill direction column with ids of direction
for s in edges_df.index:
    var = edges_df.src[s] - edges_df.dest[s]
    if var < 0:
        edges_df.loc[s, 'dir'] = 1
    else:
        edges_df.loc[s, 'dir'] = -1

# create geodataframe by merging dataframe and roads geometry
road_geometry = roads[['ID_line', 'geometry']]
edges_df = edges_df.merge(road_geometry, on='ID_line')
geo_edges = gpd.GeoDataFrame(edges_df, crs=roads.crs, geometry='geometry')

# reverse order of nodes in line if a first node in line is not a source node
for l in range(len(geo_edges)):
    src_id = geo_edges.src[l]
    src = points[(points.OBJECTID == src_id)]
    src_geom = src.geometry.iloc[0]
    x_src = src_geom.x
    y_src = src_geom.y
    line_geom = geo_edges.geometry.iloc[l]
    first_node = line_geom.coords[0]
    if first_node[0] != x_src or first_node[1] != y_src:
        geo_edges.loc[l, 'geometry'] = tools.reverse_geometry_line(line_geom)

# write geodataframe to geojson
path_to_file = os.path.join(data_dir, 'edges.geojson')
with open(path_to_file, 'w') as f:
    f.write(geo_edges.to_json())
    f.close()
