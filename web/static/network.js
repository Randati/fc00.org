"use strict";

var nodes = [];
var edges = [];
var canvas = null;
var ctx = null;
var mapOffset = {x: 0, y: 0};
var zoom = 1.0;

function changeHash(hash) {
	window.location.replace(('' + window.location).split('#')[0] + '#' + hash);
}

function updateCanvasSize() {
	$(canvas).attr({height: $(canvas).height(), width: $(canvas).width()});
	ctx.translate(mapOffset.x, mapOffset.y);
}

function drawCircle(ctx, x, y, radius, color) {
	ctx.fillStyle = color;
	ctx.beginPath();
	ctx.arc(x, y, radius, 0, Math.PI*2, true);
	ctx.fill();
}

function drawLine(ctx, x1, y1, x2, y2, color) {
	ctx.strokeStyle = color;
	ctx.beginPath();
	ctx.moveTo(x1, y1);
	ctx.lineTo(x2, y2);
	ctx.closePath();
	ctx.stroke();
}

function drawText(ctx, x, y, text, color, font) {
	// ctx.save();
	// ctx.translate(x, y);
	// ctx.rotate(Math.PI/4);
	ctx.fillStyle = color;
	ctx.font = font;
	ctx.textAlign = 'center';
	ctx.fillText(text, x, y);
	// ctx.restore();
}

function drawNetwork() {
	ctx.save();
	ctx.resetTransform();
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	ctx.restore();


	// Draw edges
	for (var i = 0; i < edges.length; ++i) {
		var edge = edges[i];
		var highlight = edge.sourceNode.hover || edge.targetNode.hover;
		var color = highlight ? 'rgba(0, 0, 0, 0.5)' : 'rgba(0, 0, 0, 0.15)';
		
		drawLine(ctx,
			edge.sourceNode.x, edge.sourceNode.y,
			edge.targetNode.x, edge.targetNode.y,
			color);
	}

	// Draw nodes
	for (var i = 0; i < nodes.length; ++i) {
		var node = nodes[i];

		drawCircle(ctx, node.x, node.y, node.radius, node.color);
	}

	// Draw labels
	for (var i = 0; i < nodes.length; ++i) {
		var node = nodes[i];

		if (node.radius > 2 || node.selected || node.hover) {
			var fontSize = 4 + node.radius * 0.4;

			drawText(ctx, node.x, node.y - node.radius - 1,
				node.label, node.textColor, fontSize + 'pt "ubuntu mono"');
		}
	}
}

function getNodeAt(x, y) {
	x -= mapOffset.x;
	y -= mapOffset.y;
	for (var i = nodes.length - 1; i >= 0; --i) {
		var node = nodes[i];
		var distPow2 = (node.x - x) * (node.x - x) + (node.y - y) * (node.y - y);

		if (distPow2 <= node.radius * node.radius) {
			return node;
		}
	}
	return null;
}

function searchNode(id) {
	for (var i = 0; i < nodes.length; ++i) {
		if (nodes[i].id == id)
			return nodes[i];
	}
	return null;
}

function clearNodes() {
	changeHash('');
	$('#node-info').html('');

	for (var i = 0; i < nodes.length; ++i) {
		var node = nodes[i];
		node.depth = 0xFFFF;
		node.color = node.originalColor;
		node.textColor = node.color;
		node.selected = false;
	}
}

function selectNode(node, redraw) {
	clearNodes();

	changeHash(node.id);

	node.selected = true;
	showNodeInfo(node);

	markPeers(node, 0);
	if (redraw)
		drawNetwork();
}

