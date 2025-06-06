# Running a small LLM locally using fastAPI

## Prerequisites

You'll need the following pre-installed in your system:
- python
- bash

## Set-up

Set up a virtual environment first, with the following command:

```bash 
python -m venv venv
```

Then activate the virtual environment:

```bash
source venv/bin/activate 
```

## Install Dependecies

> [!NOTE]
> These dependecies are large in size, and can total upto 1GB upon downloading

This project requires dependecies that can be downloaded with the following command:

```bash
pip install fastapi uvicorn transformers torch
```

You can confirm that everything has downloaded properly by checking the list of installed dependecies:

```bash
pip list
```

From the output make sure that the following are present:
- fastapi      x.x.x
- torch        x.x.x
- transformers x.x.x
- uvicorn      x.x.x
- pydantic     x.x.x

## Start the server

To start the server you simply need to use `uvicorn`

```bash 
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Having the `--reload` flag should restart the server if you edit `llm_model.py` or `main.py`

Once the server has started, the model in question would be downloaded automaticallly.      
Output on the console will look something like this:

```
INFO:     Will watch for changes in these directories: ['/mnt/d/PROJECTS/hcai-project/llm-fast-api']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1216] using StatReload
tokenizer_config.json: 100%|████████████████████████████| 26.0/26.0 [00:00<00:00, 142kB/s]
config.json: 100%|███████████████████████████████████████| 762/762 [00:00<00:00, 1.15MB/s]
vocab.json: 100%|████████████████████████████████████| 1.04M/1.04M [00:00<00:00, 3.01MB/s]
merges.txt: 100%|██████████████████████████████████████| 456k/456k [00:00<00:00, 2.05MB/s]
tokenizer.json: 100%|████████████████████████████████| 1.36M/1.36M [00:00<00:00, 6.96MB/s]
model.safetensors: 100%|███████████████████████████████| 353M/353M [00:41<00:00, 8.54MB/s]
generation_config.json: 100%|█████████████████████████████| 124/124 [00:00<00:00, 960kB/s]
INFO:     Started server process [1218]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Interacting with the model 

Once your application is up and running, you should be able to interact with it via simple rest API.    
Go to `http://0.0.0.0:8000` and you should see Swagger up and running.      
Here you can send your prompt as a request via the `/generate` end-point.   

Or you can simply use cURL:

```curl 
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?", "max_tokens": 50}'
```

## Other details

Model used: [distilgpt2](https://huggingface.co/distilgpt2)
It's size is ~500MB

