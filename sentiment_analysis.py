from google.cloud import language

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
    analyze_text_sentiment(text)