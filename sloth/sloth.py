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
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
kw_model = KeyBERT(SentenceTransformer("all-MiniLM-L6-v2"))
h2_tokenizer = AutoTokenizer.from_pretrained("transformer3/H2-keywordextractor")
h2_model = AutoModelForSeq2SeqLM.from_pretrained("transformer3/H2-keywordextractor")
random_card = random.choice([0, 1])
h2_model = h2_model.to(f'cuda:{random_card}')

# fasttext imports
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import fasttext
ft = fasttext.load_model('cc.en.300.bin')

from flask import Flask, request, jsonify

import random
import re
import logging

logging.basicConfig(filename='sloth.log', level=logging.INFO)

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

        log_line = f"Received POST request to /embed with text: '{text}'. Responding with embeddings."
        app.logger.info(log_line)

        return jsonify(response_data)


def sigmoid_scaling(data):
    values = np.array([item[1] for item in data])
    min_val = np.min(values)
    max_val = np.max(values)

    # Apply the logistic (sigmoid) function to scale the values
    scaled_values = 1 / (1 + np.exp(-(values - min_val) / (max_val - min_val)))

    scaled_data = [(item[0], scaled_values[i]) for i, item in enumerate(data)]

    return scaled_data

def add_or_update_keyword(keyword_list, new_keyword, new_weight):
    # Iterate through the list of tuples
    for i, (keyword, weight) in enumerate(keyword_list):
        if keyword == new_keyword:
            # If the keyword already exists, update its weight
            keyword_list[i] = (new_keyword, weight + new_weight)
            return keyword_list
    
    # If the keyword is not in the list, add it
    keyword_list.append((new_keyword, new_weight))
    return keyword_list

@app.route('/keyterms', methods=['POST'])
def keyterms():
    data = request.json  # Assuming the data is sent as JSON in the request body
    text = data.get('data').get('text')
    model = data.get('model')

    # loop over the text strings
    keyterms = []
    for _text in text:
        # handle short entries
        if len(_text) < 29:
            ordered_keywords = re.findall(r'\b\w{2,}\b', _text)
        else:
            # minilm extractor
            kw_keywords_2 = kw_model.extract_keywords([_text], keyphrase_ngram_range=(1, 2), top_n=15, highlight=False)
            kw_keywords_1 = kw_model.extract_keywords([_text], keyphrase_ngram_range=(1, 1), top_n=15, highlight=False)

            input_ids = h2_tokenizer(_text, return_tensors="pt").input_ids.to(f'cuda:{random_card}')
            # input_ids = h2_tokenizer(_text, return_tensors="pt").input_ids
            with torch.no_grad():
                output = h2_model.generate(input_ids, max_length=200)
            

            h2_keywords = h2_tokenizer.decode(output[0], skip_special_tokens=True).lower()

            # keyword list
            keywords = []

            # loop through singles (kw_keywords_1)
            for i, _kw_keyword_1 in enumerate(kw_keywords_1):
                for j, _kw_keyword_2 in enumerate(kw_keywords_2):
                    if _kw_keyword_1[0] in _kw_keyword_2[0] and _kw_keyword_2[0] not in [item[0] for item in keywords]:
                        keywords.append((_kw_keyword_2[0], _kw_keyword_1[1] + _kw_keyword_2[1]))

            # Split the input text by commas
            if "," in h2_keywords:
                items = h2_keywords.split(',')
                boost = 0.25
                multi = True
            else:
                items = h2_keywords.split(' ')
                boost = 0.1
                multi = False

            # update the list
            for item in items:
                item = item.strip().lower()
                keywords = add_or_update_keyword(keywords, item, boost)


            # Encode the phrases
            embeddings = [ft[keyword[0]] for keyword in keywords]

            # Convert phrase embeddings to numpy arrays
            embeddings = np.array(embeddings)

            # Calculate cosine similarity matrix
            cosine_sim_matrix = cosine_similarity(embeddings)

            for i, phrase1 in enumerate(keywords):
                max = 0
                max_keyterm = ""
                for j, phrase2 in enumerate(keywords):
                    similarity = cosine_sim_matrix[i, j]
                    if similarity != "1":
                        if similarity > max:
                            max = similarity
                            max_keyterm = phrase2[0]
                keywords = add_or_update_keyword(keywords, max_keyterm, similarity)

            scaled_keywords = sigmoid_scaling(keywords)

            sorted_keywords = sorted(scaled_keywords, key=lambda x: x[1], reverse=True)

            ordered_keywords = [item[0] for item in sorted_keywords]

        # end if
        keyterms.append(ordered_keywords)

    # Process the data and generate a response
    response_data = {
        "text": text,
        "keyterms": keyterms
    }

    log_line = f"Received POST request to /keyterms with text: '{text}'. Responding with keyterms: {keyterms}."
    app.logger.info(log_line)

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
