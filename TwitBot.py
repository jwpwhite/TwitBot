# https://github.com/jwpwhite/TwitBot

import os
import json
import tweepy
import twitter
import pandas as pd
import datetime
from datetime import datetime, timedelta
from dateutil import relativedelta
import matplotlib.pyplot as plt
import time
import numpy as np
#import matplotlib.mlab as mlab
from time import sleep
from re import search
from itertools import cycle
from random import shuffle

# function to get list of followers and followings, gets whitelisted users
def get_friends(twitter_screen_name):

    # creates the file path to the log folder
    BASE_DIR = os.getcwd()
    log_location = os.path.join(BASE_DIR, 'logs/{}/'.format(twitter_screen_name))

    # gets all of our data from the config file.
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)

    screen_name = config_data[twitter_screen_name]["auth"]["screen_name"]
    unfollow_after_hours = config_data[twitter_screen_name]["unfollow_after_hours"]

    # authorization for tweepy
    auth = tweepy.OAuthHandler(config_data[twitter_screen_name]["auth"]["CONSUMER_KEY"], config_data[twitter_screen_name]["auth"]["CONSUMER_SECRET"])
    auth.set_access_token(config_data[twitter_screen_name]["auth"]["ACCESS_TOKEN"], config_data[twitter_screen_name]["auth"]["ACCESS_SECRET"])
    api = tweepy.API(auth)

    # authorization for python-twitter (using for messaging)
    twitterapi = twitter.Api(consumer_key=config_data[twitter_screen_name]["auth"]["CONSUMER_KEY"],
                          consumer_secret=config_data[twitter_screen_name]["auth"]["CONSUMER_SECRET"],
                          access_token_key=config_data[twitter_screen_name]["auth"]["ACCESS_TOKEN"],
                          access_token_secret=config_data[twitter_screen_name]["auth"]["ACCESS_SECRET"])
    
    # gets a list of your followers and following
    followers = api.followers_ids(screen_name)
    following = api.friends_ids(screen_name)
    followers_and_following = ('{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),len(followers),len(following)))
    with open('{}followers_and_following.csv'.format(log_location), 'a', encoding="utf-8") as followFile:
        followFile.write("%s\n" % str(followers_and_following))
    total_followed = 0

    #use whilelisted screen_name or id. Using id's speeds up the program significantly...
    if config_data[twitter_screen_name]["whitelist_screen_name_or_id"] == "id":
        whitelisted_users = config_data[twitter_screen_name]["whitelisted_account_ids"]
    else:
        whitelisted_users = []
        # convert screen names to user IDs
        for item in config_data[twitter_screen_name]["whitelisted_accounts"]:
            try:
                # gets info, then gets id.
                item = api.get_user(screen_name=item).id
                # adds the id into newlist.
                whitelisted_users.append(item)
            except tweepy.TweepError:
                pass

    # blacklist users to not folllow - declaring a variable name to minimize confusion.
    blacklisted_users = config_data[twitter_screen_name]["blacklisted_account_ids"]

    return followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi


def spam_checker():
    pass
    #API.direct_messages([since_id][, max_id][, count][, page][, full_text])
    #API.get_direct_message([id][, full_text])
    #API.destroy_direct_message(id)


def optimal_unfollow_time(cut_off_datetime = '2018-08-01 12:00:00'):
    # load the relevant .csv files into dataframes
    followed_unfollowed_df = pd.DataFrame(pd.read_csv('{}followed_and_unfollowed.csv'.format(log_location)))
    followers_record_df = pd.DataFrame(pd.read_csv('{}followers_record.csv'.format(log_location)))

    # Filter the dataframe to only include records after the cutoff date
    filtered_followers_record_df = followers_record_df.loc[followers_record_df['date_time_followed_me'] > cut_off_datetime]

    # Create lists of the users followed by TwitBit and those users that followed you back
    followed_ids_list = followed_unfollowed_df['id'].tolist()
    follower_ids_list = filtered_followers_record_df['id'].tolist()

    # Create a list of users that you followed on TwitBit and those users that followed you back
    followed_back_ids = set.intersection(set(follower_ids_list),set(followed_ids_list))

    time_differences_list = []

    # For each followed user that followed you back, pull the relevant followed and follow back date times from the dataframes
    # and calculate the difference (in days) between the two date times
    for user_id in followed_back_ids:
        # get data times from dataframes for specific user id
        followed_ids_time = followed_unfollowed_df.loc[followed_unfollowed_df['id'] == user_id,['date_time']]['date_time'].values[0]
        follower_ids_time = followers_record_df.loc[followers_record_df['id'] == user_id,['date_time_followed_me']]['date_time_followed_me'].values[0]
        
        # chanage format of date times
        followed_ids_date_time = datetime.strptime(followed_ids_time,'%Y-%m-%d %H:%M:%S')
        follower_ids_date_time = datetime.strptime(follower_ids_time,'%Y-%m-%d %H:%M:%S')
        
        # calculate the difference in time
        time_difference = relativedelta.relativedelta(follower_ids_date_time,followed_ids_date_time)
        
        # extract the relevant time values
        years = time_difference.years
        months = time_difference.months
        days = time_difference.days
        hours = time_difference.hours
        minutes = time_difference.minutes
        
        # calculate the time difference in days
        days_difference = days + hours/24

        # Exclude negatives
        if days_difference > 0:
            # add time difference for each user to the list of time differences
            time_differences_list += [days_difference]
            print('user id: {}, days difference: {}'.format(user_id,str(round(days_difference, 2))))

    print('\n')
    # Plot the time differences in a histogram
    num_bins = 25
    plt.hist(time_differences_list, num_bins, facecolor='blue', alpha=0.5)
    plt.show()



def most_liked(shownlargest = 10):
    # load the relevant .csv files into dataframes
    followers_record_df = pd.DataFrame(pd.read_csv('{}followers_record.csv'.format(log_location)))
    liked_tweets_df = pd.DataFrame(pd.read_csv('{}liked_tweets.csv'.format(log_location)))

    # create a list of users that have had tweets liked
    unique_users_list = list(set(liked_tweets_df['screen_name'].tolist()))
    #create a list of users for each time a user has had a tweet liked
    most_liked_users_list = liked_tweets_df['screen_name'].tolist()

    all_users_like_count_list = []

    for user in unique_users_list:
        # check if the user is following you
        true_false = user in followers_record_df[followers_record_df['date_time_unfollowed_me'] == ' ']['screen_name'].tolist()
        # add the users screen_name, number of likes and follows-you value to a list
        all_users_like_count_list += [[user,most_liked_users_list.count(user),true_false]]

    # convert the list to a dataframe
    all_users_like_count_df = pd.DataFrame(all_users_like_count_list,columns=['user','like_count','follows_you'])
    # show the top
    return all_users_like_count_df.nlargest(shownlargest, 'like_count')


# function to estimate when a user followed you back. Needs to be run hourly to be accurate
def followers_record(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):

    print('\n{} Updating the {} followers_record.csv and followers_and_messages.csv with new followers\n'.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),screen_name))

    ### Add new followers to the followers and messages .csv file
    known_followers_df = pd.DataFrame(pd.read_csv('{}followers_and_messages.csv'.format(log_location)))
    known_followers_list = known_followers_df['id'].tolist()
    new_followers_list = list(set(followers) - set(known_followers_list))

    new_followers_to_append_list = []

    for follower_id in new_followers_list:
        searched_screen_name = api.get_user(follower_id).screen_name
        next_follower = ('{},{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),' ',searched_screen_name,follower_id,'no'))
        new_followers_to_append_list += [next_follower]

    with open('{}followers_and_messages.csv'.format(log_location), 'a', encoding="utf-8") as followers_and_messagesFile:
        for i in new_followers_to_append_list:
            followers_and_messagesFile.write("%s\n" % str(i))


    # load followers previously logged by TwitBot
    followers_record_df = pd.DataFrame(pd.read_csv('{}followers_record.csv'.format(log_location)))
    # create a list of users that were followed in the past so that they are not refollowed
    followers_record_list = followers_record_df['id'].tolist()

    # check if there are new followers not already in the list
    new_followers_list = set(followers) - set(followers_record_list)

    # create a list that will be appended to the followers_record.csv file
    follower_list = []
    follow_count = 0

    for new_follower in new_followers_list:
        try:
            # get followers screen name
            searched_screen_name = api.get_user(new_follower).screen_name
            # Record details of user being followed to followed_and_unfollowed.csv
            next_follower = ('{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),' ',searched_screen_name,new_follower))
            follower_list += [next_follower]
            follow_count += 1
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    with open('{}followers_record.csv'.format(log_location), 'a', encoding="utf-8") as followers_recordFile:
        for i in follower_list:
            followers_recordFile.write("%s\n" % str(i))
    print('Added {} new followers to the {} followers_record.csv file\n'.format(follow_count,screen_name))


    # load followers previously logged by TwitBot
    followers_record_df = pd.DataFrame(pd.read_csv('{}followers_record.csv'.format(log_location)))
    # create a dataframe with only users that have not unfollowed you already
    followers_still_following_df = followers_record_df[followers_record_df['date_time_unfollowed_me'] == ' ']
    # create a list with only users that have not unfollowed you already
    followers_still_following_list = followers_still_following_df['id'].tolist()
    # list of users have recently unfollowed you
    followers_that_unfollowed_list = set(followers_still_following_list) - set(followers)
    follow_count = 0

    print('{} Starting to check which {} followers have unfollowed you recently and saving to followers_record.csv.\n'.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),screen_name))
    for follower in followers_that_unfollowed_list:
        try:
            # add the current date_time to the date_time_unfollowed_me field in the followers_record.csv file
            followers_record_df.loc[followers_record_df['id'] == follower,['date_time_unfollowed_me']] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # print user that has unfollowed you
            print('User {} has unfollowed you.'.format(followers_record_df.loc[followers_record_df['id'] == follower,['screen_name']]['screen_name'].values[0]))
            # print total unfollowed every 10
            # increment total_followed by 1
            total_followed += 1
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    followers_record_df.to_csv('{}followers_record.csv'.format(log_location), index=False, encoding='utf8')
    print('A total of {} users unfollowed {} recently\n'.format(total_followed,screen_name))


