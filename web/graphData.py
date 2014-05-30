import json
from database import NodeDB
from graph import Node, Edge

def insert_graph_data(config, json_str):
	try:
		graph_data = json.loads(json_str)
	except ValueError:
		return False

	nodes = dict()
	edges = []

	if not 'nodes' in graph_data or not 'edges' in graph_data:
		return False
	

	try:
		for n in graph_data['nodes']:
			node = Node(n['ip'], version=n['version'])
			nodes[n['ip']] = node

		for e in graph_data['edges']:
			edge = Edge(nodes[e['a']], nodes[e['b']])
			edges.append(edge)

	except TypeError:
		return False

	print "Received %d nodes and %d links." % (len(nodes), len(edges))

	with NodeDB(config) as db:
		db.insert_graph(nodes, edges)

	return True
