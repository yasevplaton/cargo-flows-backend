import pandas as pd
import geopandas as gpd
import os.path
from tools import tools


# get data
# data = request.data
#
# # decode data
# init_table = io.StringIO(data.decode('utf-8'))

# set path to data directory
# path to data directory at localhost for testing purposes
data_dir = "data/"

# path to data directory in production
# data_dir = '/home/yasevplaton/linear-cartodiagram-backend/data/'

# read files
roads = gpd.read_file(os.path.join(data_dir, "roadsVolga.geojson"))
points = gpd.read_file(os.path.join(data_dir, "pointsVolga.geojson"))
lut = pd.read_csv(os.path.join(data_dir, "look_up_table_Volga.csv"), sep=",", index_col="OBJECTID")
flow_table = pd.read_csv(os.path.join(data_dir, "long_table_Volga.csv"), sep=",")

# transform to 3857
roads = roads.to_crs({'init': 'epsg:3857'})
points = points.to_crs({'init': 'epsg:3857'})

# convert flow table to array of correspondence matrixes
matrix_array = tools.to_matrix_array(flow_table, lut)

# collect types of goods
goods = tools.collect_goods_types(matrix_array)

# create oriented multigraph and fill it with edges from roads
net = tools.create_graph(goods, roads)

# determine the affiliation of a node to a city
net = tools.add_city_affiliation_attr(points, net)

# distribute values of flows of goods on graph's edges
# net = tools.distribute_values_on_graph(net, goods, matrix_array)
net = tools.distribute_values_on_graph(net, goods, matrix_array)

# create dataframe from multigraph
edges_df = tools.create_dataframe_from_graph(net, goods)

# create geodataframe by merging dataframe and roads geometry
road_geometry = roads[['ID_line', 'geometry']]
edges_df = edges_df.merge(road_geometry, on='ID_line')
geo_edges = gpd.GeoDataFrame(edges_df, crs=roads.crs, geometry='geometry')

# reverse order of nodes in line if a first node in line is not a source node
geo_edges = tools.reverse_nodes_order(geo_edges, points)

# reproject edges to 4326
geo_edges = geo_edges.to_crs({'init': 'epsg:4326'})

with open(os.path.join(data_dir, "edgesVolga.geojson"), 'w') as f:
    f.write(geo_edges.to_json())