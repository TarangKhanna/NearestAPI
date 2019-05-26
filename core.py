from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse
from json import dumps
from flask_jsonpify import jsonify
import urllib.request  

# fast edit distance library, implemented in c++
import editdistance

''' Ideas for word generation:
    1) leveistein automata, modify to find exact n away. Or use this to prune the search space. 
    2) graph representation, where weight of edge is edit distance - graph generation is expensive, calculation from there is cheaper. 
    What if input word is not in the given dictionary? Find closest word based on edit distance.
    3) range based, sort input accoridng to length. Proof of correctness: 
    4) brute force: for every word in dictionary, calculate edit distance. Terminate early if we got 'number' amount of words delta edit distance away from intput 'word'
'''

''' Assumptions for design:
    1) Global dictionary, uploading new dictionary will overrite previous dictionary.
    2) Assuming that case does not matter-convert dictionary and input word to lower case. 
    output will have same capitalization as in dictionary.
    3) Assuming finding nearest words (API 2), will be called more often than load dictionary (API 1). So, we can optimize design for API 2.
    4) Dictionary is not user specific, and is shared by all connections.
    5) Single threaded.
'''

''' Performance breakdown:
    According to the source code for the editdistance library that I am use (https://github.com/aflc/editdistance/blob/master/editdistance/_editdistance.cpp), 
    for the worst case input they use edit_distance_dp, which is the dynamic programming way to solve edit ditstance. Which has a time complexity and space complexity of
    O(m*n). Where m and n are the strings being compared. In the worst case the bruteNearestWord method will go over all dictionary words, lets say d. So our time complexiy would 
    be O(m*n*d).
'''

# Change to a better index, to improve performance. Trie for example or sort list on length.
# This is not thread safe. To handle multiple clients flask would do multi threading. Run single threaded or move to redis, database, etc.
DICTIONARY = []

app = Flask(__name__)
api = Api(app)

# since there is only one global dictionary 
# brute force nearest
def bruteNearestWord(inputWord, delta, number):
    abort_if_no_dictionary()
    
    inputWord = inputWord.lower()

    print(len(DICTIONARY))

    nearest = []
    count = 0
    for word in DICTIONARY:
        if count == number:
            break

        dist = editdistance.eval(inputWord)
        if dist == delta:
            nearest.append(word)
            count += 1
        
    return nearest

def abort_if_no_dictionary():
    if len(DICTIONARY) == 0:
        abort(404, message="Dictionary not provided. Use /dictionary with dictionary_url in your query. Then retry this endpoint.")

# preprocess and then update
def updateDictionary(newDict):
    global DICTIONARY
    DICTIONARY = [word.lower() for word in newDict]

# API 1: Takes in a link for the dictionary file and loads it into the memory. 
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
        
        updateDictionary(data)

        response = jsonify({'loaded_dictionary_url': dict_url})
        response.status_code = 200 
        return response

# API 2: Takes in 3 parameters: word, delta, and number to generate a list of response words. 
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
     app.run(port='7777') # can add threaded=True, to enable handling parallel requests. For now we disable it (due to global dictionary).