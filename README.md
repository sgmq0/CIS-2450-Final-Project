# CIS 2450 Final Project
Raymond Feng & Sofie Aird

Final project for CIS 2450 at Penn.

## Summary
In this project, we are studying audiobooks and podcasts that users have saved to their accounts on Spotify, iTunes, and other listening platforms. 

We plan to study the correlation between the users’ preferred audiobook genres, their preferred podcast genres, and what genres of music they listen to. The end objective is to build some kind of metric to assess a user’s overall taste in media. 

Given that we are working with music-related data, we will be using the Spotify and iTunes APIs as data sources. We may also supplement the data with an API from a book database if needed.

## Install dependencies
From the project root:

```bash
uv sync
```

## Set environment variables
Create a `.env` file:

```bash
cp .env.example .env
```

Then fill in:
- `OPENAI_API_KEY`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- optionally `GOOGLE_BOOKS_API_KEY`

## Run the backend
```bash
uv run uvicorn backend.app:app --reload
```

Then open the API docs at:

```bash
http://127.0.0.1:8000/docs
```
## Run the frontend
In another terminal window,

```bash
cd frontend
npm run dev
```

The frontend can be viewed at:
```bash
http://localhost:5173/
```

# Python Backend Setup

This project now includes a lightweight **FastAPI backend** in the `backend/` folder.

## What it does
- Searches **Spotify artists** and returns genre metadata
- Searches **iTunes podcasts** and returns podcast category metadata
- Searches **Google Books** and returns book / audiobook-style category metadata
- Computes a **media taste profile** from selected items

## Available endpoints
- `GET /health`
- `GET /api/spotify/artists?q=taylor+swift`
- `GET /api/itunes/podcasts?q=the+daily`
- `GET /api/books/audiobooks?q=atomic+habits`
- `POST /api/taste/profile`

## Media taste-score overview
The taste score combines three things:

- Consistency (how similar your genres are across music, podcasts, and audiobooks),
- Diversity (how many different genres you enjoy overall), and
- Balance (how evenly your preferences are spread across the three media types).

These are weighted together to produce a single score that reflects how cohesive, broad, and well-rounded your overall media taste is.

# React Frontend

This project also includes a **React** frontend to allow the user to smoothly interact with the API.