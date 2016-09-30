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

def getPostings(filename):
        with open(sys.argv[1] + filename, 'r') as myFile:
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


def spimi(postings):
	print 'Running SPIMI...\n'
	iterator = iter(postings)
	MAX_MEMORY = 1228800 #1200MB
	posting = next(iterator, None)
	fileNumber = 0
	dictionary = {}
	usedMemory = 0
	STRING_SIZE = 37
	while posting is not None:
		if (usedMemory <= MAX_MEMORY):
			if posting[0] not in dictionary:
				# Stored in format {term: (docFreq, documents), ...}
				dictionary[posting[0]] = [1, [posting[1]]]
                        	usedMemory += sys.getsizeof(json.dumps(posting)) - STRING_SIZE
			else:
				dictionary[posting[0]][1] = set(dictionary[posting[0]][1]) # Convert to set to avoid dupplicates
				dictionary[posting[0]][1].add(posting[1])
				dictionary[posting[0]][0] += 1 # Increment document frequency
				dictionary[posting[0]][1] = list(dictionary[posting[0]][1])
				usedMemory += sys.getsizeof(json.dumps(posting[1])) - STRING_SIZE
		else:
			fileNumber += 1	
			output = open('temp_inverted_index_' + str(fileNumber) + '.txt', 'w')
			json.dump(OrderedDict(sorted(dictionary.items(), key=lambda t: t[0])), output)
                	output.close()
			dictionary = {}
                	usedMemory = 0
			print 'created file temp_inverted_index_' + str(fileNumber) + '.txt'
		posting = next(iterator, None)



print '\nProcessing documents...'
postings = []
for filename in os.listdir(sys.argv[1]):
	if filename.endswith('.sgm'):
		postings += getPostings(filename)
spimi(postings)
