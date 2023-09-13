import fasttext

# Create and train a FastText classifier
# Replace 'train.txt' with your training data file
model = fasttext.train_supervised(input="train.txt")

# Test the trained model
# Replace 'test.txt' with your test data file
result = model.test("test.txt")

# Print evaluation metrics
print(f"Precision: {result.precision}")
print(f"Recall: {result.recall}")
print(f"F1 Score: {result.f1score}")

# Predict the label for a new text
text_to_predict = "This is a sample text to classify."
predicted_label = model.predict(text_to_predict)
print(f"Predicted label: {predicted_label[0][0]}")
