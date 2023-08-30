# Laminoid
Laminoid is a stupid simple model instance manager for Google Compute. It provides a reverse proxy for "authentication". This type of boxing has been done before in production for many years with no issues. Your milage may vary.

## Models
Laminoid deploys boxes onto Google Cloud. These boxes contain graphics cards, which can run models.

### Instructor Embeddings
Laminoid currently supports [Instructor Large](https://huggingface.co/hkunlp/instructor-large) or [Instructor XL](https://huggingface.co/hkunlp/instructor-xl). Instructor also has a [whitepaper](https://arxiv.org/abs/2212.09741) you can read.

Subsequent improvements to this repo will add support for other models, like Llama 2. We're going to need A100s to do this, however. Looking at you Google.

## Flask/NGINX Token Setup
This deployment uses a simple token assigned to the network tags on the box when it starts. On the box you start these on (fastener box coming soon) you'll create a `secrets.sh` file with the box token in it.

Using the box requires a username/password via a reverse proxy. The username is in `nginx.conf.sloth` and is `sloth`.

## Github Setup
You could possibly move this to your own repo, changing things. If you do, change the `deploy_sloth.sh` script to reflect the Github repo.

## Google Compute Setup
Change the `deploy_sloth.sh` script to use your Google service account. You can change zones, but the ones listed are known to have the L4s for boxes.

You may want to change the number of GPUs attached.

## Deploy
Run this to deploy:

```
./deploy_sloth.sh --zone us-central1-a
```

## Use
To run the Instruct service, enter the following from an ssh console into the box:

```
./start-sloth.sh
```

### Call It
To embed something, use curl:

```
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"sentences": ["The sun rises in the east.", "Cats are curious animals.", "Rainbows appear after the rain."]}' \
     https://box-ip:8888/embed
```

I had ChatGPT write that, so it could be wrong.

## NOTES
CUDA runs out of memory sometimes, likely due to gunicorn threading loading a seperate model into the GPU. I have no idea what's going on with it so don't make that number bigger unless you want to figure it out.

