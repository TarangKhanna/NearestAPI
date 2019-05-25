from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse
from json import dumps
from flask_jsonpify import jsonify
import urllib.request  

app = Flask(__name__)
api = Api(app)

# API 1: Takes in a link for the dictionary file and loads it into the memory. 
# API 2: Takes in 3 parameters: word, delta, and number to generate a list of response words. 

# if file to keep in memory is bigger than current ~ 5 mb, I would use an in memory database,
# for this case, just loading the url into a global variable will work

# ideas for word generation:
# 1) leveistein automata, modify to find exact n away
# 2) graph representation, where weight of edge is edit distance - graph generation is expensive, calculation from there is cheaper. 
# What if input word is not in the given dictionary? Find closest word based on edit distance.
# 3) range based, sort input accoridng to length. Proof of correctness: 

# assumptions for design:


DICTIONARY = []

def abort_if_no_dictionary():
    if len(DICTIONARY) == 0:
        abort(404, message="Dictionary doesn't exist")

class LoadDictionary(Resource):
    # security concern, getting data from random link
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("dictionary_url")
        args = parser.parse_args()

        dict_url = args["dictionary_url"]
        data = urllib.request.urlopen(dict_url).read().decode('utf-8')
        data = data.split("\n")
        # for line in data[:10]: 
        #     print (line)

        DICTIONARY = data

        response = jsonify({'loaded_dictionary_url': dict_url})
        response.status_code = 200 
        return response

class NearestWord(Resource):
    # security concern, getting data from random link
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("word")
        parser.add_argument("delta")
        parser.add_argument("number")
        args = parser.parse_args()

        word = args["word"]
        delta = args["delta"]
        number = args["number"]

        print (word)
        print (delta)
        print (number)
        print([word])
        response = jsonify({'list_of_words': [word, word]})
        response.status_code = 200 
        return response

# Api resource routing
api.add_resource(LoadDictionary, '/dictionary')
api.add_resource(NearestWord, '/nearestWord')

if __name__ == '__main__':
     app.run(port='7777')