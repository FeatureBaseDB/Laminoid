# load embedding models
from InstructorEmbedding import INSTRUCTOR
xl = INSTRUCTOR('hkunlp/instructor-xl')
large = INSTRUCTOR('hkunlp/instructor-large')

# transformers, keybert, torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSeq2SeqLM
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
import torch

# load bert/h2 models
kw_model = KeyBERT(SentenceTransformer("all-MiniLM-L6-v2"))
h2_tokenizer = AutoTokenizer.from_pretrained("transformer3/H2-keywordextractor")
h2_model = AutoModelForSeq2SeqLM.from_pretrained("transformer3/H2-keywordextractor")

# fasttext imports
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import fasttext
ft = fasttext.load_model('cc.en.300.bin')

from flask import Flask, request, jsonify

import random
import re

app = Flask(__name__)

@app.route('/embed', methods=['POST'])
def embed():
    if request.method == 'POST':
        data = request.json  # Assuming the data is sent as JSON in the request body
        text = data.get('text')
        model = data.get('model')

        if model == "instructor-xl":
            embeddings = xl.encode(data.get('text')).tolist()
        else:
            embeddings = large.encode(data.get('text')).tolist()

        # Process the data and generate a response
        response_data = {
            "text": text,
            "embeddings": embeddings
        }

        return jsonify(response_data)


def consolidate_keywords(keywords_1, keywords_2, keywords_3):
    # Convert each list to dictionaries for easy access
    dict_keywords_1 = {k[0]: k[1] for k in keywords_1}
    dict_keywords_2 = {k[0]: k[1] for k in keywords_2}
    dict_keywords_3 = {k[0]: k[1] for k in keywords_3}

    # Increase weight of entities in keywords_1 by checking association in keywords_2
    for entity, weight in dict_keywords_1.items():
        entity_parts = entity.split()
        for key in dict_keywords_2:
            if all(part in key for part in entity_parts):
                dict_keywords_1[entity] += dict_keywords_2[key]

    # Increase weight of words in keywords_3 by association in keywords_2
    for word, weight in dict_keywords_3.items():
        for key in dict_keywords_2:
            if word in key.split():
                dict_keywords_3[word] += dict_keywords_2[key]

    # Create a consolidated dictionary, ensuring we're only using numeric values
    consolidated = {}
    for d in [dict_keywords_1, dict_keywords_2, dict_keywords_3]:
        for key, value in d.items():
            if isinstance(value, (float, int)):  # Ensure the value is numeric
                consolidated[key] = consolidated.get(key, 0) + value

    # Sort the consolidated list by weight
    consolidated_list = sorted(consolidated.items(), key=lambda x: x[1], reverse=True)

    return consolidated_list


@app.route('/keyterms', methods=['POST'])
def keyterms():
    if request.method == 'POST':
        data = request.json  # Assuming the data is sent as JSON in the request body
        text = data.get('text')
        model = data.get('model')

        if len(text[0]) < 29:
            words = re.findall(r'\b\w{2,}\b', text[0])

            response_data = {
                "text": text,
                "keyterms": words
            }

            return jsonify(response_data)
        
        # minilm extractor
        keywords_2 = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), top_n=15, highlight=False)
        keywords_1 = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), top_n=15, highlight=False)

        # h2 extractor
        keywords_3 = []
        for _text in text:
            _keywords = []
            input_ids = h2_tokenizer(_text, return_tensors="pt").input_ids
            with torch.no_grad():
                output = h2_model.generate(input_ids, max_length=200)
            
            keywords = h2_tokenizer.decode(output[0], skip_special_tokens=True)
            _keywords = []

            for word in keywords.split(", "):
                word = word.strip().lower()
                if word in _text.lower():
                    weight = 0.50
                else:
                    weight = 0.25

                word_found = False
                for _x in _keywords:
                    if word in _x[0]:
                        word_found = True
                        break
                if not word_found:
                    _keywords.append((word, weight))

            keywords_3.append(_keywords)

        # Example usage
        final_keywords = consolidate_keywords(keywords_1, keywords_2, keywords_3)

        phrases = []
        for final_keyword in final_keywords:
            phrases.append(final_keyword[0])


        # Encode the phrases
        phrase_embeddings = [ft[phrase] for phrase in phrases]

        # Convert phrase embeddings to numpy arrays
        phrase_embeddings = np.array(phrase_embeddings)

        # Calculate cosine similarity matrix
        cosine_sim_matrix = cosine_similarity(phrase_embeddings)

        # Print the cosine similarity matrix
        keyterms = []

        for i, phrase1 in enumerate(phrases):
            max = 0
            keyterm = ""
            for j, phrase2 in enumerate(phrases):
                similarity = cosine_sim_matrix[i, j]
                if similarity != "1":
                    if similarity > max:
                        max = similarity
                        keyterm = phrase2
            if keyterm not in keyterms:
                keyterms.append(keyterm)

        # add random keyterms from keywords_3
        selected_words = random.sample(keywords_3, len(keywords_3))

        for _selection in selected_words:
            for _word in _selection:
                if _word not in keyterms:
                    keyterms.append(_word[0])

        _keyterms = []
        for keyterm in keyterms:
            if len(keyterm) > 2:
                _keyterms.append(keyterm)

        # Process the data and generate a response
        response_data = {
            "text": text,
            "keyterms": keyterms
        }

        return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)