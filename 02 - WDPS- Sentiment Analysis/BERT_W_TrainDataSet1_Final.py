

import pandas as pd
import numpy as np
import re
from bert_serving.client import BertClient
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from datetime import datetime



output_path=r'D:\Box\Box\2020 Master\VU\Study\P2 Web Data Processing Systems\Assignment\Assignment 2\Hate Speech\Result\\'


## Loading Data Set with **Binary Labels**
# load training data
train = pd.read_csv(r'D:\Box\Box\2020 Master\VU\Study\P2 Web Data Processing Systems\Assignment\Assignment 2\Hate Speech\DataSet\train.csv', encoding='iso-8859-1')

## Change the tag here, and all path will change accordingly
test1Name='#TheCrown'
test2Name='#TheQueensGambit'
test3Name='F1'
test4Name='StarWars'
test5Name='staycation'

##Note: uncomment the test2-test5 if needed

#load test data
test1=pd.read_csv(r'D:\Box\Box\2020 Master\VU\Study\P2 Web Data Processing Systems\Assignment\Assignment 2\Analysis\Data\\'+ test1Name+'.csv', encoding='iso-8859-1')
# test2=pd.read_csv(r'D:\Box\Box\2020 Master\VU\Study\P2 Web Data Processing Systems\Assignment\Assignment 2\Analysis\Data\\'+ test2Name+'.csv', encoding='iso-8859-1')
# test3=pd.read_csv(r'D:\Box\Box\2020 Master\VU\Study\P2 Web Data Processing Systems\Assignment\Assignment 2\Analysis\Data\\'+ test3Name+'.csv', encoding='iso-8859-1')
# test4=pd.read_csv(r'D:\Box\Box\2020 Master\VU\Study\P2 Web Data Processing Systems\Assignment\Assignment 2\Analysis\Data\\'+ test4Name+'.csv', encoding='iso-8859-1')
# test5=pd.read_csv(r'D:\Box\Box\2020 Master\VU\Study\P2 Web Data Processing Systems\Assignment\Assignment 2\Analysis\Data\\'+ test5Name+'.csv', encoding='iso-8859-1')



print(train.shape)
print(test1Name,test1.shape)
# print(test2Name,test2.shape)
# print(test3Name,test3.shape)
# print(test4Name,test4.shape)
# print(test5Name,test5.shape)





## version 2 of text cleaning
#set up punctuations we want to be replaced
REPLACE_NO_SPACE = re.compile("(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\|)|(\()|(\))|(\[)|(\])|(\%)|(\$)|(\>)|(\<)|(\{)|(\})")
REPLACE_WITH_SPACE = re.compile("(<br\s/><br\s/?)|(-)|(/)|(:).")


# custum function to clean the dataset (combining tweet_preprocessor and regular expression)
def clean_tweets2(df):
    tempArr = []
    for line in df:
        tmpL=line
        # remove puctuation
        tmpL = REPLACE_NO_SPACE.sub("", tmpL.lower()) # convert all tweets to lower cases
        tmpL = REPLACE_WITH_SPACE.sub(" ", tmpL)
        if tmpL=='': ## try to eliminate empty string
            tmpL='XXX'
        tempArr.append(tmpL)
    return tempArr

# #clean training data
train_tweet = clean_tweets2(train.tweet)
train_tweet = pd.DataFrame(train_tweet)
# # append cleaned tweets to the training data
train["clean_text"] = train_tweet

# # append cleaned tweets back to the test data

test1["clean_text"] = pd.DataFrame(clean_tweets2(test1.tweet))
# test2["clean_text"] = pd.DataFrame(clean_tweets2(test2.tweet))
# test3["clean_text"] = pd.DataFrame(clean_tweets2(test3.tweet))
# test4["clean_text"] = pd.DataFrame(clean_tweets2(test4.tweet))
# test5["clean_text"] = pd.DataFrame(clean_tweets2(test5.tweet))



# split into training and validation sets
train_label=train.label
X_tr, X_val, y_tr, y_val = train_test_split(train.clean_text, train_label, test_size=0.1, random_state=42)



# get the embedding for train,test,prediction sets
print('start BERT Vectorize',datetime.now())
T_Start_BERT_Vectorizing=datetime.now()
bc = BertClient() ## need to start the 'bert as service' server first
X_tr_bert = bc.encode(X_tr.tolist())
X_val_bert = bc.encode(X_val.tolist())
TEST1_val_bert = bc.encode(test1.clean_text.tolist())
# TEST2_val_bert = bc.encode(test2.clean_text.tolist())
# TEST3_val_bert = bc.encode(test3.clean_text.tolist())
# TEST4_val_bert = bc.encode(test4.clean_text.tolist())
# TEST5_val_bert = bc.encode(test5.clean_text.tolist())




## Classification
print('start model trainging',datetime.now())
T_Start_Model_Training=datetime.now()
## LR model
model_bert = LogisticRegression(max_iter=10000,C=0.1)
# train
model_bert = model_bert.fit(X_tr_bert, y_tr)


##Checking Accuracy
print('start model accuracy',datetime.now())
T_Start_Model_Accuracy=datetime.now()
pred_bert = model_bert.predict(X_val_bert)
print(accuracy_score(y_val, pred_bert))
print('end model accuracy',datetime.now())
T_End_Model_Accuracy=datetime.now()

#predict with new dataset
test1['prediction']=model_bert.predict(TEST1_val_bert)
T_test1_predict=datetime.now()
# test2['prediction']=model_bert.predict(TEST2_val_bert)
# T_test2_predict=datetime.now()
# test3['prediction']=model_bert.predict(TEST3_val_bert)
# T_test3_predict=datetime.now()
# test4['prediction']=model_bert.predict(TEST4_val_bert)
# T_test4_predict=datetime.now()
# test5['prediction']=model_bert.predict(TEST5_val_bert)
# T_test5_predict=datetime.now()


def summary_run(test,testName,inTime,OutTime):
    summary=test.groupby('prediction')
    no_prediction = test['prediction'].count()
    final_out_path=output_path+'bert_'+testName+'.csv'
    PredTime=(OutTime-inTime).total_seconds()
    print(testName,'Prediction Time:',PredTime)
    print(summary['tweet'].count() / no_prediction * 100)
    # test.to_csv(final_out_path,header=True,index=None) ## for exporting result

##Run Time Statistics
TD_Model_Training=(T_Start_Model_Accuracy-T_Start_BERT_Vectorizing).total_seconds()
TD_Model_Accuracy=(T_End_Model_Accuracy-T_Start_Model_Accuracy).total_seconds()
print('Model Training Time:',TD_Model_Training)
print('Model Accuracy Time:',TD_Model_Accuracy)

summary_run(test1,test1Name,T_End_Model_Accuracy,T_test1_predict)
# summary_run(test2,test2Name,T_test1_predict,T_test2_predict)
# summary_run(test3,test3Name,T_test2_predict,T_test3_predict)
# summary_run(test4,test4Name,T_test3_predict,T_test4_predict)
# summary_run(test5,test5Name,T_test4_predict,T_test5_predict)