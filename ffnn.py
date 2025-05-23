import numpy as np
import torch
import torch.nn as nn
from torch.nn import init
import torch.optim as optim
import math
import random
import os
import time
from tqdm import tqdm
import json
from argparse import ArgumentParser


unk = '<UNK>'
# Consult the PyTorch documentation for information on the functions used below:
# https://pytorch.org/docs/stable/torch.html
class FFNN(nn.Module):
    def __init__(self, input_dim, h):
        super(FFNN, self).__init__()
        self.h = h
        self.W1 = nn.Linear(input_dim, h)
        self.activation = nn.ReLU() # The rectified linear unit; one valid choice of activation function
        self.output_dim = 5
        self.W2 = nn.Linear(h, self.output_dim)

        self.softmax = nn.LogSoftmax() # The softmax function that converts vectors into probability distributions; computes log probabilities for computational benefits
        self.loss = nn.NLLLoss() # The cross-entropy/negative log likelihood loss taught in class

    def compute_Loss(self, predicted_vector, gold_label):
        return self.loss(predicted_vector, gold_label)

    def forward(self, input_vector):
        # [to fill] obtain first hidden layer representation
        h = self.activation(self.W1(input_vector))  # computes the first hidden layer representation
        
        # [to fill] obtain output layer representation
        z = self.W2(h)                              # computes the output layer representation
        
        # [to fill] obtain probability dist.
        predicted_vector = self.softmax(z)          # computes the probability distribution
        
        return predicted_vector


# Returns: 
# vocab = A set of strings corresponding to the vocabulary
def make_vocab(data):
    vocab = set()
    for document, _ in data:
        for word in document:
            vocab.add(word)
    return vocab 


# Returns:
# vocab = A set of strings corresponding to the vocabulary including <UNK>
# word2index = A dictionary mapping word/token to its index (a number in 0, ..., V - 1)
# index2word = A dictionary inverting the mapping of word2index
def make_indices(vocab):
    vocab_list = sorted(vocab)
    vocab_list.append(unk)
    word2index = {}
    index2word = {}
    for index, word in enumerate(vocab_list):
        word2index[word] = index 
        index2word[index] = word 
    vocab.add(unk)
    return vocab, word2index, index2word 


# Returns:
# vectorized_data = A list of pairs (vector representation of input, y)
def convert_to_vector_representation(data, word2index):
    vectorized_data = []
    for document, y in data:
        vector = torch.zeros(len(word2index)) 
        for word in document:
            index = word2index.get(word, word2index[unk])
            vector[index] += 1
        vectorized_data.append((document, vector, y))
    return vectorized_data



