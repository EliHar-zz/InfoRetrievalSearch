import pickle
import thread
from pandas.io.wb import search

def search():
	query = raw_input("Search for: ")
	if query in INVERTED_INDEX:
		print "\""+query+"\"" + " is found in: "
		print INVERTED_INDEX[query][1]
		
print '\n\t\t**************** Welcome to me search engine ******************\n\n'

file = open('inverted_Index.pickle','r')
INVERTED_INDEX = pickle.load(file)


search()
