import os
import json
import tweepy
import twitter
import TwitBot
import time
from time import sleep


twitter_screen_names = ["screen_name_1","screen_name_2"]

for twitter_screen_name in twitter_screen_names:

    #TwitBot.get_friends(twitter_screen_name)
    #TwitBot.optimal_unfollow_time(cut_off_datetime = '2018-08-22 12:00:00')
    #print(TwitBot.most_liked(30))
    TwitBot.followers_record(*TwitBot.get_friends(twitter_screen_name))
    TwitBot.fav_off_keyword(*TwitBot.get_friends(twitter_screen_name))
    TwitBot.follow_keyword(*TwitBot.get_friends(twitter_screen_name))
    #TwitBot.follow_all(*TwitBot.get_friends(twitter_screen_name),10,'Team_eBird')
    #TwitBot.follow_common_followers(*TwitBot.get_friends(twitter_screen_name),10)
    TwitBot.unfollow_after(*TwitBot.get_friends(twitter_screen_name),100)
    TwitBot.send_dm(*TwitBot.get_friends(twitter_screen_name))