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

def writeBlockToDisk(sortedDictionary, fileName):
	output = open(fileName, 'w')
	pickle.dump(sortedDictionary, output)
	output.close()
	print 'created file '+fileName
	return output

def sortDocIDs(dictionary):
	for term in dictionary:
		dictionary[term][1] = sorted(dictionary[term][1])
	return dictionary

def spimiInvert(token_stream, blockSize):
	fileName = getNewFileName()
	dictionary = {}
	while (sys.getsizeof(dictionary) <= blockSize):
		posting = next(token_stream, None)
		if posting:
			if posting[0] not in dictionary:
				# Stored in format {term: [docFreq, set([doIDs])}
				dictionary[posting[0]] = [1, set([posting[1]])]
			else:
				if posting[1] not in dictionary[posting[0]][1]:
					dictionary[posting[0]][1].add(posting[1])
					dictionary[posting[0]][0] += 1 # Increment document frequency
		else:
			break
	
	if len(dictionary) > 0:
		dictionary = sortTerms(dictionary)
		dictionary = sortDocIDs(dictionary)
		return writeBlockToDisk(dictionary, fileName)
	else:
		return None


print '\nProcessing documents...'
postings = []
for fileName in os.listdir('../../ReutersCorpus'):#sys.argv[1]):
	if fileName.endswith('.sgm'):
		postings += getPostings(fileName)

token_stream = iter(postings)
while spimiInvert(token_stream, BLOCK_SIZE):
	pass
