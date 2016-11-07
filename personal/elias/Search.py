import json
import nltk
import os
import re
import sys

from collections import OrderedDict
from math import log
from nltk.corpus import stopwords
from nltk import  word_tokenize
from string import translate, punctuation

# method to color the text
def style(text, type):
	ansi = {'underline': '\033[4m', 'bold': '\033[1m', 'end':'\033[0m\x1b[0m', \
		'blue':'\033[94m', 'green':'\033[92m' , 'yellow':'\033[93m', \
		'red':'\033[91m', 'hlg':'\x1b[6;30;42m', 'hly':'\x1b[6;30;43m'}
	return ansi[type]+'{}{[end]}'.format(text, ansi)

def underlineText(text):
	text = '\033[4m' + text
	text = text.replace('\033[0m\x1b[0m', '\033[0m\x1b[0m\033[4m')
	return text + '\033[0m\x1b[0m'

# Given a query, process the words, tokenize them and determine the type of query AND / OR / Single term 
# if no logical operator is specified then resort to AND
def getBooleanQueryParams(query):
	logicalOperator = ''
	# Remove non-ascii characters
# 	query = re.sub(r'[^\x00-\x7F]+', ' ', query)
	queryTerms = set(nltk.word_tokenize(query.translate(None, punctuation)))
	# Remove apostrophe
# 	queryTerms = [re.sub(r'\b\'m|\'s|\'re|\'d|\'ll|n\'t\b', '', token) for token in queryTerms]
	# No numbers
# 	queryTerms = [re.sub(r'\b\d+\.?\d*\b', '', token) for token in queryTerms]
# 	queryTerms = filter(lambda a: a != '', queryTerms)
	# Case folding
# 	queryTerms = [token.lower() for token in queryTerms]

	# get logical operators AND/OR
	if 'or' in queryTerms or 'OR' in queryTerms:
		logicalOperator = 'OR'
	elif len(queryTerms) == 1 and 'and' not in queryTerms and 'AND' not in queryTerms: # Single term query
		logicalOperator = None
	else:										# Either multiple word query with no OR, so AND // And is in the query
		logicalOperator = 'AND'
	# remove logical operators
	queryTerms = queryTerms - set(['and', 'AND', 'or', 'OR'])
	# Removing Stopwords (done after removing logical operators)
# 	queryTerms = set(queryTerms) - set(stopwords.words('english'))
	return (logicalOperator, queryTerms)

def getQueryTerms(query):
	# Remove non-ascii characters
# 	query = re.sub(r'[^\x00-\x7F]+', ' ', query)
	queryTerms = set(nltk.word_tokenize(query.translate(None, punctuation)))
	# Remove apostrophe
# 	queryTerms = [re.sub(r'\b\'m|\'s|\'re|\'d|\'ll|n\'t\b', '', token) for token in queryTerms]
	# No numbers
# 	queryTerms = [re.sub(r'\b\d+\.?\d*\b', '', token) for token in queryTerms]
# 	queryTerms = filter(lambda a: a != '', queryTerms)
	# Case folding
# 	queryTerms = [token.lower() for token in queryTerms]
	# Removing Stopwords
# 	queryTerms = set(queryTerms) - set(stopwords.words('english'))
	return queryTerms

# Given a document and a list of query terms, it returns the title and if any of the query terms matched the title
def titleIndoc(document, queryTerms):
	title = ''
	allTerms = ''
	matched = False
	for term in queryTerms:
		allTerms += allTerms+'|'
	allTerms = allTerms[:len(allTerms)-1]
	# Get the title of the article (document) 
	titleMatch = re.search(r'^(.*?)#####', document)
	if titleMatch:
		title = titleMatch.group(1)
		for term in queryTerms:
			queryTitleMatch = re.search(r'(\b'+term+'\\b)', title, re.I)
			if queryTitleMatch:
				matched = True
				title = re.sub(r'\b'+term.upper()+'\\b', style(term.upper(), 'green'), title)
	title = underlineText(title)
	return (title, matched)

# Given a document and a list of query terms, it returns the displayed text snipet from the body and if any of the query terms matched the snipet
def bodyInDoc(document, queryTerms):
	displayedSnipet = ''
	matched = False
	# Extract the body
	bodyMatch = re.search(r'#####(.*?)$', document)
	if bodyMatch:
		body = bodyMatch.group(1)
		# Get a sample phrase from the body
		for term in queryTerms:
			displayedSnipetMatch = re.search(r'' + term + '[.,\/#!$%\^&\*;:{}=\-_`~() ]', displayedSnipet, re.I) # To avoid apending a new snipet if new term already in old snipet
			if displayedSnipet == '' or not displayedSnipetMatch:
				displayedSnipetMatch = re.search(r'(\.\s|\W)(.{0,100}' + term + '([.,\/#!$%\^&\*;:{}=\-_`~() ]).{0,120})\s', body, re.I)
				if displayedSnipetMatch:
					matched = True
					displayedSnipet += displayedSnipetMatch.group(2)+'... '
			# Coloring the matched terms in the chosen snipet
			for term in queryTerms:
				# Replace all cases of the term: "term", "Term", "TERM"
				displayedSnipet = re.sub(r'\b'+term.upper()+'\\b', style(term.upper(),'green'), displayedSnipet)
				displayedSnipet = re.sub(r'\b'+term+'\\b', style(term, 'green'), displayedSnipet)
				displayedSnipet = re.sub(r'\b'+term[0].upper()+term[1:]+'\\b', style(term[0].upper()+term[1:], 'green'), displayedSnipet)
	return (displayedSnipet, matched)

