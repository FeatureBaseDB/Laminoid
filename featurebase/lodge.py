from database import featurebase_query
import json

sql = "SELECT question, answer, page_id FROM doc_questions;"

results = featurebase_query({"sql": sql}).get('results')

"""
  {
    "id": "identity_0",
    "conversations": [
      {
        "from": "human",
        "value": "Who are you?"
      },
      {
        "from": "gpt",
        "value": "I am Vicuna, a language model trained by researchers from Large Model Systems Organization (LMSYS)."
      },
      {
        "from": "human",
        "value": "What can you do?"
      },
      {
        "from": "gpt",
        "value": "I can chat with you."
      }
    ]
  },
"""
data = []
conversations = []
prev_id = ""
for result in results:
    if prev_id != result.get('page_id') and prev_id != "":
        data.append({"conversations": conversations, "id": result.get('page_id')})

        # reset conversations and update id
        conversations = []
        prev_id = result.get('page_id')
        conversations.append({"from": "human", "value": result.get('question')})
        conversations.append({"from": "gpt", "value": result.get('answer')})
    else:
        conversations.append({"from": "human", "value": result.get('question')})
        conversations.append({"from": "gpt", "value": result.get('answer')})

    prev_id = result.get('page_id')

print(json.dumps(data))