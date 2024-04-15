# TestPilot backend

This directory contains code for the backend server which integrates with OpenAI's GPT model. This server is made with Flask in Python, with two endpoints for the two modes of operation in the Visual Studio Code extension. 
- `/testpilot/testing` 
- `/testpilot/discovery` 

The `evaluation` folder contains code, plots and data files for evaluating TestPilot.

# How to run this server locally

This server uses Python 3.9. To run the server locally, run
```
python3 server.py
```


# Environment file setup
TestPilot requires 2 .env files for its operation. The first file is `.env.processing` which is used for the generation of synthetic data using Mistral 7B from an endpoint at https://anyscale.com. The API key is based on OpenAI's client, so the file should look like:

```
export OPENAI_API_KEY='anyscale_api_key'
export OPENAI_BASE_URL='https://api.endpoints.anyscale.com/v1''
```

The second file is `.env.server` which is used for the operation of TestPilot through OpenAI's GPT-3.5 Turbo and GPT-4. The name of the fine-tuned GPT-3.5 Turbo instance is required here. It also requires an API key and endpoint URL for accessing the ASTRADB vector database from https://www.datastax.com/. This file should look like:
```
export OPENAI_API_KEY = 'openai_api_key'
export OPENAI_ORGANIZATION_KEY= 'openai_organization_key'
export ASTRA_DB_KEY = 'astradb_api_key'
export ASTRA_DB_API = 'astradb_api_link'
export FINE_TUNED_GPT_3_POINT_5_TURBO = 'finetuned_model_name'
```

