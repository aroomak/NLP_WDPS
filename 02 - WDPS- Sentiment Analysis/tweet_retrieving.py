# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 00:18:45 2020

@author: Aram
"""

#pip install tweepy
from tweepy import *
 
import csv
#import preprocessor as p
import tweepy as tw

def main():
    ## Twitter Account Details
    consumer_key = "BasHqeRl7Htiga28Xp3CyrL2M"
    consumer_secret ="BTv9RxNrIWvQNAcymKVsfBDTy1jBES3Zx6xSkDiOc1fbeX4rzN"
    access_key= "1193807086498398210-OuAkatAw3OOBwkEyAps4nS76LF5S49"
    access_secret = "dPjxGj9afIbCuElzS4AiyI0e1JH45a92mQHDNWaNMxfuS"
    ## Establishing Connection with tweepy
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tw.API(auth,wait_on_rate_limit=True)
    

    search_words = ["#BLM", "#Brexit", "#TheCrown", "#lockdown", "#TheQueensGambit", "F1", "staycation", "StarWars"
                    ,"#ProudBoys", "#ANTIFA", "#2020election", "#China", "#Refugees", "#China #Uyghur"
                    ,"#China #Corona","#China #COVID19","#China #Lockdown"] 
    date_since = ["2020-12-14"] 
    
    
    for hashtag in search_words: ### Change the path C:/... etc. 
        csvFile = open('C:/Users/mehme/OneDrive/Desktop/tweets/'+hashtag+'.csv', 'a',newline="")
        csvWriter = csv.writer(csvFile)
        for date in date_since:
#            print(date)
            tweets = tw.Cursor(api.search,
                      q=hashtag,
                      lang="en",
                      since_id=date, tweet_mode="extended").items(1000)
            
            for tweet in tweets:
#                print(tweet.created_at, tweet.full_text)
                csvWriter.writerow([tweet.created_at, tweet.full_text.encode('utf-8')])
        csvFile.close()
    
if __name__== "__main__":
    main()