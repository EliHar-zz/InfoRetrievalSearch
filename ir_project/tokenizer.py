import gc
import glob
import json
import nltk
import os
import re
import string
import sys

from collections import OrderedDict
from math import log10
from nltk.corpus import stopwords
from nltk import  word_tokenize
from nltk.stem.porter import PorterStemmer
from string import translate

#Global Constants
PATH = sys.argv[1]
MAX_MEMORY = int(sys.argv[2]) #1,024,000Bytes size of block in memory. Not same as on disk

docLengthDict = {} 	# Store a dictionary of documents and their length
docIdDict = {} 	# Store a dictionary of documents and their length
docID = 0

def getPostings(fileName):
	global docID, docLengthDict, docIDDict

	with open(PATH + fileName, 'r') as myFile:
		documents = json.load(myFile)
	
	# Declaring two lists of stopwords for analysis purposes
	stopwordsList150 = set(stopwords.words('english'))
	stopwordsList25 = set(['a','an','and','are','as','at', 'be', 'by', 
					'for', 'from', 'has', 'he', 'in', 'is', 'it', 
					'its', 'of', 'on', 'that', 'the', 'to', 'was', 
					'were', 'will', 'with'
					])

	postings = []
	# Only keeps text from TITLE and BODY without tags or HTML symbols.
	for i in range(len(documents)):
		# Get the document
		document = ' '.join([documents[i]['title'], documents[i]['body']])

		# Get the document ID
		docID += 1

		# Ensure characters encoding
		document = document.encode('UTF-8', 'ignore')

		# Remove URLs from document
		url_pattern1 = r'(https?|ftp):\/\/\/?[^\s\/$.?#].[^\s]*'
		url_pattern2 = r'www\.[^\s\/$.?#].[^\s]*'	
		document = re.sub(url_pattern1, ' ', document)
		document = re.sub(url_pattern2, ' ', document)

		# Tokenization of words and removal of punctuation
		document = nltk.word_tokenize(document.translate(None, string.punctuation))

		docLengthDict[docID] = len(document)
		docIdDict[docID] = documents[i]['url']
		# ***************************    Lossy Compression    *******************************
		#====================================================================================
		
		# Remove apostrophe
		document = [re.sub(r'\b\'m|\'s|\'re|\'d|\'ll|n\'t\b', '', token) for token in document]
		# No numbers
		document = [re.sub(r'\b(\d+\w+)|(\w+\d+)|(\d+\.?\d*\w*)\b', '', token) for token in document]
		# Remove empty strings
		document = filter(lambda a: a != '', document)
			# Case folding
# 			documents[i] = [token.lower() for token in documents[i]]
			# Removing Stopwords 25
# 			documents[i] = [token for token in documents[i] if token not in stopwordsList25]
			# Removing Stopwords 150
		document = [token for token in document if token not in stopwordsList150]
			# Stemming (Porter)
# 			stemmer = PorterStemmer()
# 			documents[i] = [stemmer.stem(token) for token in documents[i]]
		
		for token in document:
			postings.append((token, docID))
				
	return postings

def getNewFileName():
	if not os.path.isfile('temp_inverted_index_1.json'):
		return 'temp_inverted_index_1.json'
	else:
		return 'temp_inverted_index_'+str(int(re.findall(r'index_(.*?).json', max(glob.iglob('*.json'), key=os.path.getctime))[0])+1)+'.json'

def sortDict(dictionary):
	return OrderedDict(sorted(dictionary.items(), key=lambda t: t[0]))

def writeJsonToFile(object, fileName):
	with open(fileName, 'w') as output:
		json.dump(object, output)
		output.close()
	print 'created file ' + fileName
	return True

def sortDocIDs(dictionary):
	for term in dictionary:
		dictionary[term] = OrderedDict(sorted(dictionary[term].items(), key=lambda t: int(t[0])))
	return dictionary

