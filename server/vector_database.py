from openai import OpenAI
from scipy.spatial.distance import cosine


def access_collection(vector_database, collection_name):
    collections = vector_database.get_collections()
    if collection_name not in collections['status']['collections']:
        return vector_database.create_collection("TestPilot", dimension=1536, metric="cosine")
    else:
        return vector_database.collection("TestPilot")


def convert_text_to_embedding_vector(text):
    client = OpenAI()
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model='text-embedding-3-small').data[0].embedding


def insert_to_collection(collection, code, tests, code_coverage, code_embeddings):
    document = {
        "code": code,
        "tests": tests,
        "code_coverage": code_coverage,
        "$vector": code_embeddings,
    }
    collection.insert_one(document)


def cosine_similarity_to_known_tests(collection, code_query_vector):
    most_similar_item = collection.vector_find(code_query_vector, limit=1,
                                               fields=["code", "tests", "code_coverage", "$vector"])
    if len(most_similar_item) > 0:
        print(most_similar_item[0])
        most_similar_vector = most_similar_item[0]["$vector"]
        cosine_similarity_score = 1 - cosine(code_query_vector, most_similar_vector)
        print("My Cosine Similarity Score:", cosine_similarity_score)
        print("Cosine Similarity Score:", most_similar_item[0]["$similarity"])
        print(most_similar_item[0]["code_coverage"])
        return most_similar_item[0]["$similarity"], most_similar_item[0]
    else:
        return 0, 0
