# TwitBot

This is a Twitter bot that allows you to do automate a variety of tasks and generate logs of everything that is done! Schedule specific functions to run one by one using auto.py.

Specific functions can be run:
1. Create a record of your followers and record the date/time if they unfollow you
2. Follow back users that follow you.
3. Follow the followers of another user.
4. Follow the followers that are common to multiple users
5. Follow users based on a keyword.
6. Follow users who retweeted a tweet.
7. Unfollow users that don't follow you back.
8. Unfollow all users.
9. Unfollow TwitBot followed users after X hours delay.
10. Like tweets based on a keyword.
11. Unlike all tweets.
12. Send a DM to users that follow you.
13. Get follower and following count.
14. Report users whos tweets you have liked the most.
15. Followers record to estimate when a user followed you back. Needs to be run at least daily to be accurate.
16. Check the optimal unfollow time if a user does not follow you back.

## Getting Started

### Prerequisites
You will need the follwing modules installed:
 - numpy>=1.15.2
 - pandas>=0.23.4
 - python-twitter>=3.5
 - tweepy>=3.6.0
 - matplotlib>=3.0.0

### Creating a Twitter App
Create an app https://apps.twitter.com/
Use the credentials from the app to populate the config.json file as detailed below

### Setting up config.json file
The config.json file contain all the authentication variables and settings used to run the automation.

### Todo:


## Authors
* **John White** - [jwpwhite](https://github.com/jwpwhite)
Based of Twitter-Follow-and-Unfollow-Bot by https://github.com/yousefissa/

## License
This project is licensed under the MIT License.
