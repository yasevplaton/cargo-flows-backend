## Скрипт для преобразования массива матриц корреспондеции в атрибуты ребер мультиграфа на примере реальных данных
# без сегментации дорог

import pandas as pd
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import LineString

# устанавливаем переменную с директорией, в которой лежат данные
dataDir = "C:\\My_work\\dissertation\\github\\linear-cartodiagram-backend\\data\\"

# читаем файлы c дорогами (линиями), точками
roads = gpd.read_file(dataDir + "shp\\roads.shp")
points = gpd.read_file(dataDir + "shp\\citiesJunctions.shp")

# считываем матрицы корреспонденции - 3 показателя - перевозка шоколада, бананов и апельсинов
chocolate = pd.read_csv(dataDir + "chocolateReal.csv", sep=';')
bananas = pd.read_csv(dataDir + "bananasReal.csv", sep=';')
oranges = pd.read_csv(dataDir + "orangesReal.csv", sep=';')

# записываем считанные матрицы в массив, чтобы можно было затем итерироваться по ним
matrix = [chocolate, bananas, oranges]

# определяем новые поля в таблице линий, в которых будут храниться идентификаторы соответствующих им узлов
roads["src"] = 0
roads["dest"] = 0
# добавляем поле с длиной каждой линии (в единицах исходной СК - должна быть не географическая)
roads["length"] = roads.length


# # заполняем столбцы src и dest идентификаторами соответствующих узлов

# определяем переменную цикла
i = 0
# для каждой линии:
while i < len(roads):
    # записываем в переменную var булеву колонку (Series) пересечения линии с точками (если пересечение есть - True)
    var = points.geometry.intersects(roads.loc[i, 'geometry'])
    # фильтруем точки по значениям в переменной var - получаем OBJECTID только тех точки, которые пересекаются с линией
    nodes = points.OBJECTID[var.values]
    # записываем в нужные ячейки таблицы линий значения идентификаторов узлов, соответствующих линии
    roads.loc[i, "src"] = nodes.iloc[0]
    roads.loc[i, "dest"] = nodes.iloc[1]
    # инкрементируем переменную цикла
    i += 1

# создаем массив из названий показателей, чтобы можно было итерироваться по ним
goods = ["chocolate", "bananas", "oranges"]

# создаем пустой мультиграф MG
MG = nx.MultiGraph()
# # заполняем мультиграф ребрами из lines
# для каждого показателя:
for g, ord in zip(goods, range(len(goods))):
    # создаем временный граф на основе таблицы lines
    G = nx.from_pandas_edgelist(roads, source="src", target="dest", edge_attr=["ID_line", "length"])
    # к каждому ребру добавляем исходное для расчетов значение показателя, равное нулю
    nx.set_edge_attributes(G, 0, g)
    # к каждому ребру добавляем значение порядка отрисовки (от 0 до n-1, где n - число показателей)
    nx.set_edge_attributes(G, ord, 'ORD')
    # добавляем ребра с атрибутами из графа G в граф MG
    MG.add_edges_from(G.edges.data())
    # очищаем временный граф G
    G.clear()

# конвертируем мультиграф в ориентированный мультиграф
# на выходе: число ребер = число линий * количество показателей * 2
net = MG.to_directed()


# заполняем атрибуты принадлежности точки к городу узлов графа

# создаем пустой словарь
values = {}
# для каждой точки
for n in range(len(points)):
    # заполняем словарь по структуре: {OBJECTID точки: OBJECTID города}
    values[points.OBJECTID[n]] = points.NAME[n]

# добавляем к узлам графа атрибут city и заполняем его на основе словаря values
nx.set_node_attributes(net, values, 'city')

# заполняем атрибуты ребер кумулятивными значениями показателей

