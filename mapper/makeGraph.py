#!/usr/bin/env python

import conf_sh as conf
import sys
sys.path.append(conf.cjdns_path + '/contrib/python/cjdnsadmin/')
import adminTools as admin
from collections import deque
import pygraphviz as pgv
import json
import time
import httplib2
import traceback


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

	def is_in(self, edges):
		for e in edges:
			if e.a.ip == self.a.ip and e.b.ip == self.b.ip:
					return True
		return False



def get_network_from_cjdns(ip, port, password):
	nodes = dict()
	edges = []

	cjdns = admin.connect(ip, port, password)
	me = admin.whoami(cjdns)
	my_ip = me['IP']
	nodes[my_ip] = Node(my_ip)

	nodes_to_check = deque()
	nodes_to_check.append(my_ip)

	while len(nodes_to_check) != 0:
		current_ip = nodes_to_check.popleft()
		resp = cjdns.NodeStore_nodeForAddr(current_ip)

		if not 'result' in resp or not 'linkCount' in resp['result']:
			continue

		result = resp['result']
		link_count = result['linkCount']
		
		if 'protocolVersion' in result:
			nodes[current_ip].version = result['protocolVersion']


		for i in range(0, link_count):
			result = cjdns.NodeStore_getLink(current_ip, i)['result']
			if not 'child' in result:
				continue

			child_ip = result['child']

			# Add links with one hop only
			if result['isOneHop'] != 1:
				continue

			# Add node
			if not child_ip in nodes:
				nodes[child_ip] = Node(child_ip)
				nodes_to_check.append(child_ip)

			# Add edge
			e = Edge(nodes[current_ip], nodes[child_ip])
			if not e.is_in(edges):
				edges.append(e)

	return (nodes, edges)


def get_full_network():
	all_nodes = dict()
	all_edges = []

	for i in range(0, conf.num_of_nodes):
		port = conf.rpc_firstport + i

		print '[%d/%d] Connecting to %s:%d...' % (i + 1, conf.num_of_nodes, conf.rpc_connect, port),
		sys.stdout.flush()

		try:
			nodes, edges = get_network_from_cjdns(conf.rpc_connect, port, conf.rpc_pw)
		except Exception as ex:
			print 'Fail!'
			print traceback.format_exc()
			continue

		print '%d nodes, %d edges' % (len(nodes), len(edges))

		for ip, n in nodes.iteritems():
			all_nodes[ip] = n

		for e in edges:
			if not e.is_in(all_edges):
				all_edges.append(e)

	return (all_nodes, all_edges)





def download_names_from_nameinfo():
	page = 'http://[fc5d:baa5:61fc:6ffd:9554:67f0:e290:7535]/nodes/list.json'
	print 'Downloading names from Mikey\'s nodelist...',

	ip_dict = dict()
	http = httplib2.Http('.cache', timeout=15.0)
	r, content = http.request(page, 'GET')
	name_and_ip = json.loads(content)['nodes']

	for node in name_and_ip:
		ip_dict[node['ip']] = node['name']

	print 'Done!'
	return ip_dict



def set_node_names(nodes):
	try:
		ip_dict = download_names_from_nameinfo()
	except Exception as ex:
		print 'Fail!'
		# TODO use cache
		print traceback.format_exc()
		return

	for ip, node in nodes.iteritems():
		if ip in ip_dict:
			node.label = ip_dict[ip]




def build_graph(nodes, edges):
	G = pgv.AGraph(strict=True, directed=False, size='10!')

	for n in nodes.values():
		G.add_node(n.ip, label=n.label, version=n.version)

	for e in edges:
		G.add_edge(e.a.ip, e.b.ip, len=1.0)

	G.layout(prog='neato', args='-Gepsilon=0.0001 -Gmaxiter=100000')

	return G



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


def get_graph_json(G):
	max_neighbors = 1
	for n in G.iternodes():
		neighbors = len(G.neighbors(n))
		if neighbors > max_neighbors:
			max_neighbors = neighbors
	print 'Max neighbors: %d' % max_neighbors

	out_data = {
		'created': int(time.time()),
		'nodes': [],
		'edges': []
	}

	for n in G.iternodes():
		neighbor_ratio = len(G.neighbors(n)) / float(max_neighbors)
		pos = n.attr['pos'].split(',', 1)

		out_data['nodes'].append({
			'id': n.name,
			'label': n.attr['label'],
			'version': n.attr['version'],
			'x': float(pos[0]),
			'y': float(pos[1]),
			'color': gradient_color(neighbor_ratio, [(100, 100, 100), (0, 0, 0)]),
			'size': neighbor_ratio
		})

	for e in G.iteredges():
		out_data['edges'].append({
			'sourceID': e[0],
			'targetID': e[1]
		})

	return json.dumps(out_data)




if __name__ == '__main__':
	nodes, edges = get_full_network()
	print 'Total:'
	print '%d nodes, %d edges' % (len(nodes), len(edges))
	
	set_node_names(nodes)
	G = build_graph(nodes, edges)
	output = get_graph_json(G)

	with open(conf.graph_output, 'w') as f:
		f.write(output)
