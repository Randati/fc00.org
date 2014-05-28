import json

def insert_graph_data(json_str):
	try:
		graph_data = json.loads(json_str)
	except ValueError:
		return False

	return True
