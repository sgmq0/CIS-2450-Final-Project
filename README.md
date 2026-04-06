# CIS 2450 Final Project
Raymond Feng & Sofie Aird

Final project for CIS 2450 at Penn.

## Summary
In this project, we are studying audiobooks and podcasts that users have saved to their accounts on Spotify, iTunes, and other listening platforms. 

We plan to study the correlation between the users’ preferred audiobook genres, their preferred podcast genres, and what genres of music they listen to. The end objective is to build some kind of metric to assess a user’s overall taste in media. 

Given that we are working with music-related data, we will be using the Spotify and iTunes APIs as data sources. We may also supplement the data with an API from a book database if needed.


## Development Steps
1. Clone this repository.
2. In the root folder, do `uv sync` to install all the dependencies. This will create the `.venv` folder.
3. Set the `OPENAI_API_KEY` environment variable:
```
echo "OPENAI_API_KEY=your-api-key-here" > .env
```
The api key can be found on EdStem. 
