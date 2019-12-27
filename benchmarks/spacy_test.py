import spacy
import os
from tqdm import *
import argparse
import time

def get_pos_examples(data_dir):
    file_path = os.path.join(data_dir, "{}.txt".format("dev"))
    examples= []
    with open(file_path, encoding="utf-8") as f:
        words = []
        labels = []
        for line in f.readlines():
            if line == "\n":
                if words:
                   examples.append([words, labels])
                   words = []
                   labels = []
            elif line.startswith("#"):
                pass
            else:
                line = line.strip("\n").split("\t")
                words.append(line[1])
                labels.append(line[3])
    
    if words:
        examples.append([words, labels])
    return examples
    
def get_ner_examples(data_dir):
    file_path = os.path.join(data_dir, "{}.txt".format("dev"))
    examples = []
    with open(file_path, encoding="utf-8") as f:
        words = []
        labels = []
        for line in f:
            if line.startswith("-DOCSTART-") or line == "" or line == "\n":
                if words:
                    examples.append([words, labels])
                words = []
                labels = []
            else:
                splits = line.split(" ")
                words.append(splits[0])
                if len(splits) > 1 :
                    labels.append(splits[-1].replace("\n", ""))
                else:
                    labels.append("O")
        if words:
            examples.append([words, labels])
            words = []
            labels = []
    return examples

def evaluate_pos(args, model):
    pos_examples = get_pos_examples(args.pos_data)
    print(len(pos_examples))

    pred_pos_labels = []
    true_labels = []
    total_words = []
    total_tokens = []
    # inferenece
    start = time.time()
    pos_label_list = [
        "ADJ", "ADP", "ADV", "AUX", "CCONJ", 
        "DET", "INTJ", "NOUN", "NUM", "PART",
        "PRON", "PROPN", "PUNCT", "SCONJ", "SYM",
        "VERB", "X"
    ]

    # Just use the label of the first sub-word
    total_pred_labels = []
    for exp in tqdm(pos_examples):

        words = exp[0]
        labels = exp[1]
        
        idxs = []
        text = ""
        for word in words:
            idxs += [len(text)]
            text += word + " "
        
        tokens = model(text)
        pred_pos_labels = []
        for tk in tokens:
            if tk.idx in idxs:
                pred_pos_labels.append(tk.pos_)
        # for word in words:
        #     tokens = model(word)
        #     total_words.append(word)
        #     total_tokens.append(tokens[0].text)
        #     pred_label = tokens[0].pos_
        #     if pred_label not in pos_label_list: 
        #         pred_label = "X"
        #         print(pred_label)
        #     pred_pos_labels.append(pred_label)
        
        assert len(pred_pos_labels) == len(labels)
        total_pred_labels.extend(pred_pos_labels)
       
    end = time.time()
    for exp in pos_examples:
        true_labels.extend(exp[1])

    ## evaluate
    total = len(total_pred_labels)
    hit = 0
    for pred, true_label in zip(tqdm(total_pred_labels), tqdm(true_labels)):
        if pred == true_label:
            hit += 1
    

    print("sents per second", total*1.0000000/(end - start))
    print("pos tag time cost", end - start)
    print("pos acc", hit*1.0000000 / total)

    # write the prediction for checking
    # with open("pred_pos.txt", "w+", encoding="utf-8") as f:
    #     for word, tok, pred, true in zip(total_words, total_tokens, pred_pos_labels, true_labels):
    #         line = word + "\t" + tok + "\t" + pred + "\t" + true
    #         f.write(line + "\n") 

def evaluate_ner(args, model):
    label_list = ["PER", "ORG", "LOC"]
    ner_examples = get_ner_examples(args.ner_data)

    total_pred_labels = []
    true_labels = []
    start = time.time()
    for exp in tqdm(ner_examples):

        words = exp[0]
        labels = exp[1]

        idxs = []
        text = ""
        for word in words:
            idxs += [len(text)]
            text += word + " "
        
        tokens = model(text)
        pred_ner_labels = []
        for tk in tokens:
            if tk.idx in idxs:
                pred_label = tk.ent_type_
                if len(pred_label) == 0:
                    pred_ner_labels.append("O")
                elif pred_label not in label_list:
                    pred_ner_labels.append("MISC")
                elif pred_label == "PERSON":
                    pred_ner_labels.append("PER")
                else:
                    pred_ner_labels.append(pred_label)

        assert len(pred_ner_labels) == len(labels)
        total_pred_labels.extend(pred_ner_labels)
    end = time.time()

    for exp in ner_examples:
        labs = []
        for x in exp[1]:
            if "-" in x:
                labs.append(x.split("-")[1])
            else:
                labs.append(x)
        true_labels.extend(labs)
    
    ## evaluate
    total = len(total_pred_labels)
    hit = 0
    for pred, true_label in zip(tqdm(total_pred_labels), tqdm(true_labels)):
        if pred == true_label:
            hit += 1
    
    print("sents per second", total*1.0000000/(end - start))
    print("ner tag time cost", end - start)
    print("ner acc", hit*1.0000000 / total)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pos_data", type=str, default="")
    parser.add_argument("--ner_data", type=str, default="")
    parser.add_argument("--model_type", type=str, default="")

    args = parser.parse_args()

    nlp = spacy.load(args.model_type)
    
    if len(args.pos_data) > 0:
        evaluate_pos(args, nlp)

    if len(args.ner_data) > 0:
        evaluate_ner(args, nlp)
    # ner_examples = get_ner_examples(args.ner_data)

    # print(len(ner_examples))

    