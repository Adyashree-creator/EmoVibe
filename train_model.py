import pandas as pd
import numpy as np
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import pickle
import os

print("Loading GoEmotions dataset from Hugging Face...")
dataset = load_dataset("go_emotions", split="train[:20%]")

label_mapping = {
    "happy": [0, 1, 4, 5, 15, 17, 20, 21, 23],
    "sad": [9, 10, 16, 24, 25],
    "anxious": [6, 12, 14, 19],
    "angry": [2, 3, 11],
    "neutral": [7, 22, 26, 27],
    "romantic": [8, 18],
    "energetic": [13],
    "lazy": [] # We will let 'neutral' often catch lazy, but keep it in our list
}

reverse_mapping = {}
for category, ids in label_mapping.items():
    for label_id in ids:
        reverse_mapping[label_id] = category

print("Preprocessing data...")
texts = []
labels = []

# Add rich synthetic journal-style data to teach the model real human writing
synthetic_data = [
    # HAPPY
    ("I am so happy today", "happy"),
    ("Today was the best day ever", "happy"),
    ("I got great marks in my test today", "happy"),
    ("I aced all my questions today, feeling amazing", "happy"),
    ("Everything is going so well right now", "happy"),
    ("I feel like smiling for no reason", "happy"),
    ("Life feels so good today", "happy"),
    ("I passed my exam! I am on top of the world", "happy"),
    ("Had the most wonderful day, I am beaming with joy", "happy"),
    ("I woke up feeling so positive and bright today", "happy"),
    ("My parents were so proud of me today", "happy"),
    ("I succeeded at something I worked really hard for", "happy"),
    ("Today felt like sunshine from start to finish", "happy"),
    
    # ROMANTIC
    ("I went on a date today", "romantic"),
    ("I had coffee with my boyfriend today", "romantic"),
    ("Spent a lovely evening with my long-term boyfriend", "romantic"),
    ("I miss my partner so much right now", "romantic"),
    ("I am falling so deeply in love", "romantic"),
    ("We held hands and walked in the park", "romantic"),
    ("My boyfriend surprised me with flowers today", "romantic"),
    ("I feel so loved and cherished by my partner", "romantic"),
    ("We watched the sunset together, it was magical", "romantic"),
    ("I love spending time with my special person", "romantic"),
    ("My girlfriend texted me good morning and it made my day", "romantic"),
    ("I am so deeply in love, my heart is full", "romantic"),
    ("We had a cozy dinner and talked all night", "romantic"),
    ("I keep thinking about my boyfriend all day", "romantic"),
    ("We went on a long drive and listened to music together", "romantic"),

    # SAD
    ("I am feeling really sad today", "sad"),
    ("I cried all night and don't know why", "sad"),
    ("Everything feels heavy and difficult right now", "sad"),
    ("I feel like nobody understands me", "sad"),
    ("I miss someone who is no longer in my life", "sad"),
    ("I failed at something I really cared about", "sad"),
    ("Today was really rough and hard", "sad"),
    ("I feel lost and empty inside", "sad"),
    ("Nothing feels right lately", "sad"),
    ("I am going through a tough time and feel alone", "sad"),
    ("I broke down today and could not stop crying", "sad"),
    ("I feel like I am not good enough", "sad"),

    # ANXIOUS
    ("I am feeling really anxious today", "anxious"),
    ("I have so many deadlines and I feel overwhelmed", "anxious"),
    ("My heart is racing and I feel nervous", "anxious"),
    ("I am scared about what happens next", "anxious"),
    ("I can not stop overthinking everything", "anxious"),
    ("I have an exam tomorrow and I am panicking", "anxious"),
    ("I feel restless and I do not know why", "anxious"),
    ("I am stressed about my future", "anxious"),
    ("Everything feels uncertain and it is making me uneasy", "anxious"),
    ("I keep worrying about things I cannot control", "anxious"),
    ("I have a big presentation and I am terrified", "anxious"),

    # ANGRY
    ("I am so angry right now", "angry"),
    ("I feel furious and I cannot calm down", "angry"),
    ("Someone hurt me and I am really mad about it", "angry"),
    ("I hate how this situation is going", "angry"),
    ("This is so unfair and I am fuming", "angry"),
    ("I snapped at everyone today because I was so frustrated", "angry"),
    ("I cannot believe what happened, I am livid", "angry"),
    ("I am done putting up with this", "angry"),
    ("People keep disrespecting me and I am fed up", "angry"),
    ("I feel like screaming right now", "angry"),

    # ENERGETIC
    ("I want to dance today", "energetic"),
    ("I feel so alive and full of energy", "energetic"),
    ("I am pumped up and ready to take on the world", "energetic"),
    ("Let's go out and do something wild and fun", "energetic"),
    ("I feel like I can run a marathon right now", "energetic"),
    ("I worked out today and feel incredible", "energetic"),
    ("I am buzzing with excitement today", "energetic"),
    ("I feel unstoppable today", "energetic"),
    ("Today I want to do everything at once", "energetic"),
    ("I have so much energy I don't know what to do with it", "energetic"),
    ("I want to jump around and celebrate", "energetic"),
    ("I am so hyper and excited right now", "energetic"),
    ("I feel like dancing and singing out loud", "energetic"),

    # LAZY
    ("I just want to lay in bed all day", "lazy"),
    ("I am feeling so lazy today", "lazy"),
    ("I don't want to do any work, just watch movies", "lazy"),
    ("Feeling sleepy and unproductive", "lazy"),
    ("I have no motivation to do anything today", "lazy"),
    ("I just want to lie down and do nothing", "lazy"),
    ("I feel like a couch potato today", "lazy"),
    ("I can not bring myself to start anything today", "lazy"),
    ("Today is a do-nothing kind of day", "lazy"),
    ("I feel so sluggish and slow", "lazy"),

    # NEUTRAL
    ("I had a regular, ordinary day today", "neutral"),
    ("Nothing special happened, just a normal day", "neutral"),
    ("I feel okay, not great not bad", "neutral"),
    ("Today was fine, nothing much to report", "neutral"),
    ("I went to work, came back, made dinner", "neutral"),
    ("I feel calm and unbothered today", "neutral"),
    ("Life is just going on as usual", "neutral"),
    ("I did some chores and watched some TV", "neutral"),
    ("It was a quiet and uneventful day", "neutral"),
    ("I feel balanced and steady today", "neutral"),
]

for text, label in synthetic_data:
    texts.append(text)
    labels.append(label)


for item in dataset:
    text = item['text']
    if len(item['labels']) > 0:
        first_label_id = item['labels'][0]
        if first_label_id in reverse_mapping:
            texts.append(text)
            labels.append(reverse_mapping[first_label_id])

print(f"Prepared {len(texts)} text samples.")

print("Training the Machine Learning model...")
pipeline = Pipeline([
    ('vectorizer', TfidfVectorizer(stop_words='english', ngram_range=(1,2))),
    ('classifier', LogisticRegression(class_weight='balanced', max_iter=1000))
])

pipeline.fit(texts, labels)

model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
with open(model_path, "wb") as f:
    pickle.dump(pipeline, f)

print(f"Model successfully trained and saved to {model_path}!")
