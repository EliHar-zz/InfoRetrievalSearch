import json
import nltk
import os
import re
import string
import sys
import threading
from nltk.corpus import stopwords
from nltk import  word_tokenize

def processFile(filename):
	print '\nReading file:' + filename + ' ...'
        with open(sys.argv[1] + filename, 'r') as myFile:
        	data = myFile.read().replace('\n',' ')

	print '\nSplitting documents...'
	documents = re.split("<REUTERS", data)
	del documents[0]
	tokens = []
	outputFilename = filename + '_OUTPUT.txt'
	output = open(outputFilename, 'w')
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
		# Remove non-ASCII values
		documents[i] = re.sub(r'[^\x00-\x7F]+', ' ', documents[i])
		# 2. Tokenization of words and removal of punctuation
		documents[i] = nltk.word_tokenize(documents[i].translate(None, string.punctuation))
		# 3. Removing Stopwords
		documents[i] = [word for word in documents[i] if word.lower() not in stopwords.words('english')]

		for token in documents[i]:
			tokens.append((token, docID))

	json.dump(tokens, output)
	output.close()
	print '\nFinished... created '+ outputFilename

for filename in os.listdir(sys.argv[1]):
	if filename.endswith('.sgm'):
		thread = threading.Thread(target=processFile, args=(filename,))
		thread.start()
