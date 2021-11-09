# -*- coding: utf-8 -*-
"""SVM Web Data Prossecing system

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11uIemBWcSWci3mNEG3Vuaywx2iZB0vVn
"""

##importing the packages
import sklearn
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import svm
from sklearn.metrics import accuracy_score

## Importing Data
df_train= pd.read_csv("/content/drive/MyDrive/data files/train.csv")
df_test = pd.read_csv("/content/drive/MyDrive/data files/staycation.csv", names=['id', 'tweet'])

import time 
class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""

class Timer:
  def __init__(self):
        self._start_time = None
  def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()
  def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")

df_train

df_test

!pip install tweet_preprocessor

t=Timer()###defining the timer

# remove special characters using the regular expression library
import re

#set up punctuations we want to be replaced
REPLACE_NO_SPACE = re.compile("(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\|)|(\()|(\))|(\[)|(\])|(\%)|(\$)|(\>)|(\<)|(\{)|(\})")
REPLACE_WITH_SPACE = re.compile("(<br\s/><br\s/?)|(-)|(/)|(:).")
import preprocessor as p

# custum function to clean the dataset (combining tweet_preprocessor and reguar expression)
def clean_tweets(df):
  tempArr = []
  for line in df:
    # send to tweet_processor
    tmpL = p.clean(line)
    # remove puctuation
    tmpL = REPLACE_NO_SPACE.sub("", tmpL.lower()) # convert all tweets to lower cases
    tmpL = REPLACE_WITH_SPACE.sub(" ", tmpL)
    tempArr.append(tmpL)
  return tempArr

# clean training data
train_tweet = clean_tweets(df_train.tweet)
train_tweet = pd.DataFrame(train_tweet)
# append cleaned tweets to the training data
df_train["clean_tweet"] = train_tweet

# compare the cleaned and uncleaned tweets
df_train.head(10)
# clean the test data and append the cleaned tweets to the test data
test_tweet = clean_tweets(df_test.tweet)
test_tweet = pd.DataFrame(test_tweet)
# append cleaned tweets to the training data
df_test["clean_tweet"] = test_tweet

# # compare the cleaned and uncleaned tweets
# df_test.tail()

# extract the labels from the train data
train_labels = df_train.label.values

# use 70% for the training and 30% for the test
x_train, x_test, y_train, y_test = train_test_split(df_train.clean_tweet.values, train_labels, stratify=train_labels,  random_state=1,test_size=0.3, shuffle=True)

t.start()
#Intialize the Count Vectorizer
vectorizer = CountVectorizer(binary=True, stop_words='english')

# Create a dictionary for all existing words in the training and test set
vectorizer.fit(list(x_train) + list(x_test)+list(df_test.clean_tweet))

# transform tweets to vector (counting)
x_train_vec = vectorizer.transform(x_train)
x_test_vec = vectorizer.transform(x_test)
test_vec=vectorizer.transform(df_test.clean_tweet)

# classify using support vector classifier
svm = svm.SVC(kernel = 'linear', probability=True)

# fit the SVC model based on the given training data
prob = svm.fit(x_train_vec, y_train).predict_proba(x_test_vec)
t.stop()

#perform classification and prediction on samples in x_test
y_pred_svm = svm.predict(x_test_vec)
print("Accuracy score for SVC is: ", accuracy_score(y_test, y_pred_svm) * 100,'%')

t.start()
test_prediction= svm.predict(test_vec)
df_test['predict']=test_prediction
t.stop()
df_test

df_test.groupby('predict').count()[['clean_tweet']]/df_test['id'].count()

pd.set_option('display.max_colwidth', None)
RS_arg=2

df_test[df_test['predict']==1].sample(n=10,random_state=RS_arg)

df_test[df_test['predict']==0].sample(n=10,random_state=RS_arg)