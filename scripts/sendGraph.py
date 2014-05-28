#!/usr/bin/env python2

###############################################################################
# CONFIG

# URL where data is sent
#    www.fc00.org                              for clearnet access
#    fc00.org                                  for hyperboria
#    [fcc7:5feb:2c76:53d0:f954:9768:1008:fc00] for DNS-less access
url = 'http://www.fc00.org/sendGraph'

# Cjdns path without trailing slash
cjdns_path = '/home/user/cjdns'


# ----------------------
# RPC connection details
# ----------------------

# If this is set to True connection details will be loaded from ~/.cjdnsadmin
cjdns_use_default = True

# otherwise these are used
cjdns_ip       = '127.0.0.1'
cjdns_port     = 11234
cjdns_password = 'hunter2'

###############################################################################



import sys
import urllib
import urllib2
from collections import deque
import json
sys.path.append(cjdns_path + '/contrib/python/cjdnsadmin/')
import cjdnsadmin



def main():
	cjdns = cjdns_connect()
	success = generate_and_send_graph(cjdns)
	sys.exit(0 if success else 1)

def generate_and_send_graph(cjdns):
	source_nodes = cjdns_get_node_store(cjdns)
	nodes, edges = cjdns_graph_from_nodes(cjdns, source_nodes)

	graph_data = {
		'nodes': [],
		'edges': []
	}

	for n in nodes.values():
		graph_data['nodes'].append({
			'ip':      n.ip,
			'key':     n.key,
			'version': n.version
		})
	
	for e in edges:
		graph_data['edges'].append({
			'a': e.a.ip,
			'b': e.b.ip
		})

	json_str = json.dumps(graph_data)
	return send_data(json_str)



class Node:
	def __init__(self, ip, version=None, key=None):
		self.ip = ip
		self.version = version
		self.key = key

class Edge:
	def __init__(self, a, b):
		self.a, self.b = sorted([a, b])

	def is_in(self, edges):
		for e in edges:
			if e.a.ip == self.a.ip and e.b.ip == self.b.ip:
				return True
		return False



def cjdns_connect():
	if cjdns_use_default:
		return cjdnsadmin.connectWithAdminInfo()
	else:
		return cjdnsadmin.connect(cjdns_ip, cjdns_port, cjdns_password)

def cjdns_get_node_store(cjdns):
	nodes = dict()

	i = 0
	while True:
		res = cjdns.NodeStore_dumpTable(i)

		if not 'routingTable' in res:
			break

		for n in res['routingTable']:
			if not 'ip' in n:
				continue

			ip = n['ip']
			version = None

			if 'version' in n:
				version = n['version']

			nodes[ip] = Node(ip, version)

		if not 'more' in res or res['more'] != 1:
			break

		i += 1

	return nodes

def cjdns_graph_from_nodes(cjdns, source_nodes):
	nodes_to_check = deque(source_nodes.values())

	nodes = source_nodes.copy()
	edges = []

	while len(nodes_to_check) > 0:
		node = nodes_to_check.pop()
		nodes[node.ip] = node

		resp = cjdns.NodeStore_nodeForAddr(node.ip)

		if not 'result' in resp:
			continue
		res = resp['result']

		if 'key' in res:
			node.key = res['key']

		if 'protocolVersion' in res:
			node.version = res['protocolVersion']

		if 'linkCount' in res:
			for i in range(0, int(res['linkCount'])):
				resp = cjdns.NodeStore_getLink(node.ip, i)
				if not 'result' in resp:
					continue

				res = resp['result']
				if not 'child' in res or not 'isOneHop' in res or res['isOneHop'] != 1:
					continue

				# Add node
				child_ip = res['child']
				if not child_ip in nodes:
					n = Node(child_ip)
					nodes[child_ip] = n
					nodes_to_check.append(n)

				# Add edge
				e = Edge(nodes[node.ip], nodes[child_ip])
				if not e.is_in(edges):
					edges.append(e)

	return (nodes, edges)



def send_data(graph_data):
	post_data = urllib.urlencode({'data': graph_data})
	req = urllib2.Request(url, post_data)
	response = urllib2.urlopen(req)
	output = response.read()
	return output == 'OK'



if __name__ == "__main__":
	main()
