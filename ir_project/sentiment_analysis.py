import codecs
import sys
import json
import os
from afinn import Afinn
from nltk import sent_tokenize
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from vaderSentiment.vaderSentiment import sentiment as vaderSentiment

# Path to corpus
PATH = sys.argv[1]
SUB_URL_PATH = ''
if len(sys.argv) > 2:
	SUB_URL_PATH = sys.argv[2]

# Afinn Sentiment Analysis
afinn = Afinn()

# Google Sentiment Analysis
credentials = GoogleCredentials.get_application_default()
service = discovery.build('language', 'v1', credentials=credentials)

# Google Sentiment Analysis API https://cloud.google.com/natural-language/docs/basics
"""score of the sentiment ranges between -1.0 (negative) and 1.0 (positive) and corresponds
to the overall emotional leaning of the text.magnitude indicates the overall strength of emotion 
(both positive and negative) within the given text, between 0.0 and +inf. 
Unlike score, magnitude is not normalized; each expression of emotion within the text 
(both positive and negative) contributes to the text's magnitude (so longer text blocks may have greater magnitudes)."""
def documentGoogleSA(document):
	service_request = service.documents().analyzeSentiment(
	  body={
	    'document': {
	      'type': 'PLAIN_TEXT',
	      "language": "EN",
	      'content': document,
	    },
	    "encodingType":"UTF8",
	  }
	)

	result = service_request.execute()['documentSentiment']
	return  {'score': result['score'] * 5.0, 'magnitude': result['magnitude']} # normalized resutls, between -5 and +5

# Document Vader Sentiment Analysis https://github.com/cjhutto/vaderSentiment
# https://www.linkedin.com/pulse/sentiment-analysis-using-vader-muthuraj-kumaresan
"""Score ranges between -4.0 and 4.0
The output provides the polarity and intensity of the inputs. 
The compound in the output provides the sentiment intensity and will be
in the range of -1 (Extremely negative) to 1 (Extremely positive).
Based on the compound value, you can create more ranges to define more categorical 
values for sentiment(Extremely positive, positive, neutral, negative, Extremely negative)."""
def documentVaderSA(document):
	result = {'pos':[], 'neg':[], 'compound':[], 'neu':[]}

	sentences = sent_tokenize(document)

	for sentence in sentences:
		vs = vaderSentiment(sentence)
		result['pos'].append(vs['pos'])
    	result['neg'].append(vs['neg'])
    	result['compound'].append(vs['compound'])
    	result['neu'].append(vs['neu'])

	for category in result:
		result[category] = (float(sum(result[category]))/len(result[category])) * 5.0/4.0 # normalized resutls, between -5 and +5
		result[category] = float("{0:.2f}".format(result[category]))

	return result

# Afinn Sentiment Analysis http://www2.imm.dtu.dk/pubdb/views/edoc_download.php/6006/pdf/imm6006.pdf
# Score ranges between -5 and +5
def documentAfinnSA(document):
	score = 0
	sentences = sent_tokenize(document)

	for sentence in sentences:
		score += afinn.score(sentence)

	return float("{0:.2f}".format(float(score)/len(sentences)))

def deptScoreAvg(department_docs):
	vader_result = {'pos':[], 'neg':[], 'compound':[], 'neu':[]}
	google_result = {'score': [], 'magnitude': []}
	afinn_result = 0

	for docId in department_docs:
		afinn_result += department_docs[docId]['afinn']

		google_result['score'].append(department_docs[docId]['google']['score'])
		google_result['magnitude'].append(department_docs[docId]['google']['magnitude'])

		vader_result['pos'].append(department_docs[docId]['vader']['pos'])
		vader_result['neg'].append(department_docs[docId]['vader']['neg'])
		vader_result['compound'].append(department_docs[docId]['vader']['compound'])
		vader_result['neu'].append(department_docs[docId]['vader']['neu'])

	afinn_result = float("{0:.2f}".format(float(afinn_result)/len(department_docs)))

	for category in google_result: 
		google_result[category] = float(sum(google_result[category]))/len(google_result[category])
		google_result[category] = float("{0:.2f}".format(google_result[category]))

	for category in vader_result:
		vader_result[category] = float(sum(vader_result[category]))/len(vader_result[category])
		vader_result[category] = float("{0:.2f}".format(vader_result[category]))

	return {'google': google_result, 'vader': vader_result, 'afinn': afinn_result}

def writeJsonToFile(object, fileName):
	with open(fileName, 'w') as output:
		json.dump(object, output)
		output.close()
	print 'created file ' + fileName
	return True

# *********************** MAIN *********************

if __name__ == '__main__':

	print 'Starting Sentiment Analysis...'

	analysis_summary = {}

	inverse_docIdDict = json.load(open("indexes/inverse_docIdDict.json", "r"))

	for fileName in os.listdir(PATH):
		if fileName.endswith('.json'):
			file = open(PATH + '/' + fileName)
			documents = json.load(file)
			department = {}
			for document in documents:
				if SUB_URL_PATH in document['url']:
					docId = inverse_docIdDict[document['url']]
					document_str = ''
					department[docId] = {}
					document_str = '. '.join([document_str, document['title'], document['body']]).encode('ascii', 'ignore')

					# Save normalized resutls, between -5 and +5
					department[docId]['google'] = documentGoogleSA(document_str)
					department[docId]['vader'] = documentVaderSA(document_str)
					department[docId]['afinn'] = documentAfinnSA(document_str)

			if len(SUB_URL_PATH) > 0:
				fileName = SUB_URL_PATH + '.json'
			if len(department) > 0:
				writeJsonToFile(department, 'sentiment/' + fileName)
				analysis_summary[fileName.replace('.json','')] = deptScoreAvg(department)

	if len(analysis_summary) > 0:
		writeJsonToFile(analysis_summary, 'sentiment/' + 'summary_' + SUB_URL_PATH + '.json')
