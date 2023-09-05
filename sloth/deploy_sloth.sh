#!/bin/bash
TYPE=g2-standard-24
NAME=sloth
NEW_UUID=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4 ; echo)

PREEMPTIBLE=" \
--maintenance-policy=TERMINATE \
--provisioning-model=SPOT \
--instance-termination-action=STOP \
"

# load arguments
for arg in "$@"; do
    case $arg in
        -z=*|--zone=*)
            ZONE="${arg#*=}"
            ;;
        -p|--prod|--production)
            PROD_MODE="true"
            ;;
    esac
done

if [ "$PROD_MODE" == "true" ]; then
    unset PREEMPTIBLE
    echo "Production mode enabled..."
    IP=""
    echo
else
    echo "This instance is preemtible, unless it's started with --prod"
fi


if [ -z "$ZONE" ]; then
    echo "Need a valid zone to start [us-central1-a|us-east1-b]: --zone=us-central1-a"
    exit 1
fi

# set this to your service account
SERVICE_ACCOUNT="sloth-compute@appspot.gserviceaccount.com"
GC_PROJECT="sloth-compute"

if [ -f secrets.sh ]; then
   source secrets.sh # truly, a travesty, sets TOKEN=token-[passphrase]
   echo "Here's where I say, hold on a second while we fire things up."
   gcloud compute project-info add-metadata --metadata token=$TOKEN
   echo;
else
   echo "Create 'secrets.sh', put a TOKEN=f00bar statements in it and then rerun this script."
   echo;
   exit;
fi

SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/Laminoid/" ]; then
  echo "starting sloth services"
  cd /opt/Laminoid/sloth
  bash start-sloth.sh

else
  sudo su -
  date >> /opt/start.time

  apt-get update -y

  apt-get install apache2-utils -y
  apt-get install nginx -y
  apt-get install build-essential -y
  apt-get install unzip -y
  apt-get install python3-pip -y
  apt-get install git -y
  apt-get install gcc -y
  
  # install cuda drivers
  cd /root/
  curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output install_gpu_driver.py
  python3 /root/install_gpu_driver.py

  # download code
  cd /opt/
  git clone https://github.com/FeatureBaseDB/Laminoid.git
  cd /opt/Laminoid/sloth

  # copy files
  cp bid_token.py /root/
  cp ../nginx.conf.sloth /etc/nginx/nginx.conf

  # grab the tokens and write to nginx htpasswrd and env
  cd /root
  python3 bid_token.py sloth

  # fschat

  # huggingface
  pip install --upgrade huggingface_hub

  # huggingface_cli login
  
  # vllm takes forever
  # pip install vllm 

  # requirements (for Instructor only right now)
  cd /opt/Laminoid/sloth
  pip install -r requirements.txt

  # restart ngninx
  systemctl restart nginx.service

  # start sloth service
  bash start-sloth.sh

  date >> /opt/done.time

fi
EOF
)

gcloud compute instances create $NAME-$NEW_UUID \
--project=$GC_PROJECT \
--zone=$ZONE \
--machine-type=$TYPE \
--network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
--no-restart-on-failure \
$PREEMPTIBLE \
--service-account=$SERVICE_ACCOUNT \
--scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
--accelerator=count=2,type=nvidia-l4 \
--create-disk=auto-delete=yes,boot=yes,device-name=instance-1,image=projects/ml-images/global/images/c0-deeplearning-common-gpu-v20230807-debian-11-py310,mode=rw,size=200,type=projects/$GC_PROJECT/zones/$ZONE/diskTypes/pd-ssd \
--no-shielded-secure-boot \
--shielded-vtpm \
--shielded-integrity-monitoring \
--labels=type=beast \
--tags beast,token-$TOKEN \
--reservation-affinity=any \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-sloth.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create beast --target-tags beast --allow tcp:8888
echo "Password token is: $TOKEN"
echo "IP is: $IP"
