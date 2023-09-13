#!/bin/bash

echo "Enter the text (End by typing 'EOF' on a new line and pressing Enter):"

# Read multiline input until "EOF" is typed
input=""
while IFS= read -r line; do
    if [ "$line" == "EOF" ]; then
        break
    fi
    input="${input}${line}\n"
done


input=$(echo "$input" | tr -d "'\"")

# Use jq to format the input into a proper JSON payload
json_payload=$(echo "{}" | jq --arg text "$input" '.text = [$text]')

# Use the JSON payload in the curl command
curl -X POST \
-H "Content-Type: application/json" \
-d "$json_payload" \
"http://localhost:5000/keyterms"

