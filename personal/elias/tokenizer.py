import sys
import nltk
import re
import json
from nltk.corpus import stopwords
from nltk import  word_tokenize

def removeStopwords(text):
        return [word for word in text if word not in stopwords.words('english')]

print '\nReading file:' + sys.argv[1] + ' ...'

CORPUS_PATH = "/nfs/home/e/e_harou/Documents/InfoRetrieval/InfoRetrievalSearch/ReutersCorpus/"

with open(CORPUS_PATH + sys.argv[1], 'r') as myFile:
	data = myFile.read()

print '\nSplitting documents...'
documents = re.split("<REUTERS", data)

docID = re.findall(r'NEWID="(.*?)">', data, re.DOTALL)
titles = re.findall(r'<TITLE>(.*?)</TITLE>', data, re.DOTALL)
bodies = re.findall(r'<BODY>(.*?)</BODY>', data, re.DOTALL)

print len(docID),len(titles),len(bodies)

del documents[0]

tokens = []
outputFilename = sys.argv[1] + '_OUTPUT.txt'
output = open(outputFilename, 'w')
# Only keeps text from TITLE and BODY without tags or HTML symbols.
for i in range(len(documents)):
	docID = re.findall(r'NEWID="(.*?)">', documents[i])[0]
	title =  re.findall(r'<TITLE>(.*?)</TITLE>', documents[i])
	if title:
		title = title[0] 
	body = re.findall(r'<BODY>(.*?)</BODY>', documents[i])
	if body:
		body = body[0]
	documents[i] = title + ' ' + body
	documents[i] = re.sub(r'&#.+;',' ',documents[i])
	documents[i] = re.sub(r'&lt;','<',documents[i])
	documents[i] = re.sub(r'&gt;','>',documents[i])
	documents[i] = documents[i].lower()
	
	# 2. Tokenization of words by punctuation except the period
        documents[i] = nltk.word_tokenize(documents[i])
        # 3. Removing Stopwords
        documents[i] = removeStopwords(documents[i])

	for token in documents[i]:
		tokens.append((token, docID))
		json.dump((token, docID),output)
		output.flush()
output.close()

print '\nFinished... created'+ outputFilename