def spimiInvert(token_stream, maxMemory):
	fileName = getNewFileName()
	dictionary = {}
	while (sys.getsizeof(dictionary) <= maxMemory):
		posting = next(token_stream, None)
		if posting: #[term, docID]
			if dictionary.has_key(posting[0]):
				if dictionary[posting[0]].has_key(posting[1]):
					dictionary[posting[0]][posting[1]] += 1
				else:
					dictionary[posting[0]][posting[1]] = 1
			else:
				# Stored in format {term: {docID:termFreq, docID:termFrec ...}}
				dictionary[posting[0]] = {posting[1]:1}
		else:
			break
	
	if len(dictionary) > 0:
		dictionary = sortDict(dictionary)
# 		dictionary = sortDocIDs(dictionary)
		return writeJsonToFile(dictionary, fileName)
	else:
		return False

def mergDicts(dict1, dict2):
	invertedIndex = OrderedDict()
	if dict1 != None and dict2 != None:
		iter1 = iter(dict1)
		iter2 = iter(dict2)
		
		term1 = next(iter1,None)
		term2 = next(iter2,None)
		while term1 != None and term2 != None:
			if term1 <= term2:
				if term1 not in invertedIndex:
					invertedIndex[term1] = dict1[term1]
				else:
					for docID in dict1[term1]:
						if invertedIndex[term1].has_key(docID):
							invertedIndex[term1][docID] += dict1[term1][docID]
						else:
							invertedIndex[term1][docID] = dict1[term1][docID]
				term1 = next(iter1,None)
			elif term2 < term1:
				if term2 not in invertedIndex:
					invertedIndex[term2] = dict2[term2]
				else:
					for docID in dict2[term2]:
						if invertedIndex[term2].has_key(docID):
							invertedIndex[term2][docID] += dict2[term2][docID]
						else:
							invertedIndex[term2][docID] = dict2[term2][docID]
				term2 = next(iter2,None)
		
		if term1 is None:
			while term2 != None:
				if term2 not in invertedIndex:
					invertedIndex[term2] = dict2[term2]
				else:
					for docID in dict2[term2]:
						if invertedIndex[term2].has_key(docID):
							invertedIndex[term2][docID] += dict2[term2][docID]
						else:
							invertedIndex[term2][docID] = dict2[term2][docID]
				term2 = next(iter2,None)
		else:
			while term1 != None:
				if invertedIndex.has_key(term1):
					for docID in dict1[term1]:
						if invertedIndex[term1].has_key(docID):
							invertedIndex[term1][docID] += dict1[term1][docID]
						else:
							invertedIndex[term1][docID] = dict1[term1][docID]
				else:
					invertedIndex[term1] = dict1[term1]
				term1 = next(iter1,None)
	return invertedIndex

def mergeFiles(jsonFiles):
	invertedIndex = {}	
	fileName = next(jsonFiles, None)
	while fileName != None:
		print '\nMerging file: ' + fileName
		dict = json.load(open(fileName,'r'), object_pairs_hook = OrderedDict)
		invertedIndex = mergDicts(dict, invertedIndex)
		# get the next file to merge
		os.remove(fileName)
		fileName = next(jsonFiles, None)
	writeJsonToFile(invertedIndex, "indexes/inverted_index.json")

def index_tf_idf(path):
	with open(path + "inverted_index.json", 'r') as inverted_index_file:
		inverted_index = json.load(inverted_index_file)

	with open(path + "docs_lengths.json", 'r') as docs_lengths_file:
		N = len(json.load(docs_lengths_file))

	for term in inverted_index:
		for docId in inverted_index[term]:
			tf = inverted_index[term][docId]
			df = len(inverted_index[term])
			inverted_index[term][docId] = tf * log10(N/float(df))

	writeJsonToFile(inverted_index, path + "tf-idf_index.json")

# START INDEXING PROGRAM
print '\nProcessing documents...'
postings = []
for fileName in os.listdir(PATH):
	if fileName.endswith('.json'):
		postings += getPostings(fileName)

# Store a dictionary of documents and their length
writeJsonToFile(docLengthDict, "indexes/docs_lengths.json")
writeJsonToFile(docIdDict, "indexes/docIdDict.json")

token_stream = iter(postings)
while spimiInvert(token_stream, MAX_MEMORY):
	pass

# Start Merging
mergeFiles(iter(glob.iglob('*.json')))

# Generate a tf-idf index
index_tf_idf("indexes/")
