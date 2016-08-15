from flask import Flask, jsonify, make_response, request, url_for, abort
app = Flask(__name__)

stuff = [
    {
        'id': 1,
        'name': u'Test Name',
        'size': 100
    },
    {
        'id': 2,
        'name': u'Test Name2',
        'size': 200
    }
]

def make_public_thing(thing):
    new_thing = {}
    for field in thing:
        if field == 'id':
            new_thing['uri'] = url_for('get_stuff', thing_id=thing['id'], _external=True)
        else:
            new_thing[field] = thing[field]
    return new_thing


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_request(jsonify({'error': error}), 400)

@app.route('/PDFServer/api/v1.0/stuff', methods=['GET'])
def get_stuff():
    return jsonify({'stuff': [make_public_thing(thing) for thing in stuff]})

@app.route('/PDFServer/api/v1.0/stuff/<int:stuff_id>', methods=['GET'])
def get_thing(stuff_id):
    thing = [thing for thing in stuff if thing['id'] == stuff_id]
    if len(thing) == 0:
        abort(404)
    return jsonify({'thing': make_public_thing(thing[0])})

@app.route('/PDFServer/api/v1.0/stuff', methods=['POST'])
def add_stuff():
    if not request.json or not 'name' in request.json:
        abort(400)
    thing = {
        'id': stuff[-1]['id'] + 1,
        'name': request.json['name'],
        'size': request.json.get('size', 0)
    }
    stuff.append(thing)
    return jsonify({'thing': make_public_thing(thing)}), 201

@app.route('/PDFServer/api/v1.0/stuff/<int:stuff_id>', methods=['PUT'])
def update_stuff(stuff_id):
    thing = [thing for thing in stuff if thing['id'] == stuff_id]
    if len(thing) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'name' in request.json and type(request.json['name']) != unicode:
        abort(400)
    if 'size' in request.json and type(request.json['size']) is not int:
        abort(400)
    thing[0]['name'] = request.json.get('name', thing[0]['name'])
    thing[0]['size'] = request.json.get('size', thing[0]['size'])
    return jsonify({'thing': make_public_thing(thing[0])})

@app.route('/PDFServer/api/v1.0/stuff/<int:stuff_id>', methods=['DELETE'])
def delete_stuff(stuff_id):
    thing = [thing for thing in stuff if thing['id'] == stuff_id]
    if len(thing) == 0:
        abort(404)
    stuff.remove(thing[0])
    return jsonify({'result': True})

def build(serverData):
    serverData = serverData
    lab_abbrev = serverData['LAB_ABBREV']
    packages = serverData['TEST_PACKAGES']


@app.route('/PDFServer/api/v1.0/generate', methods=['POST'])
def generate_reports():
    if not request.json or not 'LAB_ABBREV' in request.json or not 'TEST_PACKAGES' in request.json:
        abort(400)
    serverData = request.json
    try:
        build(serverData)
        success = True
    except Exception as e:
        print e
        abort(400)
        
    

@app.route('/')
def hello_world():
    return 'Hello Worlds'

if __name__ == '__main__':
    app.run()