# ********** FOR BOOLEAN RETRIEVAL  ************
# def getDocIds(queryParams):
# 	if queryParams[0] == None:
# 		if len(queryParams[1]) == 0:
# 			return {} 
# 		singleTerm = list(queryParams[1])[0]
# 		if INVERTED_INDEX.has_key(singleTerm):
# 			INVERTED_INDEX[singleTerm] = OrderedDict(sorted(INVERTED_INDEX[singleTerm].items(), key=lambda x: x[1], reverse=True))
# 			return INVERTED_INDEX[singleTerm] # single term
# 		else:
# 			return {}
# 	elif queryParams[0] == 'OR':
# 		# Add all terms in dictionary of {docID: term}
# 		result = {}
# 		for term in queryParams[1]:
# 			if INVERTED_INDEX.has_key(term):
# 				for docId in INVERTED_INDEX[term]:
# 					if result.has_key(docId):
# 						result[docId].add(term)
# 					else:
# 						result[docId] = set([term])
# 		result = OrderedDict(sorted(result.items(), key=lambda x: len(x[1]), reverse=True))
# 		return result
# 	elif queryParams[0] == 'AND':
# 		result = andQueryResult(queryParams[1])
# 		result = OrderedDict(sorted(result.items(), key=lambda x: x[1], reverse=True))
# 		return result
	
def getDocIds(queryTerms):
	if len(queryTerms) == 0:
		return {} 
	result = set([])
	for term in queryTerms:
		if INVERTED_INDEX.has_key(term):
			for docId in INVERTED_INDEX[term]:
					result.add(docId)
	return result

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
			union[key] = union[key] + dict2[key] # Add up term frequencies
		else:
			union[key] = dict2[key]
	return union

def docIdDictIntersect(dict1, dict2):
	intersection = {}
	for key in dict2:
		if dict1.has_key(key):
			intersection[key] = dict1[key] + dict2[key] # Add up term frequencies
	return intersection
		

# **************************** Ranking   **************************

def docFreq(term):
	if not INVERTED_INDEX.has_key(term):
		return 0 
	return len(INVERTED_INDEX[term])

def termFreq(term, docId):
	if not INVERTED_INDEX.has_key(term):
		return 0
	elif not INVERTED_INDEX[term].has_key(docId):
		return 0
	return INVERTED_INDEX[term][docId]

def IDF(term):
	numDocs = 20842
	return log((numDocs - docFreq(term) + 0.5) / (docFreq(term) + 0.5))

def score_BM25(docId, queryTerms, avgDoclength, docLength):
	b = 0.75
	k = 1.2
	score = 0
	for term in queryTerms:
		score += (IDF(term) * termFreq(term, docId) * (k + 1)) / (termFreq(term, docId) + k * (1 - b + b * (float(docLength) / avgDoclength)))
	
	return score

def getAvgDocLength():
	numWords = 0
	fileCount = 0
	for fileName in os.listdir("documents/"):
		if fileName.endswith('.txt'):
			fileCount += 1
			with open("documents/"+fileName) as file:
				document = file.read()
				numWords += len(document)
	return float(numWords) / float(fileCount)

def getDocLength(docId):
	with open("documents/"+docId+".txt") as file:
		document = file.read()
		# **** remove any stopwords or anything removed during lossy compression
		return len(document)
	
def getRankedDocs(docIdDict, queryTerms):
	result = {}
	for docId in docIdDict:
		docLength = getDocLength(docId)
		result[docId] = score_BM25(docId, queryTerms, avgDoclength, docLength)
	return OrderedDict(sorted(result.items(), key=lambda x: x[1], reverse=True))
	
# **************************** Search  **************************

def search(pageSize):
	query = raw_input("Looking for: \033[93m")
	print '\r\033[0m\x1b[0m'
	# Keep program running until ':q' is introduced
	while query[0] != ':':
		queryTerms = getQueryTerms(query)
		docIdDict = getDocIds(queryTerms) # gets the doc Id dictionary in order according to the requirements
		docIdDict = getRankedDocs(docIdDict, queryTerms) # get the results ranked using BM25 score
		if len(docIdDict) > 0:
			docIDStream = iter(docIdDict)
			print style("\""+query+"\"" + " is found in " + str(len(docIdDict)) + " documents:","green")
			getMoreResults = ""
			docId = 'someID'
			allResultsCount = len(docIdDict)
			while (getMoreResults == "") and docId:
				displayedResultCount = 0
				while displayedResultCount < pageSize and docId:
					docId = next(docIDStream, None)
					if docId:
						allResultsCount -= 1
						with open("documents/"+docId+".txt") as file:
							document = file.read()
							displayedSnipetText = ''
							title = titleIndoc(document, queryTerms)
							displayedSnipet = bodyInDoc(document, queryTerms)
							if not title[1] and not displayedSnipet[1]:
					 			continue
					 		
							print style('\nArticle '+docId, 'bold')+': '+title[0]+'\n\t'+displayedSnipet[0]+"\n"
							displayedResultCount += 1
				if allResultsCount > 0:
					getMoreResults = raw_input('Press \x1b[6;30;43mRETURN\033[0m\x1b[0m for more results? \033[93m')
					print '\r\033[0m\x1b[0m' # remove text coloring
					# Draw separator
					print '\n===========================================================================================\n'
		else:
			print style('No matches found.\n', 'red')
		query = raw_input("\nLooking for: \033[93m")
	# Clear colors in consol
	print '\r\033[0m\x1b[0m'
			
			
# START PROGRAM
INVERTED_INDEX = json.load(open('indexes/inverted_index_uncompressed.txt','r'))
avgDoclength = getAvgDocLength()
PAGE_SIZE = int(sys.argv[1])
print style('\n\t\t************************* Welcome to Tap Tap Search ***************************\n\n', 'underline')
search(PAGE_SIZE)