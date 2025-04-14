import json

# Load and count entries in training.json
with open(r'c:\Users\eduza\OneDrive\Desktop\Desktop\Machine Learning\FFNN-RNN\FFNN-RNN-A2\training.json', 'r') as f:
    training_data = json.load(f)
    print(f"Number of entries in training.json: {len(training_data)}")

# Load and count entries in test.json
with open(r'c:\Users\eduza\OneDrive\Desktop\Desktop\Machine Learning\FFNN-RNN\FFNN-RNN-A2\test.json', 'r') as f:
    test_data = json.load(f)
    print(f"Number of entries in test.json: {len(test_data)}")

# Load and count entries in test.json
with open(r'c:\Users\eduza\OneDrive\Desktop\Desktop\Machine Learning\FFNN-RNN\FFNN-RNN-A2\validation.json', 'r') as f:
    validation_data = json.load(f)
    print(f"Number of entries in validation.json: {len(validation_data)}")