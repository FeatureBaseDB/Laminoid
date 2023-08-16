#!/bin/bash
TYPE=a2-highgpu-1g
NAME=beast
NEW_UUID=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4 ; echo)

ZONE=$2
OPTION=$1
PREEMPTIBLE="--preemptible"
UBUNTU_VERSION="ubuntu-2204-jammy-v20230114"
IP=""

echo "This instance is preemtible, unless it's started with --prod";
case $OPTION in
    -p|--prod|--production)
       unset PREEMPTIBLE
       echo "Production mode enabled..."
       IP=""
       echo;
esac

case $ZONE in
    us-central1-a)
        echo "Using $ZONE to start beast..."
        ;;
    us-east1-b)
        echo "Using $ZONE to start beast..."
        ;;
    *)
        echo "Need a valid zone to start, such as us-central1-a or us-east1-b"
        exit
        ;;
esac

if [ -f secrets.sh ]; then
   source secrets.sh # truly, a travesty, sets TOKEN=token-[passphrase]
   echo "Here's where I say, hold on a second while we fire things up."
   gcloud compute project-info add-metadata --metadata token=$TOKEN
   echo;
else
   echo "Create 'secrets.sh', put a TOKEN=f00bar and SK=xxx statements in it and then rerun this script."
   echo;
   exit;
fi

SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/beast/" ]; then
  echo "starting beast"
else
  sudo su -
  date >> /opt/start.time

  apt-get update -y
  apt-get install build-essential -y
  
  apt-get install unzip -y
  apt-get install python3-pip -y
  pip install --upgrade huggingface_hub
  
  # 5.10.0-24-cloud-amd64 headers
  sudo apt-get install linux-headers-5.10.0-24-cloud-amd64 -y

  # install cuda drivers
  wget -q https://storage.googleapis.com/sloth-services/cuda_11.8.0_520.61.05_linux.run.3
  # bash cuda_11.8.0_520.61.05_linux.run --silent

  # download code
  apt-get install git -y
  cd /opt/
  git clone https://github.com/FeatureBaseDB/Laminoid.git
  cd /opt/Laminoid/

  cp token.py /root/

  apt-get install apache2-utils -y
  apt-get install nginx -y
  
  cp nginx.conf.beast /etc/nginx/nginx.conf

  # grab the tokens and write to nginx htpasswrd and env
  cd /root
  python3 token.py beast

  # start training
  # ./start-training.sh

  # restart ngninx
  systemctl restart nginx.service

  date >> /opt/done.time

fi
EOF
)

gcloud compute instances create $NAME-$NEW_UUID \
--project=sloth-compute \
--zone=$ZONE \
--machine-type=$TYPE \
--network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
--no-restart-on-failure \
--maintenance-policy=TERMINATE \
--provisioning-model=SPOT \
--instance-termination-action=STOP \
--service-account=291267903070-compute@developer.gserviceaccount.com \
--scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
--accelerator=count=1,type=nvidia-tesla-a100 \
--create-disk=auto-delete=yes,boot=yes,device-name=instance-1,image=projects/debian-cloud/global/images/debian-11-bullseye-v20230814,mode=rw,size=100,type=projects/sloth-compute/zones/us-central1-f/diskTypes/pd-balanced \
--no-shielded-secure-boot \
--shielded-vtpm \
--shielded-integrity-monitoring \
--labels=type=beast \
--tags beast,token-$TOKEN \
--reservation-affinity=any \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-beast.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create beast --target-tags beast --allow tcp:8389
echo "Password token is: $TOKEN"
echo "IP is: $IP"
