from flask import Flask, request
from flask_restful import Resource, Api, abort, reqparse
from json import dumps
from flask_jsonpify import jsonify
import urllib.request  

# fast edit distance library, implemented in c++ for speed.
import editdistance # used for brute force solution

''' Ideas for word generation:
    1) leveistein automata, modify to find exact n away. Or use this to prune the search space. 
    2) graph representation, where weight of edge is edit distance - graph generation is expensive, calculation from there is cheaper. 
    What if input word is not in the given dictionary? Find closest word based on edit distance.
    3) range based, sort input accoridng to length. Proof of correctness: 
    4) brute force: for every word in dictionary, calculate edit distance. Terminate early if we got 'number' amount of words delta edit distance away from intput 'word'
    5) Use brute force to test correctness of improved solution
'''

''' Assumptions for design:
    1) Global dictionary, uploading new dictionary will overrite previous dictionary.
    2) Assuming that case does not matter-convert dictionary and input word to lower case. 
    3) Assuming finding nearest words (API 2), will be called more often than load dictionary (API 1). So, we can optimize design for API 2.
    4) Dictionary/trie is not user specific, and is shared by all connections.
    5) Single threaded.
    6) If we can not find enough number of words exactly delta away from input word, API 2 returns how many ever possible, with a flag (found_number_words) to indicate if it found required matches (true if it did).
    7) nearest words returned are in alphabetical ordering
'''

''' Performance breakdown:
    Brute force solution: According to the source code for the editdistance library that I am use (https://github.com/aflc/editdistance/blob/master/editdistance/_editdistance.cpp), 
    for the worst case input they use edit_distance_dp, which is the dynamic programming way to solve edit ditstance. Which has a time complexity and space complexity of
    O(m*n). Where m and n are the strings being compared. In the worst case the bruteNearestWord method will go over all dictionary words, lets say d. So our time complexiy would 
    be O(m*n*d), in the worst case O(d*(s)^2), where s is max length of word.

    Improved (current solution): Based on the dp solution of edit distance, we can see that the table that is built, can be reused for a word with the same prefix. \
    For example with car as the input, and comparing it with arc we create a levenshtein distance table, and when we compare car with arcs, we can reuse this table and simply
    fill in the last row.
    Using a trie to store our dictionary, all shared prefixes in the dictionary are collaped into a single path,
    so we can process them in the best order for building up the levenshtein tables one row at a time.
    The upper bound for the runtime is O(<max word length> * <number of nodes in the trie>). 
'''

# Modified improved solution is based on: http://stevehanov.ca/blog/index.php?id=114

# This is not thread safe. To handle multiple clients flask would do multi threading. Run single threaded or move to redis, database, etc.
# for brute force solution
# DICTIONARY = []

app = Flask(__name__)
api = Api(app)

class TrieNode:
    def __init__(self):
        self.word = None
        self.children = {}

    def insert(self, word):
        node = self
        for letter in word:
            if letter not in node.children: 
                node.children[letter] = TrieNode()

            node = node.children[letter]

        node.word = word

# This is not thread safe. To handle multiple clients flask would do multi threading. Run single threaded or move to redis, database, etc.
trie = TrieNode()
trieExists = False

def abort_if_no_trie():
    if not trieExists:
        abort(404, message="Dictionary not provided. Post to /dictionary with dictionary_url in your query. Then retry this endpoint.")
    
def search(word, maxCost, maxResults):
    abort_if_no_trie()
    word = word.lower()

    # build first row
    currentRow = range(len(word) + 1)

    results = []
    resultCount = [0] # to avoid len(results) cost, made a list since int is immutable in python

    # recursively search each branch of the trie
    for letter in trie.children:
        if searchRecursive(trie.children[letter], letter, word, currentRow, 
            results, maxCost, maxResults, resultCount):
            # terminate search if maxresults found
            return results
    
    return results

# This recursive helper is used by the search function above. It assumes that
# the previousRow has been filled in already.
# returns boolean, if true, then we have found the number of nearest words requested.
def searchRecursive(node, letter, word, previousRow, results, maxCost, maxResults, resultCount):
    columns = len(word) + 1
    currentRow = [previousRow[0] + 1]

    for column in range(1, columns):
        insertCost = currentRow[column - 1] + 1
        deleteCost = previousRow[column] + 1

        if word[column - 1] != letter:
            replaceCost = previousRow[column - 1] + 1
        else:                
            replaceCost = previousRow[column - 1]

        currentRow.append(min(insertCost, deleteCost, replaceCost))

    # if the last entry in the row indicates the optimal cost is equal to the
    # maximum cost, and there is a word in this trie node, then add it.
    if currentRow[-1] == maxCost and node.word != None:
        results.append(node.word)
        resultCount[0] += 1 # make sure to update this when appending to results

    if resultCount[0] == maxResults:
        return True

    # if any entries in the row are less than the maximum cost, then 
    # recursively search each branch of the trie
    if min(currentRow) <= maxCost:
        for letter in node.children:
            if searchRecursive(node.children[letter], letter, word, currentRow, 
                results, maxCost, maxResults, resultCount):
                return True

    return False

# brute force nearest
# def bruteNearestWord(inputWord, delta, number):
#     abort_if_no_dictionary()
    
#     inputWord = inputWord.lower()

#     print(len(DICTIONARY))

#     nearest = []
#     count = 0
#     for word in DICTIONARY:
#         if count == number:
#             break

#         dist = editdistance.eval(inputWord)
#         if dist == delta:
#             nearest.append(word)
#             count += 1
        
#     return nearest

# def abort_if_no_dictionary():
#     if len(DICTIONARY) == 0:
#         abort(404, message="Dictionary not provided. Use /dictionary with dictionary_url in your query. Then retry this endpoint.")

# preprocess and then update
def updateDictionary(newDict):
    # global DICTIONARY
    global trie
    global trieExists
    trieExists = True
    # reset on update
    trie = TrieNode()

    # DICTIONARY = [word.lower() for word in newDict]

    for word in newDict:
        trie.insert(word.lower())

# API 1: Takes in a link for the dictionary file and loads it into the memory. 
class LoadDictionary(Resource):
    # security concern, getting data from random link
    def post(self):
        # global DICTIONARY
        parser = reqparse.RequestParser()
        parser.add_argument("dictionary_url")
        args = parser.parse_args()

        dict_url = args["dictionary_url"]

        if not dict_url:
            abort(404, message="Dictionary not provided. Post to /dictionary with dictionary_url in your query. Then retry this endpoint.")

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

        # query validation
        if not word or not delta or not number:
            abort(404, message="Missing a key. Please make sure these 3 parameters exist: word, delta, and number.")
        
        # nearest = bruteNearestWord(word, int(delta), int(number))
        nearest = search(word, int(delta), int(number)) 

        foundAll = False
        if len(nearest) == int(number):
            foundAll = True

        response = jsonify({'list_of_words': nearest, 'found_number_words': foundAll})
        response.status_code = 200 
        return response

# API resource routing
api.add_resource(LoadDictionary, '/dictionary')
api.add_resource(NearestWord, '/nearestWord')

if __name__ == '__main__':
     app.run(port='7777') # can add threaded=True, to enable handling parallel requests. For now we disable it (due to global dictionary).