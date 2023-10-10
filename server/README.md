# TestPilot backend

This directory contains code for the backend server which integrates with OpenAI's GPT model. This server is made with Flask in Python, with the endpoint `/gpt` that requires code from Visual Studio Code as the body to the request.

# How to run this server locally

 Run `python3 server.py`


# How an .env file should look in this directory

```
export OPENAI_API_KEY = 'key_here'
export OPENAI_ORGANIZATION_KEY= 'key_here'
```