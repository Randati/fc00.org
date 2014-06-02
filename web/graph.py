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

	def __eq__(self, that):
		return self.a.ip == that.a.ip and self.b.ip == that.b.ip

	def __repr__(self):
		return 'Edge(a.ip="%s", b.ip="%s")' % (
			self.a.ip,
			self.b.ip)
