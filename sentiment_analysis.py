from google.cloud import language
import threading
import logging
import requests
from pprint import pprint

def analyze_text_sentiment(text):
    client = language.LanguageServiceClient()
    document = language.Document(content=text, type_=language.Document.Type.PLAIN_TEXT)

    response = client.analyze_sentiment(document=document)

    sentiment = response.document_sentiment
    results = dict(
        text=text,
        score=sentiment.score,
        magnitude=sentiment.magnitude,
    )
    # for k, v in results.items():
    #     print(f"{k:10}: {v}")
    return results

# Temporary solution to call the Natural Language API from flask
def analyze_text_sentiment_workaround(text):
    API_KEY = "AIzaSyCUDeQMDkbAkdKbKm9xNbANcxdr0iphfRI"
    doc = {'type': 1, 'language': 'en', 'content': text}
    d = {'document': doc, 'encodingType': 'UTF32'}
    url = 'https://language.googleapis.com/v1beta2/documents:analyzeSentiment?key=' + API_KEY
    response = requests.post(url, json=d, timeout=10.0).json()
    
    sentiment = response['documentSentiment']
    results = dict(
        text=text,
        score=sentiment['score'],
        magnitude=sentiment['magnitude']
    )
    
    return results

def analyze_text_sentiment_batch(texts):
    n = len(texts)
    lock = threading.Lock()
    res = [{}] * n

    def thread_function(text, idx):
        results = analyze_text_sentiment_workaround(text)
        with lock:
            res[idx] = results
    
    threads = list()
    for index in range(n):
        logging.info("Main    : create and start thread %d.", index)
        x = threading.Thread(target=thread_function, args=(texts[index], index,))
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        logging.info("Main    : before joining thread %d.", index)
        thread.join()
        logging.info("Main    : thread %d done", index)

    return res


def classify_text(text):
    client = language.LanguageServiceClient()
    document = language.Document(content=text, type_=language.Document.Type.PLAIN_TEXT)

    response = client.classify_text(document=document)

    for category in response.categories:
        print("=" * 80)
        print(f"category  : {category.name}")
        print(f"confidence: {category.confidence:.0%}")

if __name__ == '__main__':
    text = "Bharath is an amazing person"
    analysis = analyze_text_sentiment_workaround(text)
    print(analysis)