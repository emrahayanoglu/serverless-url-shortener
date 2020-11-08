from flask import Flask, render_template, request, jsonify, redirect
from flask_redis import FlaskRedis
import utils
import validators
import os


app = Flask(__name__)
app.config['REDIS_URL'] = os.environ.get('REDIS_URL')
redis_client = FlaskRedis(app)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', unique_token=utils.generate_form_hash(redis_client))


@app.route('/<hash>', methods=['GET'])
def redirect_to_url(hash):
    found_url = utils.check_url_exists(redis_client, hash)
    if found_url is not None:
        utils.increment_view_counter(redis_client, hash)
        return redirect(found_url, code=302)
    return render_template('error.html', title='Param from Flask!')


@app.route('/management/create', methods=['POST'])
def create_hash():
    url_param = request.get_json().get('url', None)
    if url_param is not None:
        if validators.url(url_param):
            found_hash = utils.check_url_exists(redis_client, url_param)
            if found_hash is not None:
                return jsonify({'result': True, 'hash': found_hash})
            hash = utils.convert_to_hash(utils.get_and_increment_index(redis_client))
            utils.set_hash(redis_client, hash, url_param)
            return jsonify({'result': True, 'short_url': 'https://minurl.xyz/{}'.format(hash)})
    return jsonify({'result': False})


@app.route('/management/stats/<hash>', methods=['GET'])
def show_statistics(hash):
    found_url = utils.check_url_exists(redis_client, hash)
    if found_url is None:
        return jsonify({'error': 'Hash Not Found', 'result': True})

    stats = utils.get_statistics_for_link(redis_client, hash, found_url)

    return jsonify(stats)
