class Node:
	def __init__(self, ip, version=None, label=None):
		self.ip = ip
		self.version = version
		self.label = ip[-4:] if label == None else label

	def __lt__(self, b):
		return self.ip < b.ip

	def __repr__(self):
		return 'Node(ip="%s", version=%s, label="%s")' % (
			self.ip,
			self.version,
			self.label)

class Edge:
	def __init__(self, a, b):
		self.a, self.b = sorted([a, b])

	def is_in(self, edges):
		for e in edges:
			if e.a.ip == self.a.ip and e.b.ip == self.b.ip:
					return True
		return False

	def __repr__(self):
		return 'Edge(a.ip="%s", b.ip="%s")' % (
			self.a.ip,
			self.b.ip)
