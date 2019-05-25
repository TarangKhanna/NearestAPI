from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse
from json import dumps
from flask_jsonpify import jsonify

app = Flask(__name__)
api = Api(app)

# API 1: Takes in a link for the dictionary file and loads it into the memory. 
# API 2: Takes in 3 parameters: word, delta, and number to generate a list of response words. 

# if file to keep in memory is bigger than current ~ 5 mb, I would use an in memory database,
# for this case, just loading the url into a global variable will work

DICTIONARY = {}

def abort_if_no_dictionary():
    if len(DICTIONARY) == 0:
        abort(404, message="Dictionary doesn't exist")

class LoadDictionary(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("dictionary_url")
        args = parser.parse_args()

        # DICTIONARY = args["dictionary_url"]

        response = jsonify({'loaded_dictionary_url': args["dictionary_url"]})
        response.status_code = 200 
        return response

# Api resource routing
api.add_resource(LoadDictionary, '/dictionary')

if __name__ == '__main__':
     app.run(port='7777')