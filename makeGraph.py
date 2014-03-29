#!/usr/bin/env python

from mapperconf_sh import *
import sys
sys.path.append(cjdns_path + '/contrib/python/cjdnsadmin/')
import adminTools as admin
from collections import deque
import pygraphviz as pgv
import json
import time
import httplib2

class Node:
	def __init__(self, ip):
		self.ip = ip
		self.version = -1
		self.label = ip[-4:]

	def __lt__(self, b):
		return self.ip < b.ip

class Edge:
	def __init__(self, a, b):
		self.a, self.b = sorted([a, b])

all_nodes = dict()
all_edges = []
these_nodes = dict()
these_edges = []

def add_node(node):
	if not node in all_nodes:
		all_nodes[node.ip] = node
	if not node in these_nodes:
		these_nodes[node.ip] = node

def add_edge(e):
	all_edges.append(e)
	these_edges.append(e)

def has_edge(a, b):
	a, b = sorted([a, b])

	for e in these_edges:
		if e.a.ip == a and e.b.ip == b:
			return True
	return False

for port in range(rpc_firstport, rpc_firstport + num_of_nodes):
	print port,
	these_nodes = dict()
	these_edges = []
	cjdns = admin.connect(rpc_connect, port, rpc_pw)
	root = admin.whoami(cjdns)
	rootIP = root['IP']
	print rootIP

	add_node(Node(rootIP))

	nodes = deque()
	nodes.append(rootIP)

	while len(nodes) != 0:
		parentIP = nodes.popleft()
		resp = cjdns.NodeStore_nodeForAddr(parentIP)
		numLinks = 0

		if 'result' in resp:
			link = resp['result']
			if 'linkCount' in link:
				numLinks = int(resp['result']['linkCount'])
				all_nodes[parentIP].version = resp['result']['protocolVersion']

			for i in range(0, numLinks):
				resp = cjdns.NodeStore_getLink(parentIP, i)
				childLink = resp['result']

				if not 'child' in childLink:
					print 'No child'
					continue
				childIP = childLink['child']

				# Check to see if its one hop away from parent node
				if childLink['isOneHop'] != 1:
					continue

				# If its a new node then we want to follow it
				if not childIP in these_nodes:
					add_node(Node(childIP))
					nodes.append(childIP)

				# If there is not a link between the nodes we should put one there
				if not has_edge(childIP, parentIP):
					add_edge(Edge(these_nodes[childIP], these_nodes[parentIP]))
	# cjdns.disconnect()

	print (len(these_nodes), len(these_edges))
	# print 'Number of nodes:', G.number_of_nodes()
	# print 'Number of edges:', G.number_of_edges()

print "Total", (len(all_nodes), len(all_edges))

G = pgv.AGraph(strict=True, directed=False, size='10!')

for n in all_nodes.values():
	G.add_node(n.ip, label=n.label, version=n.version)

for e in all_edges:
	G.add_edge(e.a.ip, e.b.ip, len=1.0)

G.layout(prog='neato', args='-Gepsilon=0.0001 -Gmaxiter=100000') # neato, fdp, dot


max_neighbors = 0

for n in G.iternodes():
	neighbors = len(G.neighbors(n))
	if neighbors > max_neighbors:
		max_neighbors = neighbors

print 'Max neighbors:', max_neighbors



def download_node_names():
	print "Downloading names"
	page = 'http://[fc5d:baa5:61fc:6ffd:9554:67f0:e290:7535]/nodes/list.json'

	ip_dict = dict()
	h = httplib2.Http(".cache", timeout=15.0)
	try:
		r, content = h.request(page, "GET")
		nameip = json.loads(content)['nodes']

		for node in nameip:
			ip_dict[node['ip']] = node['name']

		print "Names downloaded"
	except Exception as e:
		print "Connection to Mikey's nodelist failed, continuing without names", e

	return ip_dict


node_names = download_node_names()

def gradient_color(ratio, colors):
	jump = 1.0 / (len(colors) - 1)
	gap_num = int(ratio / (jump + 0.0000001))

	a = colors[gap_num]
	b = colors[gap_num + 1]

	ratio = (ratio - gap_num * jump) * (len(colors) - 1)

	r = a[0] + (b[0] - a[0]) * ratio
	g = a[1] + (b[1] - a[1]) * ratio
	b = a[2] + (b[2] - a[2]) * ratio

	return '#%02x%02x%02x' % (r, g, b)


out_data = {
	'created': int(time.time()),
	'nodes': [],
	'edges': []
}

for n in G.iternodes():
	neighbor_ratio = len(G.neighbors(n)) / float(max_neighbors)

	pos = n.attr['pos'].split(',', 1)

	try:
		name = node_names[n.name]
	except:
		name = n.attr['label']

	out_data['nodes'].append({
		'id': n.name,
		'label': name,
		'version': n.attr['version'],
		'x': float(pos[0]),
		'y': float(pos[1]),
		# 'color': gradient_color(neighbor_ratio, [(255,60,20), (23,255,84), (41,187,255)]),
		'color': gradient_color(neighbor_ratio, [(100, 100, 100), (0, 0, 0)]),
		# 'color': gradient_color(neighbor_ratio, [(255, 255, 255), (255, 0 ,255)]),
		'size': neighbor_ratio
	})

# '#29BBFF', '#17FF54', '#FFBD0F', '#FF3C14', '#590409'

for e in G.iteredges():
	out_data['edges'].append({
		'sourceID': e[0],
		'targetID': e[1]
	})

json_output = json.dumps(out_data)

f = open('web/static/graph.json', 'w')
f.write(json_output)
f.close()