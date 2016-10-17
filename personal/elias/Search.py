import json
import re
import nltk

from collections import OrderedDict
from matplotlib.pyplot import flag
from nltk.corpus import stopwords
from nltk import  word_tokenize
from string import translate, punctuation
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
	queryTerms = set(nltk.word_tokenize(query.translate(None, punctuation)))
	# get logical operators AND/OR
	if 'or' in queryTerms:
		logicalOperator = 'OR'
	elif len(queryTerms) == 1 and 'and' not in queryTerms: # Single term query
		logicalOperator = None
	else:										# Either multiple word query with no OR, so AND // And is in the query
		logicalOperator = 'AND'

	# Removing Stopwords
	queryTerms = queryTerms - set(stopwords.words('english'))
	
	return (logicalOperator, queryTerms)

def titleIndoc(document, queryTerms):
	title = ''
	allTerms = ''
	for term in queryTerms:
		allTerms += allTerms+'|'
	allTerms = allTerms[:len(allTerms)-1]
	# Get the title of the article (document) 
	titleMatch = re.search(r'^(.*?)#####', document)
	if titleMatch:
		title = titleMatch.group(1)
		queryTitleMatch = re.search(r''+allTerms+'(?![a-zA-Z0-9_+-])', title, re.I)
		if queryTitleMatch:
			for term in queryTerms:
				title = title.replace(term.upper(), style(term.upper(), 'hlg'))
	return (title, queryTitleMatch)

def bodyInDoc(document, queryTerms):
	displayedSnipet = ''
	allTerms = ''
	for term in queryTerms:
		allTerms += allTerms+'|'
	allTerms = allTerms[:len(allTerms)-1]
	# Get a sample phrase from the body
	bodyMatch = re.search(r'#####(.*?)$', document)
	if bodyMatch:
		body = bodyMatch.group(1)
		displayedSnipetMatch = re.search(r'(\.\s|\W)(.{0,80}' + allTerms + '(?![a-zA-Z0-9_+-]).{0,80})\s', body, re.I)
		if displayedSnipetMatch:
			displayedSnipet = displayedSnipetMatch.group(2)+'...'
			for term in queryTerms:
				displayedSnipet = displayedSnipet.replace(term, style(term, 'hly')) # "term"
				displayedSnipet = displayedSnipet.replace(term[0].upper()+term[1:], style(term[0].upper()+term[1:], 'hly')) #"Term"
				displayedSnipet = displayedSnipet.replace(term.upper(), style(term.upper(), 'hly')) # "TERM"
	return (displayedSnipet, displayedSnipetMatch)

def getDocIds(queryParams):
	if queryParams[0] == None:
		singleTerm = list(queryParams[1])[0]
		if INVERTED_INDEX.has_key(singleTerm):
			INVERTED_INDEX[singleTerm] = OrderedDict(sorted(INVERTED_INDEX[singleTerm].items(), key=lambda x: x[1], reverse=True))
			return INVERTED_INDEX[singleTerm] # single term
		else:
			return {}
	elif queryParams[0] == 'OR':
		# Add all terms in dictionary of {docID: term}
		result = {}
		for term in queryParams[1]:
			if INVERTED_INDEX.has_key(term):
				for docId in INVERTED_INDEX[term]:
					if result.has_key(docId):
						result[docId].add(term)
					else:
						result[docId] = set([term])
		result = OrderedDict(sorted(result.items(), key=lambda x: len(x[1]), reverse=True))
		return result
	elif queryParams[0] == 'AND':
		return OrderedDict(sorted(andQueryResult(queryParams[1]).items(), key=lambda x: x[1], reverse=True))

def orQueryResult(queryTerms):
	union = {}
	for term in queryTerms:
		if INVERTED_INDEX.has_key(term):
			union = docIdDictUnion(union, INVERTED_INDEX[term])
	return union
	
def andQueryResult(queryTerms):
	# intersection of postings lists
	intersection = {}
	terms = iter(queryTerms)
	term = next(terms, None)
	if not INVERTED_INDEX.has_key(term):
		return {}
	intersection.update(INVERTED_INDEX[term])
	term = next(terms, None)
	while term:
		if not INVERTED_INDEX.has_key(term):
			return {}
		intersection = docIdDictIntersect(intersection, INVERTED_INDEX[term])
		term = next(terms, None)
	return intersection

def docIdDictDiff(dict1, dict2):
	diff = {}
	for key in dict1:
		if not dict2.has_key(key):
			diff[key] = dict1[key]
	return diff

def docIdDictUnion(dict1, dict2):
	union = {}
	union.update(dict1)
	for key in dict2:
		if union.has_key(key):
			union[key] = union[key]+dict2[key]
		else:
			union[key] = dict2[key]
	return union

def docIdDictIntersect(dict1, dict2):
	intersection = {}
	for key in dict2:
		if dict1.has_key(key):
			intersection[key] = dict1[key]+dict2[key]
	return intersection
		

def search(pageSize):
	query = raw_input("Look for: "+'\033[92m')
	print '\r\033[0m\x1b[0m'
	# Keep program running until ':q' is introduced
	while query[0] != ':':
		queryParams = getQueryParams(query)
		queryTerms = queryParams[1]
		docIdDict = getDocIds(queryParams) # gets the doc Id dictionary in order according to the requirements
		if len(docIdDict) > 0:
			docIDStream = iter(docIdDict)
			print style("\n\""+query+"\"" + " is found in " + str(len(docIdDict)) + " documents:","green")
			getMoreResults = "y"
			docId = 'someID'
			allResultsCount = len(docIdDict)
			while (getMoreResults == "y" or getMoreResults == "Y") and docId:
				displayedResultCount = 0
				while displayedResultCount < pageSize and docId:
					docId = next(docIDStream, None)
					if docId:
						allResultsCount -= 1
						with open("documents/"+docId+".txt") as file:
							document = file.read()
							displayedSnipetText = ''
# 							title = None
							#get and process the title and body in a document
# 							for term in queryTerms:
# 								if not title:
							title = titleIndoc(document, queryTerms)
# 							else:
							displayedSnipet = bodyInDoc(document, queryTerms)
# 							displayedSnipetText += displayedSnipet[0]
							# In case doc pre-processing resulted in words that will give false positive (eg. "B-6P" --> "BP")
					 		if title[1] is None and displayedSnipet[1] is None:
					 			continue
					 		
							print style('\nArticle '+docId, 'bold')+': '+title[0]+'\n\t'+displayedSnipet[0]+"\n"
							displayedResultCount += 1
				if allResultsCount > 0:
					getMoreResults = raw_input('More results? (y/n) \033[92m')
					print '\r\033[0m\x1b[0m' # remove text coloring
					# Draw separator
					print '\n===========================================================================================\n'
		else:
			print style('No matches found.\n', 'red')
		query = raw_input("\nLook for: \033[92m")
	# Clear colors in consol
	print '\r\033[0m\x1b[0m'	
			
print 'loading search engine...'	
INVERTED_INDEX = json.load(open('inverted_Index.txt','r'))

print '\n\t\t**************** Welcome to Tap Tap Search ******************\n\n'

search(4)