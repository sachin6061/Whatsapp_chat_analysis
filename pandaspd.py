import re
import regex
import pandas as pd
import numpy as np
import emoji
from collections import Counter
import matplotlib.pyplot as plt


# %matplotlib inline

def startsWithDateAndTimeAndroid(s):
    pattern = '^([0-9]+)(\/)([0-9]+)(\/)([0-9]+), ([0-9]+):([0-9]+)[ ]?(AM|PM|am|pm)? -'
    result = re.match(pattern, s)
    if result:
        return True
    return False


def FindAuthor(s):
    s = s.split(":")
    if len(s) == 2:
        return True
    else:
        return False


def getDataPointAndroid(line):
    splitLine = line.split(' - ')
    dateTime = splitLine[0]
    date, time = dateTime.split(', ')
    message = ' '.join(splitLine[1:])
    if FindAuthor(message):
        splitMessage = message.split(':')
        author = splitMessage[0]
        message = ' '.join(splitMessage[1:])
    else:
        author = None
    return date, time, author, message


def getDataPointios(line):
    splitLine = line.split('] ')
    dateTime = splitLine[0]
    if ',' in dateTime:
        date, time = dateTime.split(',')
    else:
        date, time = dateTime.split(' ')
    message = ' '.join(splitLine[1:])
    if FindAuthor(message):
        splitMessage = message.split(':')
        author = splitMessage[0]
        message = ' '.join(splitMessage[1:])
    else:
        author = None
    if time[5] == ":":
        time = time[:5] + time[-3:]
    else:
        if 'AM' in time or 'PM' in time:
            time = time[:6] + time[-3:]
        else:
            time = time[:6]
    return date, time, author, message


def split_count(text):
    text = emoji.demojize(text)
    text = re.findall(r'(:[^:]*:)', text)
    list_emoji = [emoji.emojize(x) for x in text]
    return list_emoji


parsedData = []  # List to keep track of data so it can be used by a Pandas dataframe
conversationPath = 'group1.txt'


def startsWithDateAndTimeios(line):
    pass


with open(conversationPath, encoding="utf-8") as fp:
    device = ''
    first = fp.readline()
    print(first)
    if '[' in first:
        device = 'ios'
    else:
        device = "android"
    fp.readline()
    messageBuffer = []
    date, time, author = None, None, None  # message contains 4 things-"date","time","author","message"
    while True:
        line = fp.readline()
        if not line:
            break
        else:
            line = line.strip()
            if startsWithDateAndTimeAndroid(line):
                if len(messageBuffer) > 0:
                    parsedData.append([date, time, author, ' '.join(messageBuffer)])
                messageBuffer.clear()
                date, time, author, message = getDataPointAndroid(line)
                messageBuffer.append(message)
            else:
                messageBuffer.append(line)
    if device == 'android':
        df = pd.DataFrame(parsedData, columns=['Date', 'Time', 'Author', 'Message'])
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.dropna()
        df["emoji"] = df["Message"].apply(split_count)
        # print(df["Message"].apply(split_count))
        URLPATTERN = r'(https?://\S+)'
        df['urlcount'] = df.Message.apply(lambda x: re.findall(URLPATTERN, x)).str.len()

    print('group members', df.Author.unique())
    print('Total group members', len(df.Author.unique()))
    total_messages = df.shape[0]
    print('Total number of messages', total_messages)
    media_messages = df[df['Message'] == '<Media omitted>'].shape[0]
    print("Total number of media message", media_messages)
    emojis = sum(df['emoji'].str.len())
    print('Total Emojis ', emojis)
    URLPATTERN = r'(https?://\S+)'  # regex pattern matching with start with https
    df['urlcount'] = df.Message.apply(lambda x: re.findall(URLPATTERN,
                                                           x)).str.len()  # return url which matches with pattern and count it through lambda function
    links = np.sum(df.urlcount)  # sumup all the links
    print("Total number of url", links)

    total_emojis_list = list([a for b in df.emoji for a in b])
    emoji_dict = dict(Counter(total_emojis_list))
    emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)
    print("most used emojis", emoji_dict)

    link_messages = df[df['urlcount'] > 0]
    deleted_messages = df[
        (df["Message"] == " You deleted this message") | (df["Message"] == " This message was deleted.")]
    media_messages_df = df[(df['Message'] == ' <Media omitted>') | (df['Message'] == ' image omitted') | (
            df['Message'] == ' video omitted') | (df['Message'] == ' sticker omitted')]
    messages_df = df.drop(media_messages_df.index)
    messages_df = messages_df.drop(deleted_messages.index)
    messages_df = messages_df.drop(link_messages.index)

    messages_df['Word_Count'] = messages_df['Message'].apply(
        lambda s: len(s.split(' ')))  # word is calculated by spliting sentence by whitespace
    messages_df["MessageCount"] = 1

    frnds = messages_df.Author.unique()
    frnds_author = []
    message_count = []

    for i in range(len(frnds)):
        # Filtering out messages of particular user
        req_df = messages_df[messages_df["Author"] == frnds[i]]
        # req_df will contain messages of only one particular user
        # print(f'Stats of {frnds[i]} -')
        # shape will print number of rows which indirectly means the number of messages
        # print('Messages Sent', req_df.shape[0])
        # Word_Count contains of total words in one message. Sum of all words/ Total Messages will yield words per message
        words_per_message = (np.sum(req_df['Word_Count'])) / req_df.shape[0]
        # print('Words per message', words_per_message)
        # media conists of media messages
        media = media_messages_df[media_messages_df['Author'] == frnds[i]].shape[0]
        # print('Media Messages Sent', media)
        # emojis conists of total emojis
        emojis = sum(req_df['emoji'].str.len())
        # print('Emojis Sent', emojis)
        # links consist of total links
        links = sum(link_messages[link_messages['Author'] == frnds[i]]["urlcount"])

        # print('Links Sent', links)
        frnds_author.append(frnds[i])
        message_count.append(req_df.shape[0])

    print('Most active user in group')
    data_df = pd.DataFrame({'author': frnds_author, 'message_count': message_count})
    print(data_df.max())

# this is for show plot
    messages_df['Time'].value_counts().head(
        10).plot.barh()  # Top 10 Times of the day at which the most number of messages were sent
    plt.xlabel('Number of messages')
    plt.ylabel('Time')
    print(plt.show())

