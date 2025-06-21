# Flask + MongoDB Atlas App

## Overview
A multi‐user Flask app with secure MongoDB Atlas integration, Excel upload, and CRUD, ready for Render.com.

## Features
- User registration/login (Flask‐Login)
- Environment‐based config (`.env`)
- MongoDB Atlas (`pymongo`, ping‐on‐startup)
- Excel import (`pandas`/`openpyxl`)
- CRUD on user‐scoped items
- Modular via Blueprints
- CSRF protection (Flask‐WTF)
- Deployable on Render.com or via Docker

## Setup

1. Clone repo & `cd project`
2. `python3.10 -m venv venv && source venv/bin/activate`
3. Copy `.env.example` → `.env`, fill in values
4. `pip install -r requirements.txt`

## Running Locally

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