function markPeers(node, depth) {
	node.depth = depth;

	// var colors = ['#000000', '#333333', '#555555', '#777777', '#999999', '#BBBBBB', '#DDDDDD'];
	// var colors = ['#000000', '#29BBFF', '#09E844', '#FFBD0F', '#FF5E14', '#FF3C14', '#FF7357', '#FF9782', '#FFC8BD', '#FFE6E0'];
	var colors = ['#000000', '#096EE8', '#09E8B8', '#36E809', '#ADE809', '#E8B809', '#E87509', '#E83A09'];
	var txtCol = ['#000000', '#032247', '#034537', '#0E3D02', '#354703', '#403203', '#3D1F02', '#3B0E02'];
	// var colors = ['#000000', '#064F8F', '#068F81', '#068F38', '#218F06', '#6F8F06', '#8F7806', '#8F5106'];
	// var colors = ['#FFFFFF', '#29BBFF', '#17FF54', '#FFBD0F', '#FF3C14', '#590409'];
	node.color = (depth >= colors.length) ? '#FFFFFF' : colors[depth];
	node.textColor = (depth >= txtCol.length) ? '#FFFFFF' : txtCol[depth];

	for (var i = 0; i < node.peers.length; ++i) {
		var n = node.peers[i];
		if (n.depth > depth + 1)
			markPeers(n, depth + 1);
	}
}

function showNodeInfo(node) {
	var ip_peers = [];
	var dns_peers = [];

	for (var i = 0; i < node.peers.length; ++i) {
		var n = node.peers[i];
		if (/^[0-9A-F]{4}$/i.test(n.label))
			ip_peers.push(n);
		else
			dns_peers.push(n);
	}

	var label_compare = function(a, b) {
		return a.label.localeCompare(b.label);
	}

	dns_peers.sort(label_compare);
	ip_peers.sort(label_compare);

	var peers = dns_peers.concat(ip_peers);

	var html =
		'<h2>' + node.label + '</h2>' +
		'<span class="tt">' + node.id + '</span><br>' +
		'<br>' +
		'<strong>Version:</strong> ' + node.version + '<br>' +
		'<strong>Location:</strong> Helsinki, Finland<br>' +
		'<strong>Peers:</strong> ' + node.peers.length + '<br>' +
		'<table>' +
		// '<tr><td></td><td><strong>Their peers #</strong></td></tr>' +
		peers.map(function (n) {
			return '<tr>' +
				'<td><a href="#' + n.id + '" class="tt">' + n.label + '</a></td>' +
				'<td>' + n.peers.length + '</td></tr>';
		}).join('') +
		'</table>';

	$('#node-info').html(html);
}

function mousePos(e) {
	var rect = canvas.getBoundingClientRect();
	return {x: e.clientX - rect.left, y: e.clientY - rect.top};
}



