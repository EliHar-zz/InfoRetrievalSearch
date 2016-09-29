from nltk.corpus import stopwords

def removeStopwords(text):
        return [word for word in text if word not in stopwords.words('english')
