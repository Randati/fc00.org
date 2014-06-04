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

# otherwise these are used.
cjdns_ip         = '127.0.0.1'
cjdns_first_port = 11234
cjdns_password   = 'hunter2'
cjdns_processes  = 1   # This can be used if you are running multiple instances
                       # of cjdns with consecutive port numbers

###############################################################################



import sys
import urllib
import urllib2
from collections import deque
import traceback
import json
sys.path.append(cjdns_path + '/contrib/python/cjdnsadmin/')
import cjdnsadmin
import adminTools



def main():
	all_nodes = dict()
	all_edges = []

	for process in range(0, 1 if cjdns_use_default else cjdns_processes):
		print 'Connecting port %d...' % (cjdns_first_port + process),; sys.stdout.flush()

		try:
			cjdns = cjdns_connect(process)
			print adminTools.whoami(cjdns)['IP']

			nodes, edges = generate_graph(cjdns)

			# Merge results
			all_nodes.update(nodes)
			for e in edges:
				if not e in all_edges:
					all_edges.append(e)
		except Exception, err:
			print 'Failed!'
			print traceback.format_exc()

	success = send_graph(all_nodes, all_edges)
	sys.exit(0 if success else 1)


def generate_graph(cjdns):
	source_nodes = cjdns_get_node_store(cjdns)
	print '  Found %d source nodes.' % len(source_nodes)

	nodes, edges = cjdns_graph_from_nodes(cjdns, source_nodes)
	print '  Found %d nodes and %d links.' % (len(nodes), len(edges))

	return (nodes, edges)

def send_graph(nodes, edges):
	graph_data = {
		'nodes': [],
		'edges': []
	}

	for n in nodes.values():
		graph_data['nodes'].append({
			'ip':      n.ip,
			'version': n.version
		})
	
	for e in edges:
		graph_data['edges'].append({
			'a': e.a.ip,
			'b': e.b.ip
		})

	json_str = json.dumps(graph_data)

	print 'Sending data...',; sys.stdout.flush()
	answer = send_data(json_str)
	success = answer == 'OK'
	print ('Done!' if success else answer)

	return success


class Node:
	def __init__(self, ip, version=None):
		self.ip = ip
		self.version = version

	def __lt__(self, b):
		return self.ip < b.ip


class Edge:
	def __init__(self, a, b):
		self.a, self.b = sorted([a, b])

	def __eq__(self, that):
		return self.a.ip == that.a.ip and self.b.ip == that.b.ip



def cjdns_connect(process=0):
	if cjdns_use_default:
		return cjdnsadmin.connectWithAdminInfo()
	else:
		return cjdnsadmin.connect(cjdns_ip, cjdns_first_port + process, cjdns_password)

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
				if not e in edges:
					edges.append(e)

	return (nodes, edges)



def send_data(graph_data):
	post_data = urllib.urlencode({'data': graph_data})
	req = urllib2.Request(url, post_data)
	response = urllib2.urlopen(req)
	return response.read()



if __name__ == '__main__':
	main()
