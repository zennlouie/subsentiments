# SubSentiments: Reddit Sentiment Analysis Tool

SubSentiments is a  web application tool that performs sentiment analysis on posts and comments from a specified subreddit. The analysis categorizes the content into negative, neutral, and positive sentiments. Users can choose different visualization options and download the analysis results in PDF format.

## Features
- Fetch posts and comments from a specified subreddit.
- Perform sentiment analysis using a DistilBERT model.
- Visualize the results with bar charts, line graphs, word clouds, and pie charts.
- Download the results as a PDF file.

## Requirements
- `panel`
- `asyncpraw`
- `pandas`
- `matplotlib`
- `wordcloud`
- `reportlab`
- `asyncio`

## Note
Currently, this is only the web application part code. The code/scripts for the process of data gathering and sentiment analysis is not included.