def load_data(train_data, val_data):
    with open(train_data) as training_f:
        training = json.load(training_f)
    with open(val_data) as valid_f:
        validation = json.load(valid_f)

    tra = []
    val = []
    for elt in training:
        tra.append((elt["text"].split(),int(elt["stars"]-1)))
    for elt in validation:
        val.append((elt["text"].split(),int(elt["stars"]-1)))

    return tra, val


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-hd", "--hidden_dim", type=int, required = True, help = "hidden_dim")
    parser.add_argument("-e", "--epochs", type=int, required = True, help = "num of epochs to train")
    parser.add_argument("--train_data", required = True, help = "path to training data")
    parser.add_argument("--val_data", required = True, help = "path to validation data")
    parser.add_argument("--test_data", default = "to fill", help = "path to test data")
    parser.add_argument('--do_train', action='store_true')
    args = parser.parse_args()

    # fix random seeds
    random.seed(42)
    torch.manual_seed(42)

    # load data
    print("========== Loading data ==========")
    train_data, valid_data = load_data(args.train_data, args.val_data) # X_data is a list of pairs (document, y); y in {0,1,2,3,4}
    vocab = make_vocab(train_data)
    vocab, word2index, index2word = make_indices(vocab)

    print("========== Vectorizing data ==========")
    train_data = convert_to_vector_representation(train_data, word2index)
    valid_data = convert_to_vector_representation(valid_data, word2index)
    

    model = FFNN(input_dim = len(vocab), h = args.hidden_dim)
    optimizer = optim.SGD(model.parameters(),lr=0.01, momentum=0.9)
    print("========== Training for {} epochs ==========".format(args.epochs))
    
    # Lists to store results for each epoch
    train_accuracies = []
    train_times = []
    val_accuracies = []
    val_times = []

    error_samples_train = []
    error_samples_val = []

    
    for epoch in range(args.epochs):
        model.train()
        optimizer.zero_grad()
        loss = None
        correct = 0
        total = 0
        start_time = time.time()
        print("Training started for epoch {}".format(epoch + 1))
        random.shuffle(train_data) # Good practice to shuffle order of training data
        minibatch_size = 16 
        N = len(train_data) 
        for minibatch_index in tqdm(range(N // minibatch_size)):
            optimizer.zero_grad()
            loss = None
            for example_index in range(minibatch_size):
                original_text, input_vector, gold_label = train_data[minibatch_index * minibatch_size + example_index]
                predicted_vector = model(input_vector)
                predicted_label = torch.argmax(predicted_vector)
                correct += int(predicted_label == gold_label)
                total += 1
                example_loss = model.compute_Loss(predicted_vector.view(1,-1), torch.tensor([gold_label]))
                if loss is None:
                    loss = example_loss
                else:
                    loss += example_loss
            loss = loss / minibatch_size
            loss.backward()
            optimizer.step()
            predicted_label = torch.argmax(predicted_vector)
            if predicted_label != gold_label:
                error_samples_train.append((" ".join(original_text), gold_label, predicted_label.item()))

        train_time = time.time() - start_time # time taken for training
        train_acc = correct / total # accuracy on training set
        train_accuracies.append(train_acc)
        train_times.append(train_time)
        print("Training completed for epoch {}".format(epoch + 1))
        print("Training accuracy for epoch {}: {}".format(epoch + 1, train_acc))
        print("Training time for this epoch: {}".format(train_time))


        loss = None
        correct = 0
        total = 0
        start_time = time.time()
        print("Validation started for epoch {}".format(epoch + 1))
        minibatch_size = 16 
        N = len(valid_data) 
        for minibatch_index in tqdm(range(N // minibatch_size)):
            optimizer.zero_grad()
            loss = None
            for example_index in range(minibatch_size):
                original_text, input_vector, gold_label = valid_data[minibatch_index * minibatch_size + example_index]
                predicted_vector = model(input_vector)
                predicted_label = torch.argmax(predicted_vector)
                correct += int(predicted_label == gold_label)
                total += 1
                example_loss = model.compute_Loss(predicted_vector.view(1,-1), torch.tensor([gold_label]))
                if loss is None:
                    loss = example_loss
                else:
                    loss += example_loss
            loss = loss / minibatch_size
            predicted_label = torch.argmax(predicted_vector)
            if predicted_label != gold_label:
                error_samples_val.append((" ".join(original_text), gold_label, predicted_label.item()))
        val_time = time.time() - start_time # time taken for validation
        val_acc = correct / total # accuracy on validation set
        val_accuracies.append(val_acc)
        val_times.append(val_time) 
        print("Validation completed for epoch {}".format(epoch + 1))
        print("Validation accuracy for epoch {}: {}".format(epoch + 1, val_acc))
        print("Validation time for this epoch: {}".format(val_time))

    # Write results to error_samples_ffnn.txt
    with open("error-samples/error_samples_ffnn.txt", "w") as f:
        f.write("Training Errors:\n")
        for vec, gold, pred in error_samples_train[:10]:  # just first 10 for brevity
            f.write(f"Text: {vec}\nGold: {gold}, Pred: {pred}\n\n")

        f.write("\nValidation Errors:\n")
        for vec, gold, pred in error_samples_val[:10]:
            f.write(f"Text: {vec}\nGold: {gold}, Pred: {pred}\n\n")

    # Write results to test_ffnn.out
    print("========== Writing results to test_ffnn.out ==========")
    with open("results/test_ffnn.out", "w") as f:
        f.write("Training Results:\n")
        f.write("Number of epochs: {}\n".format(args.epochs))
        f.write("Hidden dimension: {}\n".format(args.hidden_dim))
        f.write("Training data: {}\n".format(args.train_data))
        f.write("Validation data: {}\n".format(args.val_data))
        if args.test_data != "to fill":
            f.write("Test data: {}\n".format(args.test_data))
        f.write("\nPer-epoch Results:\n")
        for epoch in range(args.epochs):
            f.write("\nEpoch {}:\n".format(epoch + 1))
            f.write("Training accuracy: {}\n".format(train_accuracies[epoch]))
            f.write("Training time: {}\n".format(train_times[epoch]))
            f.write("Validation accuracy: {}\n".format(val_accuracies[epoch]))
            f.write("Validation time: {}\n".format(val_times[epoch]))
    