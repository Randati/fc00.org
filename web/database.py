import MySQLdb as mdb
from graph import Node, Edge
import time


class NodeDB:
	def __init__(self, config):
		self.con = mdb.connect(
			config['MYSQL_DATABASE_HOST'],
			config['MYSQL_DATABASE_USER'],
			config['MYSQL_DATABASE_PASSWORD'],
			config['MYSQL_DATABASE_DB'])
		self.cur = self.con.cursor()

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.con.commit()
		self.con.close()



	def insert_node(self, node):
		now = int(time.time())
		self.cur.execute('''
			INSERT INTO nodes (ip, name, version, first_seen, last_seen)
			VALUES (%s, %s, %s, %s, %s)
			ON DUPLICATE KEY
			UPDATE name = %s, version = %s, last_seen = %s''', (
			node.ip, node.label, node.version, now, now,
			node.label, node.version, now))

	def insert_edge(self, edge):
		now = int(time.time())
		self.cur.execute('''
			INSERT INTO edges (a, b, first_seen, last_seen)
			VALUES (%s, %s, %s, %s)
			ON DUPLICATE KEY
			UPDATE last_seen = %s''', (
			edge.a.ip, edge.b.ip, now, now,
			now))

	def insert_graph(self, nodes, edges):
		for n in nodes.itervalues():
			self.insert_node(n)

		for e in edges:
			self.insert_edge(e)



	def get_nodes(self, time_limit):
		since = int(time.time() - time_limit)
		cur = self.con.cursor(mdb.cursors.DictCursor)
		cur.execute("SELECT ip, version, name FROM nodes WHERE last_seen > %s", (since,))
		db_nodes = cur.fetchall()

		nodes = dict()
		for n in db_nodes:
			nodes[n['ip']] = Node(n['ip'], n['version'], n['name'])

		return nodes

	def get_edges(self, nodes, time_limit):
		since = int(time.time() - time_limit)
		cur = self.con.cursor(mdb.cursors.DictCursor)
		cur.execute("SELECT a, b FROM edges WHERE last_seen > %s", (since,))
		db_edges = cur.fetchall()

		edges = []
		for e in db_edges:
			edges.append(Edge(nodes[e['a']], nodes[e['b']]))

		return edges

	def get_graph(self, time_limit):
		nodes = self.get_nodes(time_limit)
		edges = self.get_edges(nodes, time_limit)
		return (nodes, edges)
