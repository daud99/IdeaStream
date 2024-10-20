# Project Setup Guide

This guide will help you set up the project environment and run the web server. We are using **Python 3.10** for this project.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)
- [Python 3.10](https://www.python.org/downloads/)

Also, make sure to install FFMPEG by running
   ```bash
        brew install ffmpeg
   ```

## Setting Up the Database

To set up the MongoDB database, follow these steps:

1. Pull the MongoDB Docker image:
   ```bash
   docker pull mongo
   ```

2. Run the MongoDB container:
   ```bash
   docker run --name some-mongo -d mongo
   ```

   This command will start a new MongoDB instance in a detached mode.

## Setting Up the Web Server

To set up the web server, follow these steps:

1. Create a virtual environment:
   ```bash
   pip install virtualenv
   virtualenv venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

To start the web server, use the following command:
```bash
uvicorn main:app --reload
```

The `--reload` flag enables automatic reloading, allowing you to see changes without restarting the server.
