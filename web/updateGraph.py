#!/usr/bin/env python
from flask import Config
from database import NodeDB
import graphPlotter


def generate_graph(time_limit=60*60*3):
	nodes, edges = load_graph_from_db(time_limit)

	graph = graphPlotter.position_nodes(nodes, edges)
	json = graphPlotter.get_graph_json(graph)

	with open('static/graph.json', 'w') as f:
		f.write(json)


def load_graph_from_db(time_limit):
	config = Config('./')
	config.from_pyfile('web_config.cfg')

	with NodeDB(config) as db:
		return db.get_graph(time_limit)


if __name__ == '__main__':
	generate_graph()
