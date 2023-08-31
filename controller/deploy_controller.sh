#!/bin/bash
TYPE=e2-medium
NAME=controller
NEW_UUID=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4 ; echo)

IP="34.122.236.144"
SUBNET="--subnet=default $IP"

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

case $ZONE in
    us-central1-a)
        echo "Using $ZONE to start $NAME-$NEW_UUID..."
        ;;
    us-east1-b)
        echo "Using $ZONE to start $NAME-$NEW_UUID..."
        ;;
    *)
        echo "Invalid zone specified: $ZONE"
        exit 1
        ;;
esac

# set this to your service account
SERVICE_ACCOUNT="slothbot@sloth-compute.iam.gserviceaccount.com"
GC_PROJECT="sloth-compute"

if [ -f secrets.sh ]; then
   source secrets.sh # truly, a travesty, sets TOKEN=token-[passphrase]
   echo "Here's where I say, hold on a second while we fire things up."
   gcloud compute project-info add-metadata --metadata token=$TOKEN
   echo;
else
   echo "Create 'secrets.sh', put a TOKEN=<token> statement in it and then rerun this script."
   echo;
   exit;
fi

SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/Laminoid/" ]; then
  echo "starting controller"
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

  pip install google-cloud
  pip install google-api-python-client
  pip install google-auth-httplib2
  pip install gunicorn
  pip install flask

  # download code
  cd /opt/
  git clone https://github.com/FeatureBaseDB/Laminoid.git
  cd /opt/Laminoid/

  # copy files
  cp bid_token.py /root/
  cp nginx.conf.controller /etc/nginx/nginx.conf

  # grab the tokens and write to nginx htpasswrd and env
  cd /root
  python3 bid_token.py controller

  # restart ngninx
  systemctl restart nginx.service

  cd /opt/Laminoid/controller
  ./start-controller.sh &

  date >> /opt/done.time

fi
EOF
)

gcloud compute instances create $NAME-$NEW_UUID \
--project=$GC_PROJECT \
--zone=$ZONE \
--machine-type=$TYPE \
--network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
$SUBNET \
--no-restart-on-failure \
$PREEMPTIBLE \
--service-account=$SERVICE_ACCOUNT \
--scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/compute,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
--create-disk=auto-delete=yes,boot=yes,device-name=instance-1,image=projects/debian-cloud/global/images/debian-11-bullseye-v20230814,mode=rw,size=100,type=projects/$GC_PROJECT/zones/$ZONE/diskTypes/pd-ssd \
--no-shielded-secure-boot \
--shielded-vtpm \
--shielded-integrity-monitoring \
--labels=type=beast \
--tags sloth,token-$TOKEN \
--reservation-affinity=any \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-controller.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create beast --target-tags beast --allow tcp:8389
echo "Password token is: $TOKEN"
echo "IP is: $IP"
