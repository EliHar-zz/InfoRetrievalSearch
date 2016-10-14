import collections
import glob
import nltk
import os
import pickle
import re
import string
import sys
from collections import OrderedDict
from nltk.corpus import stopwords
from nltk import  word_tokenize

#Global Constants
BLOCK_SIZE = 1024000 #1,024,000Bytes size of block in memory. Not same as on disk
PATH = '../../ReutersCorpus/'

def getPostings(fileName):
	with open(PATH + fileName, 'r') as myFile:
		data = myFile.read().replace('\n',' ')

	documents = re.split("<REUTERS", data)
	del documents[0]
	stopwordsList = set(stopwords.words('english'))
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

		documents[i] = title + ' ' + body
		documents[i] = re.sub(r'&#.+;', ' ', documents[i])
		documents[i] = re.sub(r'&lt;', '<', documents[i])
		documents[i] = re.sub(r'&gt;', '>', documents[i])
		# 1. Remove numbers
		documents[i] = re.sub(r'\d+', '', documents[i])
		# 2. Remove non-ASCII values
		documents[i] = re.sub(r'[^\x00-\x7F]+', ' ', documents[i])
		# 3. Tokenization of words and removal of punctuation
		documents[i] = nltk.word_tokenize(documents[i].translate(None, string.punctuation))
		# 4. Removing Stopwords
		documents[i] = [word for word in documents[i] if word.lower() not in stopwordsList]
		for token in documents[i]:
			postings.append((token, docID))
	return postings

def getNewFileName():
	if not os.path.isfile('temp_inverted_index_1.pickle'):
		return 'temp_inverted_index_1.pickle'
	else:
		return 'temp_inverted_index_'+str(int(re.findall(r'index_(.*?).pickle', max(glob.iglob('*.pickle'), key=os.path.getctime))[0])+1)+'.pickle'

def sortTerms(dictionary):
	return OrderedDict(sorted(dictionary.items(), key=lambda t: t[0]))

def writeToDisk(sortedDictionary, fileName):
	output = open(fileName, 'w')
	pickle.dump(sortedDictionary, output)
	output.close()
	print 'created file '+fileName
	return True

def sortDocIDs(dictionary):
	for term in dictionary:
		dictionary[term][1] = OrderedDict(sorted(dictionary[term][1].items(), key=lambda t: int(t[0])))
	return dictionary

def spimiInvert(token_stream, blockSize):
	fileName = getNewFileName()
	dictionary = {}
	while (sys.getsizeof(dictionary) <= blockSize):
		posting = next(token_stream, None)
		if posting: #[term, docID]
			if posting[0] not in dictionary:
				# Stored in format {term: [docFreq, {docID:termFreq, docID:termFrec ...}}
				dictionary[posting[0]] = [1, {posting[1]:1}]
			else:
				if posting[1] not in dictionary[posting[0]][1]:
					dictionary[posting[0]][1][posting[1]] = 1
					dictionary[posting[0]][0] += 1 # Increment document frequency
				else:
					dictionary[posting[0]][1][posting[1]] += 1
		else:
			break
	
	if len(dictionary) > 0:
		dictionary = sortTerms(dictionary)
		dictionary = sortDocIDs(dictionary)
		return writeToDisk(dictionary, fileName)
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
					for docID in dict1[term1][1]:
						if docID in invertedIndex[term1][1]:
							invertedIndex[term1][1][docID] += dict1[term1][1][docID]
						else:
							invertedIndex[term1][1][docID] = dict1[term1][1][docID]
							invertedIndex[term1][0] += 1
				term1 = next(iter1,None)
			elif term2 < term1:
				if term2 not in invertedIndex:
					invertedIndex[term2] = dict2[term2]
				else:
					for docID in dict2[term2][1]:
						if docID in invertedIndex[term2][1]:
							invertedIndex[term2][1][docID] += dict2[term2][1][docID]
						else:
							invertedIndex[term2][1][docID] = dict2[term2][1][docID]
							invertedIndex[term2][0] += 1
				term2 = next(iter2,None)
		
		if term1 is None:
			while term2 != None:
				if term2 not in invertedIndex:
					invertedIndex[term2] = dict2[term2]
				else:
					for docID in dict2[term2][1]:
						if docID in invertedIndex[term2][1]:
							invertedIndex[term2][1][docID] += dict2[term2][1][docID]
						else:
							invertedIndex[term2][1][docID] = dict2[term2][1][docID]
							invertedIndex[term2][0] += 1
				term2 = next(iter2,None)
		else:
			while term1 != None:
				if term1 not in invertedIndex:
					invertedIndex[term1] = dict1[term1]
				else:
					for docID in dict1[term1][1]:
						if docID in invertedIndex[term1][1]:
							invertedIndex[term1][1][docID] += dict1[term1][1][docID]
						else:
							invertedIndex[term1][1][docID] = dict1[term1][1][docID]
							invertedIndex[term1][0] += 1
				term1 = next(iter1,None)
	return invertedIndex


def mergeFiles(pickleFiles):
	invertedIndex = OrderedDict()	
	fileName = next(pickleFiles, None)
	while fileName != None:
		print '\nMerging file: ' + fileName
		dict = pickle.load(open(fileName,'r'))
		invertedIndex = mergDicts(dict, invertedIndex)
		# get the next file to merge
		fileName = next(pickleFiles, None)
	writeToDisk(invertedIndex, "inverted_Index.pickle")

# START INDEXING PROGRAM
print '\nProcessing documents...'
postings = []
for fileName in os.listdir('../../ReutersCorpus'):#sys.argv[1]):
	if fileName.endswith('.sgm'):
		postings += getPostings(fileName)

token_stream = iter(postings)
while spimiInvert(token_stream, BLOCK_SIZE):
	pass

# Start Merging
mergeFiles(iter(glob.iglob('*.pickle')))