# function to follow back users that follow you.
def follow_back(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    # Makes a list of  those you don't follow back.
    non_following = set(followers) - set(following) - set(blacklisted_users)

    print('{} Starting to follow users as {}...'.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),screen_name))

    # starts following users.
    for f in non_following:
        try:
            api.create_friendship(f)
            total_followed += 1
            if total_followed % 10 == 0:
                print(str(total_followed) + ' users followed so far.')
            print('Followed user. Sleeping 10 seconds.')
            sleep(10)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    print('{} Total users that followed {} back: {}'.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),screen_name,total_followed))


# function to follow the followers of another user.
def follow_all(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    #their_screen_name = input('Input their name. Do not use an @ sign. For example, for @POTUS, input just POTUS: ')
    their_followers = api.followers_ids(their_screen_name)
    
    # import users followed previously by TwitBot
    followed_unfollowed_df = pd.DataFrame(pd.read_csv('{}followed_and_unfollowed.csv'.format(log_location)))
    # create a list of users that were followed in the past so that they are not refollowed
    followed_previously_list = followed_unfollowed_df['id'].tolist()
    
    # Makes a list of nonmutual followings.
    their_followers_reduced = set(their_followers) - set(following) - set(followed_previously_list) - set(blacklisted_users)
    
    # create followed_list to store all the users that have been followed
    followed_list = []
    users_followers_list = []
    follow_count = 0

    # loops through their_followers and followers and adds non-mutual relationships to their_followers_reduced
    print("{} Starting to follow @{}'s users...".format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),their_screen_name))
    # loops through the list and follows users.
    for f in their_followers_reduced:
        try:
            # follows the user.
            api.create_friendship(f)
            searched_screen_name = api.get_user(f).screen_name
            # Record details of user being followed to followed_and_unfollowed.csv
            next_followed = ('{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),searched_screen_name,f,'no'))
            followed_list += [next_followed]
            # Record details of user being followed to following_another_users_followers.csv
            next_users_follower = ('{},{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),their_screen_name,searched_screen_name,f,'no'))
            users_followers_list += [next_users_follower]
            total_followed += 1
            follow_count += 1
            if total_followed % 10 == 0:
                print(str(total_followed) + ' users followed so far.')
            print('Followed user {}, {}. Sleeping 10 seconds.'.format(searched_screen_name,f))
            if follow_count >= number_to_follow:
                break 
            sleep(10)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    with open('{}followed_and_unfollowed.csv'.format(log_location), 'a', encoding="utf-8") as followed_unfollowedFile:
        for i in followed_list:
            followed_unfollowedFile.write("%s\n" % str(i))
    with open('{}following_another_users_followers.csv'.format(log_location), 'a', encoding="utf-8") as following_another_users_followersFile:
        for i in users_followers_list:
            following_another_users_followersFile.write("%s\n" % str(i))
    print('Total users followed: {}\n'.format(total_followed))


# Function to follow the followers that are common to multiple users. The purpose of the function is to target followers with very specific interests.
def follow_common_followers(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    screen_names_list = ['audubonsociety','CornellBirds','Team_eBird']
    list_of_user_follower_sets = []
    
    # create a list of user follower sets
    for screen_name in screen_names_list:
        user_followers_set = set(api.followers_ids(screen_name))
        list_of_user_follower_sets += [user_followers_set]

    # create a set of all the followers that are common to all the users in screen_names_list
    common_followers = set.intersection(*list_of_user_follower_sets)
    
    # import users followed previously by TwitBot
    followed_unfollowed_df = pd.DataFrame(pd.read_csv('{}followed_and_unfollowed.csv'.format(log_location)))
    # create a list of users that were followed in the past so that they are not refollowed
    followed_previously_list = followed_unfollowed_df['id'].tolist()
    
    # Makes a list of nonmutual followings.
    their_followers_reduced = set(common_followers) - set(following) - set(followed_previously_list) - set(blacklisted_users)
    
    # create followed_list to store all the users that have been followed
    followed_list = []
    users_followers_list = []
    follow_count = 0

    # loops through their_followers and followers and adds non-mutual relationships to their_followers_reduced
    print("{} Starting to follow common followers of users: {}".format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),screen_names_list))
    # loops through the list and follows users.
    for f in their_followers_reduced:
        try:
            # follows the user.
            api.create_friendship(f)
            searched_screen_name = api.get_user(f).screen_name
            # Record details of user being followed to followed_and_unfollowed.csv
            next_followed = ('{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),searched_screen_name,f,'no'))
            followed_list += [next_followed]
            # Record details of user being followed to following_another_users_followers.csv
            next_users_follower = ('{},{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),screen_names_list,searched_screen_name,f,'no'))
            users_followers_list += [next_users_follower]
            total_followed += 1
            follow_count += 1
            print('Followed user {}, {}. Sleeping 10 seconds.'.format(searched_screen_name,f))
            if total_followed % 10 == 0:
                print(str(total_followed) + ' users followed so far.')
            if follow_count >= number_to_follow:
                break 
            sleep(10)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    with open('{}followed_and_unfollowed.csv'.format(log_location), 'a', encoding="utf-8") as followed_unfollowedFile:
        for i in followed_list:
            followed_unfollowedFile.write("%s\n" % str(i))
    with open('{}following_users_common_followers.csv'.format(log_location), 'a', encoding="utf-8") as following_users_common_followersFile:
        for i in users_followers_list:
            following_users_common_followersFile.write("%s\n" % str(i))
    print('Total users followed: {}'.format(total_followed))


# function to follow users based on a keyword:
def follow_keyword(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    # import users followed previously by TwitBot
    followed_unfollowed_df = pd.DataFrame(pd.read_csv('{}followed_and_unfollowed.csv'.format(log_location)))
    # create a list of users that were followed in the past so that they are not refollowed
    followed_previously_list = followed_unfollowed_df['id'].tolist()
    for i in config_data[screen_name]["keywords"]:
        # gets search result
        search_results = api.search(
            q=i,
            count=config_data[screen_name]["follow_results_search"],
            lang=config_data[screen_name]["lang"])
        searched_screen_ids = [tweet.author._json['id'] for tweet in search_results]
        filtered_screen_ids = list(set(searched_screen_ids) - set(following) - set(followed_previously_list) - set(blacklisted_users))

        # create followed_list to store all the users that have been followed
        followed_list = []
        
        # only follows 100 of each keyword to avoid following non-relevant users.
        print('\n{} Starting to follow users who tweeted \'{}\''.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),i))
        for i in range(0, len(filtered_screen_ids) - 1):
            try:
                # follows the user.
                api.create_friendship(filtered_screen_ids[i])
                searched_screen_name = api.get_user(filtered_screen_ids[i]).screen_name
                next_followed = ('{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),searched_screen_name,filtered_screen_ids[i],'no'))
                followed_list += [next_followed]
                total_followed += 1
                if total_followed % 10 == 0:
                    print(str(total_followed) + ' users followed so far.')
                print('Followed user {}, {}. Sleeping 10 seconds.'.format(searched_screen_name,filtered_screen_ids[i]))
                sleep(10)
            except (tweepy.RateLimitError, tweepy.TweepError) as e:
                error_handling(e)

        with open('{}followed_and_unfollowed.csv'.format(log_location), 'a', encoding="utf-8") as followed_unfollowedFile:
            for i in followed_list:
                followed_unfollowedFile.write("%s\n" % str(i))
    print('Total users followed: {}\n'.format(total_followed))



# function to follow users who retweeted a tweet.
def follow_rters(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    print("Per Twitter's API, this method only returns a max of 100 users per tweet. \n")

    # gets the tweet ID using regex
    tweet_url = input('Please input the full URL of the tweet: ')
    try:
        tweetID = search('/status/(\d+)', tweet_url).group(1)
    except tweepy.TweepError as e:
        print(e)
        print('Could not get tweet ID. Try again. ')
        follow_rters()

    # gets a list of users who retweeted a tweet
    RTUsers = api.retweeters(tweetID)
    RTUsers = set(RTUsers) - set(blacklisted_users)

    print('Starting to follow users.')

    # follows users:
    for f in RTUsers:
        try:
            api.create_friendship(f)
            total_followed += 1
            if total_followed % 10 == 0:
                print(str(total_followed) + ' users followed so far.')
            # sleeps so it doesn't follow too quickly.
            print('Followed user. Sleeping 10 seconds.')
            sleep(10)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    print(total_followed)



# function to unfollow users that don't follow you back.
def unfollow_back(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    print('Starting to unfollow users...')
    # makes a new list of users who don't follow you back.
    non_mutuals = set(following) - set(followers) - set(whitelisted_users)
    for f in non_mutuals:
        try:
            # unfollows non follower.
            api.destroy_friendship(f)
            total_followed += 1
            if total_followed % 10 == 0:
                print(str(total_followed) + ' unfollowed so far.')
            print('Unfollowed user. Sleeping 15 seconds.')
            sleep(15)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    print(total_followed)



# function to unfollow all users.
def unfollow_all(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    # whitelists some users.
    unfollowing_users = set(following) - set(whitelisted_users)
    print('Starting to unfollow.')
    for f in unfollowing_users:
        # unfollows user
        api.destroy_friendship(f)
        # increment total_followed by 1
        total_followed += 1
        # print total unfollowed every 10
        if total_followed % 10 == 0:
            print(str(total_followed) + ' unfollowed so far.')
        # print sleeping, sleep.
        print('Unfollowed user. Sleeping 8 seconds.')
        sleep(8)
    print(total_followed)


# function to unfollow users followed by twitterBot if they have not followed back after a set number of hours.
def unfollow_after(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi, max_unfollow=10):
    # import users followed by twitbot
    followed_unfollowed_df = pd.DataFrame(pd.read_csv('{}followed_and_unfollowed.csv'.format(log_location)))
    # what is the datetime that corresponds with the users defined hours before unfollow
    cut_off_datetime = datetime.now() - timedelta(hours=unfollow_after_hours)
    # create a list of users that were followed more than the defined numner of hours ago
    followed_prior_to_cutoff_df = followed_unfollowed_df[(followed_unfollowed_df['unfollowed'] == 'no') & (followed_unfollowed_df['date_time'] < cut_off_datetime.strftime('%Y-%m-%d %H:%M:%S'))]
    followed_prior_to_cutoff_list = followed_prior_to_cutoff_df['id'].tolist()
    # whitelists some users and filter our users that have not reached the deadline.
    all_unfollowing_users = set(followed_prior_to_cutoff_list) -set(followers) - set(whitelisted_users)
    # limit the list by the max_unfollow variable
    unfollowing_users = list(all_unfollowing_users)[:max_unfollow]
    print('{} Starting to unfollow users that did not follow {} back.'.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),screen_name))
    for f in unfollowing_users:
        try:
            # unfollows user
            api.destroy_friendship(f)
            # increment total_followed by 1
            total_followed += 1
            # change unfollowed status in dataframe to 'yes'
            followed_unfollowed_df.loc[followed_unfollowed_df['id'] == f,['unfollowed']] = 'yes'
            # print sleeping.
            print('Unfollowed user {}. Sleeping 8 seconds.'.format(followed_unfollowed_df.loc[followed_unfollowed_df['id'] == f,['screen_name']]['screen_name'].values[0]))
            # print total unfollowed every 10
            if total_followed % 10 == 0:
                print(str(total_followed) + ' unfollowed so far.')
            #sleep for 10 seconds
            sleep(10)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            print(f)
            error_handling(e)
    followed_unfollowed_df.to_csv('{}followed_and_unfollowed.csv'.format(log_location), index=False, encoding='utf8')
    print('Total users unfollowed: {}\n'.format(total_followed))


# Function to favorite tweets based on keywords
def fav_off_keyword(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):

    for i in config_data[screen_name]["keywords"]:
        # gets search result
        search_results = api.search(
            q=i,
            count=config_data[screen_name]["fav_results_search"],
            lang=config_data[screen_name]["lang"])
        # extract tweet ids and user data from tweets
        searched_tweet_user_data = [tweet._json for tweet in search_results]

        # extract original tweet id's. These are the original post's tweet id's where a post has been retweeted. Prevents error when you try to like a retweet where the tweet has already been liked.
        searched_tweet_ids = []

        for tweet in searched_tweet_user_data:
            try:
                searched_tweet_ids += [[tweet['id'],tweet['retweeted_status']['id']]]
            except:
                searched_tweet_ids += [[tweet['id'],' ']]

        # import users followed previously by TwitBot
        liked_tweets_df = pd.DataFrame(pd.read_csv('{}liked_tweets.csv'.format(log_location)))
        liked_tweet_ids_list = liked_tweets_df['tweet_id'].tolist()
        liked_original_tweet_ids_list = liked_tweets_df['original_tweet_id'].tolist()
        liked_tweet_retweet_ids_list = list(set(liked_tweet_ids_list + liked_original_tweet_ids_list))

        liked_tweets_list = []

        # only follows 100 of each keyword to avoid following non-relevant users.
        print('\n{} Starting to like users who tweeted \'{}\''.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),i))
        for x in range(0, len(searched_tweet_ids) - 1):
            # search to see if a tweet has already been liked and then ignore if it has.
            try:
                # Don't like if the user is in Blacklisted users list or already liked as a tweet or retweet
                if searched_tweet_user_data[x]['user']['id'] in blacklisted_users:
                    break
                if searched_tweet_ids[x][0] in liked_tweet_retweet_ids_list:
                    break
                if searched_tweet_ids[x][1] in liked_tweet_retweet_ids_list:
                    break

                # Add tweet id's to liked_tweet_retweet_ids_list to make sure they are not liked more than once
                liked_tweet_retweet_ids_list += [searched_tweet_ids[x][0],searched_tweet_ids[x][1]]

                api.create_favorite(searched_tweet_ids[x][0])
                # get user and tweet data for post analysis
                tweet_id = searched_tweet_ids[x][0]
                original_tweet_id = searched_tweet_ids[x][1]
                tweet_date_time = searched_tweet_user_data[x]['created_at']
                searched_hashtag = i
                liked_screen_name = searched_tweet_user_data[x]['user']['screen_name']
                user_id = searched_tweet_user_data[x]['user']['id']
                follows_me = liked_screen_name in followers
                user_location = searched_tweet_user_data[x]['user']['location'].replace(',','')
                followers_count = searched_tweet_user_data[x]['user']['followers_count']
                friends_count = searched_tweet_user_data[x]['user']['friends_count']
                favourites_count = searched_tweet_user_data[x]['user']['favourites_count']
                statuses_count = searched_tweet_user_data[x]['user']['statuses_count']
                tweet_likes = searched_tweet_user_data[x]['favorite_count']
                tweet_text = ' '#searched_tweet_user_data[x]['text']
                liked_tweet = ('{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}'.format(
                    tweet_id,
                    original_tweet_id,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    tweet_date_time,
                    searched_hashtag,
                    liked_screen_name,
                    user_id,
                    follows_me,
                    user_location,
                    followers_count,
                    friends_count,
                    favourites_count,
                    statuses_count,
                    tweet_likes,
                    tweet_text))
                liked_tweets_list += [liked_tweet]

                total_followed += 1
                if total_followed % 10 == 0:
                    print(str(total_followed) + ' tweets liked so far.')
                print('Liked tweet by {}. Sleeping 12 seconds.'.format(liked_screen_name))
                sleep(12)
            except (tweepy.RateLimitError, tweepy.TweepError) as e:
                print(searched_tweet_ids[x][0])
                error_handling(e)
        with open('{}liked_tweets.csv'.format(log_location), 'a', encoding="utf-8") as liked_tweetsFile:
            for i in liked_tweets_list:
                liked_tweetsFile.write("%s\n" % str(i))
        print('Total tweets liked: {}\n'.format(total_followed))
        print('Taking a quick 20 second snooze')
        sleep(20)
        print('\nYawn... OK, ready to go :)\n')
    return total_followed

# unfavorite all favorites
def unfavorite_all(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    total_unliked = 0
    all_favorites = api.favorites(screen_name)

    for i in all_favorites:
        try:
            api.destroy_favorite(i.id)
            total_unliked += 1
            if total_unliked % 10 == 0:
                print(str(total_unliked) + ' tweets unliked so far.')
            print('Unliked tweet. Sleeping 8 seconds.')
            sleep(8)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)

# Send a DM to users that follow you.
def send_dm(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    known_followers_df = pd.DataFrame(pd.read_csv('{}followers_and_messages.csv'.format(log_location)))
    known_followers_list = known_followers_df['id'].tolist()
    new_followers_list = list(set(followers) - set(known_followers_list))

    new_followers_to_append_list = []

    for follower_id in new_followers_list:
        searched_screen_name = api.get_user(follower_id).screen_name #check this screen_name is not going to conflict with the screen_name variable.
        next_follower = ('{},{},{},{},{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),' ',searched_screen_name,follower_id,'no'))
        new_followers_to_append_list += [next_follower]

    with open('{}followers_and_messages.csv'.format(log_location), 'a', encoding="utf-8") as followers_and_messagesFile:
        for i in new_followers_to_append_list:
            followers_and_messagesFile.write("%s\n" % str(i))


    known_followers_df = pd.DataFrame(pd.read_csv('{}followers_and_messages.csv'.format(log_location)))
    followers_to_message_list = known_followers_df[known_followers_df['messaged'] == 'no']['id'].tolist()

    shuffle(followers_to_message_list)
    messages = config_data[screen_name]["messages"]
    greetings = config_data[screen_name]["greetings"]
    signoff = config_data[screen_name]["signoff"]
    # tries sending a message to your followers. switches greeting and message.
    print('{} Starting to send messages to new {} followers... '.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'),screen_name))
    for user, message, greeting, signoff in zip(followers_to_message_list, cycle(messages), cycle(greetings), cycle(signoff)):
        try:
            username = api.get_user(user).screen_name
            # sends dm.
            #api.send_direct_message(user_id=user, text='{} @{},\n{}\n{}'.format(greeting, username, message, signoff))
            #api.send_direct_message(type='message_create', recipient_id=user, message_data='{} @{},\n{}\n{}'.format(greeting, username, message, signoff))
            twitterapi.PostDirectMessage(user_id=user, screen_name=None, return_json=False,text='{} @{},\n{}\n{}'.format(greeting, username, message, signoff))
            # updated dataframe to register that the user has been messaged
            known_followers_df.loc[known_followers_df['id'] == user,['messaged']] = 'yes'
            total_followed += 1
            if total_followed % 5 == 0:
                print(str(total_followed) + ' messages sent so far.')
            print('Sent the {} a DM. Sleeping 45 seconds.'.format(username))
            sleep(45)
        except (tweepy.RateLimitError, tweepy.TweepError) as e:
            error_handling(e)
    known_followers_df.to_csv('{}followers_and_messages.csv'.format(log_location), index=False, encoding='utf8')
    print('Total messages sent to new {} followers: {}\n'.format(screen_name,total_followed))


# function to get follower/following count
def get_count(followers, following, total_followed, whitelisted_users, blacklisted_users, log_location, config_data, screen_name, unfollow_after_hours, api, twitterapi):
    # prints the count.
    print('You follow {} users and {} users follow you.'.format(len(following), len(followers)))
    print('This is sometimes inaccurate due to the nature of the API and updates. Be sure to double check. ')



# function to handle errors
def error_handling(e):
    error = type(e)
    if error == tweepy.RateLimitError:
        print("You've hit a limit! Sleeping for 30 minutes.")
        sleep(60 * 30)
    if error == tweepy.TweepError:
        print('Uh oh. Could not complete task. Sleeping 10 seconds.')
        sleep(10)


# function to continue
def Continue():
    # asks the user if they want to keep calculating, converts to lower case
    keep_going = input('Do you want to keep going? Enter yes or no. \n'
                       '').lower()
    # evaluates user's response.
    if keep_going == 'yes':
        main_menu()
    elif keep_going == 'no':
        print('\n'
              'Thanks for using the Twitter bot!')
        quit()
    else:
        print('\n'
              'Input not recognized. Try again.')


# runs the main function, which runs everything else.
if __name__ == "__main__":
    main_menu()
