# Laminoid
Laminoid is a stupid simple instance manager for Google Compute to run machine learning models. 

Laminoid provides a reverse proxy for "authentication".

## Models
Laminoid deploys boxes onto Google Cloud. These boxes contain graphics cards, which can run models.

### Instructor Embeddings
Laminoid currently supports [Instructor Large](https://huggingface.co/hkunlp/instructor-large) or [Instructor XL](https://huggingface.co/hkunlp/instructor-xl). Instructor also has a [whitepaper](https://arxiv.org/abs/2212.09741) you can read.

Subsequent improvements to this repo will add support for other models, like Llama 2. We're going to need A100s to do this without QLoRA, however. Looking at you, Google.

## Flask/NGINX Token Setup
This deployment uses a simple token assigned to the network tags on the box when it starts. For now, you'll need to start these manually. A fastener box for starting them via an API is coming soon, but you can do this from the Google Shell in the Google Cloud Console. 

You'll create a `secrets.sh` file with the box token in it before you do the deployment below.

Using the box requires a username/password via a reverse proxy. The username is in `nginx.conf.sloth` and is `sloth`.

## Github Setup
You could possibly move this to your own repo, changing things. If you do, change the `deploy_sloth.sh` script to reflect the Github repo.

## Google Compute Setup
Change the `deploy_sloth.sh` script to use your Google service account and project names. You can change zones, but the ones listed are known to have the L4s for boxes.

You may want to change the number of GPUs attached if you like spending money.

## Deploy
Run this to deploy the box:

```
./deploy_sloth.sh --zone us-central1-a
```

## Setup
SSH into the box and then run the following commands.

Setup the conda environment:

```
conda create -n sloth python=3.10
conda activate sloth
```

Install the requirements:

```
pip install -r requirements.txt
```

Open up the firewall (on the box or the shell you deployed from):

```
gcloud compute firewall-rules create beast --target-tags beast --allow tcp:8888
```

## Use
To run the Instruct service, enter the following from an SSH console into the box:

```
bash start-sloth.sh
```

I'd put all of this into the deploy script, but I'm working on figuring out how to use `conda` to do it automatically with another account besides root.

### Call It
To embed something from somewhere, use curl:

```
curl -X POST \
     -u sloth:f00bar \
     -H "Content-Type: application/json" \
     -d '{"sentences": ["The sun rises in the east.", "Cats are curious animals.", "Rainbows appear after the rain."]}' \
     http://box-ip:8888/embed
```

I had ChatGPT write that, so it could be wrong.

## NOTES
CUDA runs out of memory sometimes, likely due to gunicorn threading loading a seperate model into the GPU. I have no idea what's going on with it so don't make that number bigger unless you want to figure it out.

