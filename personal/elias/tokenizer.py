import gc
import glob
import json
import nltk
import os
import re
import string
import sys

from collections import OrderedDict
from nltk.corpus import stopwords
from nltk import  word_tokenize
from nltk.stem.porter import PorterStemmer
from string import translate

#Global Constants
PATH = sys.argv[1]
MAX_MEMORY = int(sys.argv[2]) #1,024,000Bytes size of block in memory. Not same as on disk

def getPostings(fileName):
	with open(PATH + fileName, 'r') as myFile:
		data = myFile.read().replace('\n',' ')

	documents = re.split("<REUTERS", data)
	del documents[0]
	
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
		# Get the document ID
		docID = re.findall(r'NEWID="(.*?)">', documents[i])
		if docID:
			docID = docID[0]
		else:
			docID = ''

		# Get the title
		title =  re.findall(r'<TITLE>(.*?)</TITLE>', documents[i])
		if title:
			title = title[0]
		else:
			title = ''

		# Get the body
		body = re.findall(r'<BODY>(.*?)</BODY>', documents[i])
		if body:
			body = body[0]
		else:
			body = ''

		if title != '' or body != '':
			documents[i] = title + '#####' + body # add separator between title and body
			# Cleaning up
			documents[i] = re.sub(r'&#.+;', ' ', documents[i], )
			documents[i] = re.sub(r'&lt;', '<', documents[i])
			documents[i] = re.sub(r'&gt;', '>', documents[i])
			documents[i] = re.sub(r'<.{0,9}>', '', documents[i])
			# Remove non-ASCII values
			documents[i] = re.sub(r'[^\x00-\x7F]+', ' ', documents[i])
			# Remove unneeded spaces (needed for storing the documents as text files)
			documents[i] = re.sub(r'\s{2,5}', ' ', documents[i])
			
			# Store cleaned up text to be queried later on
			output = open("documents/" + docID + ".txt","w")
			output.write(documents[i])
			output.close()
			
			# Remove separation so that it doesn't affect indexing
			documents[i] = re.sub(r'#####', '. ', documents[i])
			
			# Tokenization of words and removal of punctuation
			documents[i] = nltk.word_tokenize(documents[i].translate(None, string.punctuation))
			
			# ***************************    Lossy Compression    *******************************
			#====================================================================================
			
# 			# Remove apostrophe
			documents[i] = [re.sub(r'\b\'m|\'s|\'re|\'d|\'ll|n\'t\b', '', token) for token in documents[i]]
# 			# No numbers
			documents[i] = [re.sub(r'\b\d+\b', '', token) for token in documents[i]]
			documents[i] = filter(lambda a: a != '', documents[i])
# 			# Case folding
			documents[i] = [token.lower() for token in documents[i]]
# 			# Removing Stopwords 25
			documents[i] = [token for token in documents[i] if token not in stopwordsList25]
# 			# Removing Stopwords 150
			documents[i] = [token for token in documents[i] if token not in stopwordsList150]
# 			# Stemming (Porter)
			stemmer = PorterStemmer()
			documents[i] = [stemmer.stem(token) for token in documents[i]]
			
			for token in documents[i]:
				postings.append((token, docID))
				
	return postings

def getNewFileName():
	if not os.path.isfile('temp_inverted_index_1.txt'):
		return 'temp_inverted_index_1.txt'
	else:
		return 'temp_inverted_index_'+str(int(re.findall(r'index_(.*?).txt', max(glob.iglob('*.txt'), key=os.path.getctime))[0])+1)+'.txt'

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
		fileName = next(jsonFiles, None)
	writeJsonToFile(invertedIndex, "inverted_index.txt")

# START INDEXING PROGRAM
print '\nProcessing documents...'
postings = []
for fileName in os.listdir(PATH):
	if fileName.endswith('.sgm'):
		postings += getPostings(fileName)

token_stream = iter(postings)
while spimiInvert(token_stream, MAX_MEMORY):
	pass

# Start Merging
mergeFiles(iter(glob.iglob('*.txt')))
