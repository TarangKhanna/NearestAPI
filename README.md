# WordGeneratorAPI
API to generate nearest words based on provided dictionary.

# Run
I tested using Python 3.7.3 

pip install -r requirements.txt

python core.py 

will run in localhost on port 7777

pip freeze output:

aniso8601==6.0.0
certifi==2019.3.9
Click==7.0
editdistance==0.5.3
Flask==1.0.3
Flask-Jsonpify==1.5.0
Flask-RESTful==0.3.7
itsdangerous==1.1.0
Jinja2==2.10.1
MarkupSafe==1.1.1
pytz==2019.1
six==1.12.0
Werkzeug==0.15.4

# API requests

API 1: 
POST http://127.0.0.1:7777/dictionary?dictionary_url=https://raw.githubusercontent.com/dwyl/english-words/master/words.txt

Expected output:
{
    "loaded_dictionary_url": "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"
}

API 2: 
GET http://127.0.0.1:7777/nearestWord?word=car&delta=1&number=5 

Expected output:
{
    "found_number_words": true,
    "list_of_words": [
        "aar",
        "ar",
        "bar",
        "ca",
        "ca'"
    ]
}

# Notes

Ideas for word generation:

    1) leveistein automata, modify to find exact n away. Or use this to prune the search space. 
    2) graph representation, where weight of edge is edit distance - graph generation is expensive, calculation from there is cheaper. 
    What if input word is not in the given dictionary? Find closest word based on edit distance.
    3) range based, sort input accoridng to length. Proof of correctness: 
    4) brute force: for every word in dictionary, calculate edit distance. Terminate early if we got 'number' amount of words delta edit distance away from intput 'word'
    5) Use brute force to test correctness of improved solution

Assumptions for design:

    1) Global dictionary, uploading new dictionary will overrite previous dictionary.
    2) Assuming that case does not matter-convert dictionary and input word to lower case. 
    3) Assuming finding nearest words (API 2), will be called more often than load dictionary (API 1). So, we can optimize design for API 2.
    4) Dictionary/trie is not user specific, and is shared by all connections.
    5) Single threaded.
    6) If we can not find enough number of words exactly delta away from input word, API 2 returns how many ever possible, with a flag (found_number_words) to indicate if it found required matches (true if it did).
    7) nearest words returned are in alphabetical ordering
    8) space is counted as a character, so if we have "car " as input, with delta 1, 
    our output can have "car" as 1 edit distance away

Performance breakdown:

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
