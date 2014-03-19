from flask import Flask, render_template, request
from flaskext.mysql import MySQL
import MySQLdb
from pprint import pprint


app = Flask(__name__)
app.debug = True
app.config['MYSQL_DATABASE_HOST']     = 'localhost'
app.config['MYSQL_DATABASE_PORT']     = 3306
app.config['MYSQL_DATABASE_USER']     = 'fc00'
app.config['MYSQL_DATABASE_PASSWORD'] = 'A54RZ8FN9CtgIdPWmVIgp3sKgm1uSNVlVtPGipOHsalMZ9DNEUTeOijNcZRpLCn1'
app.config['MYSQL_DATABASE_DB']       = 'fc00'
app.config['MYSQL_DATABASE_CHARSET']  = 'utf8'

mysql = MySQL()
mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor(MySQLdb.cursors.DictCursor)


@app.context_processor
def add_ip():
	return dict(ip=request.environ['REMOTE_ADDR'])



@app.route('/')
@app.route('/network')
def page_network():
	return render_template('network.html')

@app.route('/world-map')
def page_world_map():
	cursor.execute('SELECT ip, ipv4, ipv6, domain, CONVERT(longitude, CHAR(16)) as longitude, CONVERT(latitude, CHAR(16)) as latitude FROM nodes')
	nodes = cursor.fetchall()
	return render_template('world-map.html', nodes=nodes)

@app.route('/tools')
def page_tools():
	return render_template('tools.html')

@app.route('/test')
def asd():
	pprint(vars(request))
	return 'Asd'


if __name__ == '__main__':
	app.run(host='::')