# для каждого узла
for s, ds in net.nodes.items():
    # если в узле есть город
    if ds['city'] != 'junction':
        # отбираем последовательно каждый узел графа
        for t, dt in net.nodes.items():
            # если в узле есть город
            if dt['city'] != 'junction':
                # строим самый короткий по расстоянию маршрут между текущими узлами, получаем массив узлов
                route = nx.shortest_path(net, source=s, target=t, weight="length")
                # создаем вспомогательный линейный граф H на основе полученного массива узлов
                H = nx.path_graph(route)
                # для каждого ребра в H:
                for e in H.edges:
                    # устанавливаем начальное значение счетчика идентификаторов ребер в пределах мультиребра
                    j = 0
                    # для каждого показателя и соответсвующей ему матрицы корреспонденции:
                    for g, m in zip(goods, matrix):
                        # так как nx.shortest_path строит маршрут также и между одинаковыми узлами (s = t),
                        # ставим условие, что учитывам только маршруты между разными узлами (s != t)
                        if s != t:
                            # прибавляем к текущему значению показателя у ребра значение ячейки в соответствующей
                            # матрице корреспонденции для текущей пары узлов s, t
                            net.edges[e[0], e[1], j][g] = net.edges[e[0], e[1], j][g] + m.iloc[s - 1, t]
                            # инкрементируем значение счетчика идентификаторов ребер в пределах мультиребра
                            j += 1
                # очищаем временный граф H
                H.clear()


# создание фрейма данных на основе данных ребер полученного графа

# определение пустых списков (будущих полей фрейма)

sources = []
destination = []
id_line = []
types = []
values = []
order = []

# заполнение списков данными ребер
for n1, n2, dattr in net.edges.data():
    sources.append(n1)
    destination.append(n2)
    id_line.append(dattr['ID_line'])
    order.append(dattr['ORD'])
    for k, v in dattr.items():
        if k in goods:
            types.append(k)
            values.append(v)

# получение финального словаря, на основе которого будет создаваться dataframe
datastore = {'src': sources,
             'dest': destination,
             'ID_line': id_line,
             'type': types,
             'value': values,
             'order': order}

# создание фрейма данных
edgesDF = pd.DataFrame(datastore, columns=['src', 'dest', 'ID_line', 'type', 'value', 'order'])

# сортировка датафрейма по идентификатору линии, затем по ID узла-источника, затем по ID узла-назначения
edgesDF = edgesDF.sort_values(by=['ID_line', 'src', 'dest']).copy()

# переопределяем индексы строк (от 0 до общего количества ребер)
edgesDF.index = range(len(edgesDF))

# добавляем столбец, кодирующие направление перемещения груза, сначала заполняем его нулями
edgesDF['dir'] = 0

# определяем новый порядок столбцов - чтобы dir стоял перед order
edgesDF = edgesDF[['src', 'dest', 'ID_line', 'type', 'value', 'dir', 'order']].copy()

# заполняем столбец dir кодами направления перемещения 1 и -1
for s in edgesDF.index:
    var = edgesDF.src[s] - edgesDF.dest[s]
    if var < 0:
        edgesDF.loc[s, 'dir'] = 1
    else:
        edgesDF.loc[s, 'dir'] = -1

# присоединяем геометрию линий на основе ключевого поля идентификатора линии
roadGeom = roads[['ID_line', 'geometry']]
edgesDF = edgesDF.merge(roadGeom, on='ID_line')

# преобразуем полученный dataframe в geodataframe
geoEdges = gpd.GeoDataFrame(edgesDF, crs=roads.crs, geometry='geometry')

# функция обратной сортировки последовательности узлов линии
# аргумент функции - объект LineString, возвращает объект LineString с обратной последовательностью узлов

def reverseGeometryLine(line):
    # создаем пустой список,
    coordArr = []
    # куда записываем координаты узлов линии в исходном порядке
    for i in line.coords:
        coordArr.append(i)
    # создаем новый список,
    revArr = []
    # куда записываем координаты узлов линии в обратном порядке
    for i in reversed(coordArr):
        revArr.append(i)
    # преобразуем полученный список координат в объект LineString
    revLine = LineString(revArr)
    # и возвращаем его в качестве результата функции
    return(revLine)


# изменение порядка координат узлов линии в случае, если координаты исходного узла не совпадают с координатами
# точки-источника
for l in range(len(geoEdges)):
    srcID = geoEdges.src[l]
    src = points[(points.OBJECTID == srcID)]
    srcGeom = src.geometry.iloc[0]
    xSource = srcGeom.x
    ySource = srcGeom.y
    lineGeom = geoEdges.geometry.iloc[l]
    firstNode = lineGeom.coords[0]
    if firstNode[0] != xSource or firstNode[1] != ySource:
        geoEdges.loc[l, 'geometry'] = reverseGeometryLine(lineGeom)


# записываем geodataframe в шейп-файл
geoEdges.to_file(dataDir + "shp\\edges.shp", 'ESRI Shapefile')