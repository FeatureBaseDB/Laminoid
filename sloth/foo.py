from transformers import pipeline
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

tokenizer = AutoTokenizer.from_pretrained("transformer3/H2-keywordextractor")
model = AutoModelForSeq2SeqLM.from_pretrained("transformer3/H2-keywordextractor")
sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(sentence_model)

text = input("enter text: ")
keywords_with_scores = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), top_n=15, highlight=False)
print(keywords_with_scores)        


keywords_with_scores = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), top_n=15, highlight=False)
print(keywords_with_scores)        

input_ids = tokenizer(text, return_tensors="pt").input_ids

with torch.no_grad():
    output = model.generate(input_ids, max_length=200)

generated_keywords = tokenizer.decode(output[0], skip_special_tokens=True)
print(generated_keywords)
