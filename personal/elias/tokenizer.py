import collections
import json
import nltk
import os
import re
import string
import sys
from collections import OrderedDict
from nltk.corpus import stopwords
from nltk import  word_tokenize

#Global Constants
BLOCK_SIZE = 1024000 #1,024,000Bytes
PATH = '../../ReutersCorpus/'

def getPostings(filename):
        with open(PATH + filename, 'r') as myFile:
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


def spimi(generator, blockSize):
	print 'Running SPIMI...\n'
	posting = next(generator, None)
	fileNumber = 0
	dictionary = {}
	usedMemory = 0
	while posting is not None:
		if (usedMemory <= blockSize):
			if posting[0] not in dictionary:
				# Stored in format {term: (docFreq, documents), ...}
				dictionary[posting[0]] = [1, set([posting[1]])]
			else:
				dictionary[posting[0]][1].add(posting[1])
				dictionary[posting[0]][0] += 1 # Increment document frequency
			usedMemory = sys.getsizeof(dictionary)
		else:
			fileNumber += 1	
			output = open('temp_inverted_index_' + str(fileNumber) + '.txt', 'w')
			# Converting the sets to lists in order to be serialized
			for term in dictionary:
				dictionary[term][1] = sorted(list(dictionary[term][1]))
			json.dump(OrderedDict(sorted(dictionary.items(), key=lambda t: t[0])), output)
			output.close()
			dictionary = {}
			usedMemory = 0
			print 'created file temp_inverted_index_' + str(fileNumber) + '.txt'
		posting = next(generator, None)



print '\nProcessing documents...'
postings = []
for filename in os.listdir('../../ReutersCorpus'):#sys.argv[1]):
	if filename.endswith('.sgm'):
		postings += getPostings(filename)
postingsGenerator = iter(postings)
spimi(postingsGenerator, BLOCK_SIZE)