$(document).ready(function() {
	canvas = document.getElementById('map');
	ctx = canvas.getContext('2d');
	updateCanvasSize();


	jQuery.getJSON('/static/graph.json', function(data) {
		nodes = data.nodes;
		edges = data.edges;

		// Calculate node radiuses
		for (var i = 0; i < nodes.length; ++i) {
			var node = nodes[i];
			node.x = node.x * 1.2;
			node.y = node.y * 1.2;
			node.radius = 4 + node.size * 10;
			node.hover = false;
			node.selected = false;
			node.edges = [];
			node.peers = [];
			node.depth = 0xFFFF;
			// node.color = '#000';
			node.originalColor = node.color;
			node.textColor = node.color;
		}

		// Find node references for edges
		for (var i = 0; i < edges.length; ++i) {
			var edge = edges[i];

			for (var n = 0; n < nodes.length; ++n) {
				if (nodes[n].id == edge.sourceID) {
					edge.sourceNode = nodes[n];
					// edge.sourceNode.edges.append(edge);
				}
				else if (nodes[n].id == edge.targetID)
					edge.targetNode = nodes[n];
			}

			edge.sourceNode.edges.push(edge);
			edge.targetNode.edges.push(edge);
			edge.sourceNode.peers.push(edge.targetNode);
			edge.targetNode.peers.push(edge.sourceNode);
		}



		// Set update time
		var delta = Math.round(new Date().getTime() / 1000) - data.created;
		var min = Math.floor(delta / 60);
		var sec = delta % 60;
		$('#update-time').text(min + ' min, ' + sec + ' s ago');

		// Set stats
		$('#number-of-nodes').text(nodes.length);
		$('#number-of-connections').text(edges.length);


		if (window.location.hash) {
			var id = window.location.hash.substring(1);
			var node = searchNode(id);
			if (node) selectNode(node, false);
		}

		drawNetwork();

		$(window).resize(function() {
			updateCanvasSize();
			drawNetwork();
		});


		// Initialize search
		var searchArray = [];
		for (var i = 0; i < nodes.length; ++i) {
			var node = nodes[i];

			searchArray.push({
				value: node.label,
				data: node
			});

			searchArray.push({
				value: node.id,
				data: node
			});
		}

		$('#search-box').autocomplete({
			lookup: searchArray,
			autoSelectFirst: true,
			lookupLimit: 7,
			onSelect: function(suggestion) {
				selectNode(suggestion.data, true);
			}
		});

		$('#search-box').keypress(function(e) {
			if (e.which == 13) {
				selectNode(searchNode($('#search-box').val()), true);
			}
		});

		$(document).on('click', '#node-info a', function(e) {
			var id = e.target.hash.substring(1);
			selectNode(searchNode(id), true);
		});


	});



	var mouseDownPos = null;
	var mouseLastPos = null;
	var mouseDownNode = null;
	var mouseHoverNode = null;


	$(canvas).mousemove(function(e) {
		var mouse = mousePos(e);

		// Dragging
		if (mouseDownPos != null) {
			$('body').css('cursor', 'move');
			var dx = mouse.x - mouseLastPos.x;
			var dy = mouse.y - mouseLastPos.y;
			mapOffset.x += dx;
			mapOffset.y += dy;
			ctx.translate(dx, dy);
			mouseLastPos = {x: mouse.x, y: mouse.y};
			drawNetwork();
		}
		// Hovering
		else {
			var node = getNodeAt(mouse.x, mouse.y);

			if (node == mouseHoverNode)
				return;

			if (node == null) {
				nodeMouseOut(mouseHoverNode);
			}
			else {
				if (mouseHoverNode != null)
					nodeMouseOut(mouseHoverNode);

				nodeMouseIn(node);
			}
			mouseHoverNode = node;

			drawNetwork();
		}
	});


	$(canvas).mousedown(function(e) {
		var mouse = mousePos(e);
		mouseLastPos = mouseDownPos = {x: mouse.x, y: mouse.y};
		mouseDownNode = getNodeAt(mouse.x, mouse.y);
		return false;
	});

	$(canvas).mouseup(function(e) {
		var mouse = mousePos(e);
		var mouseMoved =
			Math.abs(mouse.x - mouseDownPos.x) + 
			Math.abs(mouse.y - mouseDownPos.y) > 3

		if (!mouseMoved) {
			if (mouseDownNode)
				selectNode(mouseDownNode, true);
			else {
				clearNodes();
				drawNetwork();
			}
		}
		else {
			$('body').css('cursor', 'auto');
		}

		mouseDownPos = null;
		mouseDownNode = null;
		return false;
	});


	function handleScroll(e) {
		var mouse = mousePos(e);
		var e = window.event;
		var delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));

		var ratio = (delta < 0) ? (3 / 4) :  1 + (1 / 3);
		var mx = mouse.x - mapOffset.x;
		var my = mouse.y - mapOffset.y;

		zoom *= ratio;

		for (var i = 0; i < nodes.length; ++i) {
			var node = nodes[i];
			node.x = (node.x - mx) * ratio + mx;
			node.y = (node.y - my) * ratio + my;
			// node.x *= ratio;
			// node.y *= ratio;
			// node.radius *= ratio;
			node.radius = (4 + node.size * 8) * zoom;
		}

		drawNetwork();
	}
	canvas.addEventListener("mousewheel", handleScroll, false);
	canvas.addEventListener("DOMMouseScroll", handleScroll, false);

});

function nodeMouseIn(node) {
	node.hover = true;
	$('body').css('cursor', 'pointer');
}

function nodeMouseOut(node) {
	node.hover = false;
	$('body').css('cursor', 'auto');
}