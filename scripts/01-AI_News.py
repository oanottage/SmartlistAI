import pandas as pd
import requests
import json
import datetime
import time
import sqlite3
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from newsapi import NewsApiClient
import os
import openai
import warnings
import pdfkit
warnings.filterwarnings("ignore")
os.chdir('/Users/oanottage/Desktop/BTS/Data Science Foundations/DSFinal/')


# Function to preprocess source value from API
def extract_source_fields(row):
    source = row['source']
    source_id = source['id']
    source_name = source['name']
    return pd.Series({'source_id': source_id, 'source_name': source_name})


# Get today's date
today = datetime.datetime.today().date()
month_ago = today - datetime.timedelta(days=28)


# Industry Label
industry = "artificial intelligence"
industry_csv = industry.replace(" ", "_")
industry = industry.replace(" ", "&q=")


# API Connection
newsapi = NewsApiClient(api_key='90d9ca3d39694c12a3ad69e20a13220b')
all_articles = newsapi.get_everything(q=industry,
                                      from_param=month_ago,
                                      to=today,
                                      language='en',
                                      sort_by='popularity',
                                      page=1)
articles = all_articles['articles']
df = pd.DataFrame(articles)
df = df.reset_index()


# Apply the custom function to the 'source' column
df[['source_id', 'source_name']] = df.apply(extract_source_fields, axis=1)

# Use the pop() method to remove the 'source_id' and 'source_name' columns from the dataframe
source_id = df.pop('source_id')
source_name = df.pop('source_name')

# Use the insert() method to insert the 'source_id' and 'source_name' columns at the beginning of the dataframe
df.insert(0, 'source_id', source_id)
df.insert(1, 'source_name', source_name)

df.drop(columns=['source'], inplace=True)


# Create a wordcloud
# Extract the "title" column and combine all text into a single string
text = " ".join(df["title"].dropna())
# Create a WordCloud object with the desired parameters
wordcloud = WordCloud(width=800, height=400, max_words=200,
                      background_color="white").generate(text)
# Display the WordCloud using Matplotlib
plt.figure(figsize=(12, 10))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.savefig('media/{}_by_title_{}.png'.format(industry_csv, today))


# Create a wordcloud
# Extract the "description" column and combine all text into a single string
text = " ".join(df["description"].dropna())
# Create a WordCloud object with the desired parameters
wordcloud = WordCloud(width=800, height=400, max_words=200,
                      background_color="white").generate(text)
# Display the WordCloud using Matplotlib
plt.figure(figsize=(12, 10))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.savefig('media/{}_by_description_{}.png'.format(industry_csv, today))


# Create a wordcloud
# Extract the "content" column and combine all text into a single string
text = " ".join(df["content"].dropna())
# Create a WordCloud object with the desired parameters
wordcloud = WordCloud(width=800, height=400, max_words=200,
                      background_color="white").generate(text)
# Display the WordCloud using Matplotlib
plt.figure(figsize=(12, 10))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.savefig("media/{}_by_content_{}.png".format(industry_csv, today))


# Save to CSV
df.to_csv(
    'data/external/NewsAPI/{industry_csv}_articles_FROM_{month_ago}_TO_{today}.csv', index=False)


# Save to Database
df['TimeStamp'] = today
df.columns = ['source_id', 'source_name', 'ind', 'author', 'title', 'description',
              'url', 'urlToImage', 'publishedAt', 'content', 'TimeStamp']
# Run the 'create if it doesn't exist' SQL statement


def create_db(folder, table_name, df):
    # Open a connection to the database and create a cursor
    cnx = sqlite3.connect('{}/DSFinal.db'.format(folder))
    c = cnx.cursor()

    # Get the column names and types from the dataframe
    cols = df.columns.tolist()
    types = df.dtypes.tolist()

    # Create the SQL CREATE TABLE statement
    create_statement = "CREATE TABLE IF NOT EXISTS {} ({})".format(
        table_name, ', '.join(['{} {}'.format(col, types) for col, types in zip(cols, types)]))

    # Execute the CREATE TABLE statement
    c.execute(create_statement)

    # Commit the changes and close the cursor and connection
    cnx.commit()


