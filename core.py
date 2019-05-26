from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse
from json import dumps
from flask_jsonpify import jsonify
import urllib.request  

# fast edit distance library, implemented in c++
import editdistance

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
# 4) brute force: for every word in dictionary, calculate edit distance. Terminate early if we got 'number' amount of words delta edit distance away from intput 'word'

# assumptions for design:
# global dictionary, one at a time. Uploading new dictionary will overrite previous dictionary
# taking capitalization into account, treat everthing as lower car.
# output will have same capitalization as in dictionary.

# performance breakdowns:

DICTIONARY = []

# since there is only one global dictionary 
# brute force nearest
def bruteNearestWord(inputWord, delta, number):
    inputWord = inputWord.lower()
    print (inputWord)
    print (delta)
    print (number)
    print(len(DICTIONARY))

    # abort_if_no_dictionary()
    # print(editdistance.eval("Car".lower(), "CARE".lower()))

    nearest = []
    count = 0
    for word in DICTIONARY:
        if count == number:
            break

        dist = editdistance.eval(inputWord, word.lower())
        if dist == delta:
            nearest.append(word)
            count += 1
        
    return nearest

def abort_if_no_dictionary():
    if len(DICTIONARY) == 0:
        abort(404, message="Dictionary doesn't exist")

class LoadDictionary(Resource):
    # security concern, getting data from random link
    def post(self):
        global DICTIONARY
        parser = reqparse.RequestParser()
        parser.add_argument("dictionary_url")
        args = parser.parse_args()

        dict_url = args["dictionary_url"]
        data = urllib.request.urlopen(dict_url).read().decode('utf-8')
        data = data.split("\n")
        # for line in data[:10]: 
        #     print (line)
        
        # preprocess before adding, such as make lower case
        DICTIONARY = data
        # print(data[:10])
        # print(DICTIONARY[:10])
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
        
        nearest = bruteNearestWord(word, int(delta), int(number))

        response = jsonify({'list_of_words': nearest})
        response.status_code = 200 
        return response

# Api resource routing
api.add_resource(LoadDictionary, '/dictionary')
api.add_resource(NearestWord, '/nearestWord')

if __name__ == '__main__':
     app.run(port='7777')