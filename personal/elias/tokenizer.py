import gc
import glob
import json
import os
import re
import sys

from collections import OrderedDict
from nltk.corpus import stopwords
from nltk import  word_tokenize
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
			documents[i] = title + '#####' + body
			documents[i] = re.sub(r'&#.+;', ' ', documents[i], )
			documents[i] = re.sub(r'&lt;', '<', documents[i])
			documents[i] = re.sub(r'&gt;', '>', documents[i])
			documents[i] = re.sub(r'<.{0,9}>', '', documents[i])
			# Remove appostrophe
			documents[i] = re.sub(r'\'s|\'re|\'d|\'ll', '', documents[i])
			
			# Remove non-ASCII values
			documents[i] = re.sub(r'[^\x00-\x7F]+', ' ', documents[i])
			# Remove unneeded spaces
			documents[i] = re.sub(r'\s{2,5}', ' ', documents[i])

			output = open("documents/" + docID + ".txt","w")
			output.write(documents[i])
			output.close()
			
			documents[i] = re.sub(r'#####', '. ', documents[i])
# 			documents[i] = documents[i].replace('\n',' ')
			# 1. Remove numbers
			documents[i] = re.sub(r'\d+', '', documents[i])
			# 2. Tokenization of words and removal of punctuation
			documents[i] = nltk.word_tokenize(documents[i].translate(None, string.punctuation))
			# 3. Removing Stopwords
			documents[i] = [word.lower() for word in documents[i] if word.lower() not in stopwordsList150]
			
			for token in documents[i]:
				postings.append((token, docID))
				
	return postings

def getNewFileName():
	if not os.path.isfile('temp_inverted_index_1.txt'):
		return 'temp_inverted_index_1.txt'
	else:
		return 'temp_inverted_index_'+str(int(re.findall(r'index_(.*?).txt', max(glob.iglob('*.txt'), key=os.path.getctime))[0])+1)+'.txt'

def sortTerms(dictionary):
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
			if posting[0] not in dictionary:
				# Stored in format {term: {docID:termFreq, docID:termFrec ...}}
				dictionary[posting[0]] = {posting[1]:1}
			else:
				if posting[1] not in dictionary[posting[0]]:
					dictionary[posting[0]][posting[1]] = 1
				else:
					dictionary[posting[0]][posting[1]] += 1
		else:
			break
	
	if len(dictionary) > 0:
		dictionary = sortTerms(dictionary)
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
						if docID in invertedIndex[term1]:
							invertedIndex[term1][docID] += dict1[term1][docID]
						else:
							invertedIndex[term1][docID] = dict1[term1][docID]
				term1 = next(iter1,None)
			elif term2 < term1:
				if term2 not in invertedIndex:
					invertedIndex[term2] = dict2[term2]
				else:
					for docID in dict2[term2]:
						if docID in invertedIndex[term2]:
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
						if docID in invertedIndex[term2]:
							invertedIndex[term2][docID] += dict2[term2][docID]
						else:
							invertedIndex[term2][docID] = dict2[term2][docID]
				term2 = next(iter2,None)
		else:
			while term1 != None:
				if term1 not in invertedIndex:
					invertedIndex[term1] = dict1[term1]
				else:
					for docID in dict1[term1]:
						if docID in invertedIndex[term1]:
							invertedIndex[term1][docID] += dict1[term1][docID]
						else:
							invertedIndex[term1][docID] = dict1[term1][docID]
				term1 = next(iter1,None)
	return invertedIndex


def mergeFiles(jsonFiles):
	invertedIndex = OrderedDict()	
	fileName = next(jsonFiles, None)
	while fileName != None:
		print '\nMerging file: ' + fileName
		dict = json.load(open(fileName,'r'))
		invertedIndex = mergDicts(dict, invertedIndex)
		# get the next file to merge
		fileName = next(jsonFiles, None)
# 	invertedIndex = sortDocIDs(invertedIndex)
	writeJsonToFile(invertedIndex, "inverted_Index.txt")

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