# Creating the table
def create_table(folder, table_name, df):
    cnx = sqlite3.connect('{}/DSFinal.db'.format(folder))
    c = cnx.cursor()
    # Get the list of column names and data types in the DataFrame
    cols = list(df.columns)
    types = df.dtypes.apply(lambda x: x.name).tolist()

    # Create the CREATE TABLE statement dynamically
    create_statement = "CREATE TABLE IF NOT EXISTS {} ({})".format(
        table_name, ', '.join(['{} {}'.format(col, types) for col, types in zip(cols, types)]))

    # Execute the CREATE TABLE statement
    c.execute(create_statement)
    # Commit the changes and close the cursor and connection
    cnx.commit()


# Dynamic Insertion
def dynamic_insertion(folder, table_name, df):
    cnx = sqlite3.connect('{}/DSFinal.db'.format(folder))
    c = cnx.cursor()
    # Get the list of column names in the DataFrame
    cols = list(df.columns)

    # Create the INSERT statement dynamically
    insert_statement = "INSERT INTO {}({}) VALUES ({})".format(
        table_name, ", ".join(cols), ", ".join(['?' for _ in range(len(cols))]))

    # Insert the data into the database
    for index, row in df.iterrows():
        c.execute(insert_statement, tuple(row))
        cnx.commit()

    # Close the database connection and cursor
    c.close()
    cnx.close()

# Putting it all together


def push(folder, table_name, df):
    create_db(folder, table_name, df)
    create_table(folder, table_name, df)
    dynamic_insertion(folder, table_name, df)


push('databases', 'news_api', df)
push('databases', 'news_api', df)


# OPENAI

openai.api_key = "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"
raw = pd.read_csv(
    'data/external/NewsAPI/{}_articles_FROM_{}_TO_{}.csv'.format(industry_csv, month_ago, today))


df_raw = raw[raw['title'].notnull()].reindex(
    columns=raw.columns.tolist() + ['Minor_Tag', 'Major_Tag', 'Summary'])


df = df_raw.head(10)

summary = "Give 20-50 word summary of this article: "
major = "Give me 3 major tags for this article: "
minor = "Give me 3 major tags for this article: "

# Minor Tag
for i in range(df.shape[0]):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=minor+df["content"].iloc[i],
        temperature=0,
        max_tokens=60,
        top_p=1,
        frequency_penalty=0.5)
    answer = response['choices'][0]['text']
    df["Minor_Tag"].iloc[i] = answer


# Major Tag
for i in range(df.shape[0]):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=major+df["content"].iloc[i],
        temperature=0,
        max_tokens=60,
        top_p=1,
        frequency_penalty=0.5)
    answer = response['choices'][0]['text']
    df["Major_Tag"].iloc[i] = answer


# Summary
for i in range(df.shape[0]):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=summary+df["content"].iloc[i],
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0.5)
    answer = response['choices'][0]['text']
    df["Summary"].iloc[i] = answer


html_str = ''

# loop through the dataframe and generate the HTML code
for i in range(df.shape[0]):
    html_str += "<h3>Article {}: {}</h3>".format(i+1, df['title'].iloc[i])
    html_str += "<br>"
    html_str += '<img src="{}" width="500" height="300">'.format(
        df["urlToImage"].iloc[i])
    html_str += "<br>"
    html_str += "<br>"
    html_str += "Summary: " + df['Summary'].iloc[i].replace("\n", "")
    html_str += "<br>"
    html_str += "<a href='{}' target='_blank'>Click to read more</a> <br>".format(
        df['url'].iloc[i])
    html_str += "<br>"
    html_str += "Tags: " + df['Major_Tag'].iloc[i].replace("\n", "<br>")
    html_str += "<br>"
    html_str += ""

config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')


# create a PDF file from the HTML string
pdfkit.from_string(
    html_str, 'deliverables/OpenAI_Top_{}_news_article_summaries_{}.pdf'.format(df.shape[0], today))

df.to_csv(
    "deliverables/OpenAI_Top_{}_news_article_summaries_{}.csv".format(df.shape[0], today))
