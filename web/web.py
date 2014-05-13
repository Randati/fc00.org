from flask import Flask, render_template, request

app = Flask(__name__)
app.debug = False


@app.context_processor
def add_ip():
	return dict(ip=request.environ['REMOTE_ADDR'])


@app.route('/')
@app.route('/network')
def page_network():
	return render_template('network.html', page='network')

@app.route('/about')
def page_about():
	return render_template('about.html', page='about')


if __name__ == '__main__':
	app.run(host='::')
