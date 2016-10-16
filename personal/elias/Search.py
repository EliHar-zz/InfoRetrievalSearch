import json
import re

from collections import OrderedDict
from matplotlib.pyplot import flag
from nltk.corpus import stopwords
from nltk import  word_tokenize
from string import translate
from CodeWarrior.Standard_Suite import document

def style(text, type):
	ansi = {'underline': '\033[4m', 'bold': '\033[1m', 'end':'\033[0m\x1b[0m', \
		'blue':'\033[94m', 'green':'\033[92m' , 'yellow':'\033[93m', \
		'red':'\033[91m', 'hlg':'\x1b[6;30;42m', 'hly':'\x1b[6;30;43m'}
	return ansi[type]+'{}{[end]}'.format(text, ansi)

# if no logical operator is specified then resort to AND
def getQueryParams(query):
	logicalOperator = ''
	query = re.sub(r'\'s|\'re|\'d|\'ll', '', query)
	# Remove non-ASCII values
	query = re.sub(r'[^\x00-\x7F]+', ' ', query)
	# Remove unneeded spaces
	query = re.sub(r'\s{2,5}', ' ', query)
	# Remove numbers
	query = re.sub(r'\d+', '', query)
	# All lower case
	query = query.lower()
	# Tokenization of words and removal of punctuation
	query = set(nltk.word_tokenize(query.translate(None, string.punctuation)))
	# get logical operators AND/OR
	if 'or' in query:
		logicalOperator = 'OR'
	elif len(query) == 1 and 'and' not in query: # Single term query
		logicalOperator = None
	else:										# Either multiple word query with no OR, so AND // And is in the query
		logicalOperator = 'AND'

	# Removing Stopwords
	query = query - set(stopwords.words('english'))
	
	return {logicalOperator: query}

def titleIndoc(document, query):
	title = ''
	# Get the title of the article (document) 
	titleMatch = re.search(r'^(.*?)#####', document)
	if titleMatch:
		title = titleMatch.group(1)
		queryTitleMatch = re.search(query, title, re.I)
		if queryTitleMatch:
			title = title.replace(query.upper(), style(query.upper(), 'hlg'))
	return (title, queryTitleMatch)

def bodyInDoc(document, query):
	displayedSnipet = ''
	# Get a sample phrase from the body
	bodyMatch = re.search(r'#####(.*?)$', document)
	if bodyMatch:
		body = bodyMatch.group(1)
		displayedSnipetMatch = re.search(r'(\.\s|\W)(.{0,80}' + query + '(?![a-zA-Z0-9_+-]).{0,80})\s', body, re.I)
		if displayedSnipetMatch:
			displayedSnipet = displayedSnipetMatch.group(2)+'...'
			displayedSnipet = displayedSnipet.replace(query, style(query, 'hly')) # "term"
			displayedSnipet = displayedSnipet.replace(query[0].upper()+query[1:], style(query[0].upper()+query[1:], 'hly')) #"Term"
			displayedSnipet = displayedSnipet.replace(query.upper(), style(query.upper(), 'hly')) # "TERM"
	return (displayedSnipet, displayedSnipetMatch)

def search():
	query = raw_input("Look for: "+'\033[92m')
	print '\r\033[0m\x1b[0m'
	# Keep program running until ':q' is introduced
	while query != ':q':
		if query in INVERTED_INDEX:
			INVERTED_INDEX[query] = OrderedDict(sorted(INVERTED_INDEX[query].items(), key=lambda x: x[1], reverse=True))
			
			print style("\n\""+query+"\"" + " is found in: \n","green")
			getMoreResults = "y"
			docID = 'someID'
			docIDStream = iter(INVERTED_INDEX[query])
			allResultsCount = len(INVERTED_INDEX[query])
			while (getMoreResults == "y" or getMoreResults == "Y") and docID:
				displayedResultCount = 0
				while displayedResultCount < 4 and docID:
					docID = next(docIDStream, None)
					if docID:
						allResultsCount -= 1
						with open("documents/"+docID+".txt") as file:
							document = file.read()
							#get and process the title and body in a document
							title = titleIndoc(document, query)
							displayedSnipet = bodyInDoc(document, query)
							# In case doc pre-processing resulted in words that will give false positive (eg. "B-6P" --> "BP")
					 		if title[1] is None and displayedSnipet[1] is None:
					 			continue
					 		
							print style('\nArticle '+docID, 'bold')+': '+title[0]+'\n\t'+displayedSnipet[0]+"\n"
							displayedResultCount += 1
				if allResultsCount > 0:
					getMoreResults = raw_input('More results? (y/n) \033[92m')
					# remove coloring and draw separator
					print '\r\033[0m\x1b[0m'
					print '\n===========================================================================================\n'
		else:
			print style('No matches found.\n', 'red')
		query = raw_input("\nLook for: \033[92m")
	# Clear colors in consol
	print '\r\033[0m\x1b[0m'	
			
print 'loading search engine...'	
INVERTED_INDEX = json.load(open('inverted_Index.txt','r'))

print '\n\t\t**************** Welcome to Tap Tap Search ******************\n\n'

search()