Tested on Ubuntu Pro 18-04

## Get the server up and running
### Install Docker
Update to latest Linux version
```
sudo apt-get update
sudo apt-get dist-upgrade
```
Enable the official Docker repository by following [this docker.com guide](https://docs.docker.com/install/linux/docker-ce/ubuntu/). Then install Docker:
```
sudo apt-get install docker-ce
```
Test docker:
```
sudo docker run hello-world
```
Next, install Docker-Compose following [this docker.com guide](https://docs.docker.com/compose/install/). 
Then add a new user `dockeruser` and make the user a member of the `docker` user group and switch to the new user.
```
sudo adduser dockeruser
sudo usermod -aG docker dockeruser
su dockeruser
```
From now on, always use `dockeruser` for any operations.

### Get Docker Swarm up and running
Replace the IP `192.168.0.2` with your own for the swarm, e.g. simply the server's own IP if your running everything on a single host/node/server:
```
docker swarm init --advertise-addr 192.168.0.2
```

### Pull code from Github
Navigate to a folder where you'd like to set-up this docker-compose recipe and your personal docker setup, e.g. `~/docker-mediaserver`. Get everything from Github:
```
cd ~/
git clone https://github.com/croneter/docker_mediaserver ./docker-mediaserver
cd docker-mediaserver
git fetch --all
git pull --all
```

### Fetch latest update from Github
Any time you want to get the latest code from Github, type
```
git pull
```

## Configuration Using Docker

### Set Your Secrets
Create the secrets that we need to run our stacks. Choose any strong master/admin password for Keycloak with `keycloak_admin_password`. Grab your personal token from [duckdns.org](https://www.duckdns.org/) for `traefik_duckdns_token`.
```
printf <secret> | docker secret create keycloak_admin_password -
printf <secret> | docker secret create traefik_duckdns_token -
```
If you ever want to edit a secret, simply remove it first with
```
docker secret rm <name of the secret, e.g. keycloak_admin_password>
```
You'll also need a short-lived Plex secret once, see below.

### Set your environment variables to suit your config
Run the dedicated script; be sure to log-out and log-in again after doing so!
```
python setup.py
```
Note done all the values you insert; you'll need some below. You'll also probably need to run that command once per Docker swarm node.

### Adapt all environment files
Set-up your values in all the environment files:
```
nano forward-auth.env.example
nano keycloak.env.example
nano pihole.env.example
```
Be sure to safe each file WITHOUT the ending `.example`, so e.g. as `forward-auth.env`.

## Run The Stacks
To get everything up and running, be sure to be in your `~/docker_mediaserver` folder and type
```
python start.py
```
Be sure to first start the stack `overlay` as that stack is needed for everything else, but also `traefik` and `keycloak` should be up and running at any point of time.    
Alternatively, type directly:
```
docker stack deploy -c overlay.yml overlay
docker stack deploy -c traefik.yml traefik
docker stack deploy -c keycloak.yml keycloak
```

### Plex
Before running the Plex stack, you'll need to set your short-lived Plex claim. See below.

### Customize Your Lidarr Docker Image
Lidarr is customized to enable you to automatically convert FLAC to MP3. To enable automatic conversation, customize Lidarr:
* Navigate to Settings -> Connection
* Create a new Custom Connection
* For the path, add `/usr/local/bin/flac2mp3.sh`. Only select
  * "On Release Import"
  * "On Upgrade"

### Build Your DNS Over HTTPS image
In the `dns-over-https` directory, do
```
docker build -t dns-over-https .
```
Then
```
docker tag dns-over-https:latest dns-over-https:staging
```

## Setting Up Your Services Using a Browser
### Setting up Keycloak
On first "boot" of your server, visit `https://keycloak.<yourdomain>`. Use your Keycloak admin credentials to log-in.
* Create a new realm. Paste that realm's name into `.env` as `HTPC_KEYCLOAK_REALM`
* Create a new client for our container `forward-auth`. Set `Access Type` to `Confidential`. Set one `Valid Redirect URIs` to `https://auth.<yourdomain>/_oauth`
* Copy the `Client ID` and paste it as `KEYCLOAK_CLIENT_ID` in our `.env` file
* In the Credentials tab, copy the `Secret` and paste it as `KEYCLOAK_CLIENT_SECRET` in our `.env` file. 
* Reboot your server with `docker-compose down`, then `docker-compose up`

### Configure SABNZBD once
Add your domain to whitelist. Navigate to your chosen `config_dir`, then
```
cd sabnzbd
nano sabnzbd.ini
```
Add your domain to the `host_whitelist`-entry like this:
```
host_whitelist = <other entries>, sabnzbd.example.duckdns.org
```
Deactivate the `X_Frame_Options` to allow iFrames for Organizr by editing the line to
```
x_frame_options = 0
```

### Setup your Plex Media Server
You need to have a valid Plex claim ONCE in order to claim your new Plex Media Server and tie it to your account. 
* Grab a Plex claim token from [plex.tv/claim](https://www.plex.tv/claim) - it will only be valid for 4 minutes!!
* Paste the claim token into a new Docker secret: 
```
printf <secret> | docker secret create plex_claim -
```
* Start your Plex stack.
* Then connect to Plex by visiting `https://example.duckdns.org:<YOUR EXTERNAL PLEX PORT>` and claim your PMS.
* Make sure your PMS can be reached from outside: navigate to the PMS settings, then `Remote Access`. Set `Manually specify public port` to your custom port

### Setup Organizr
Choose a `Personal`-License if you want Radarr, Sonarr, etc. working, i.e. appearing as Homepage options. For Organizr Single Sign On, use an email address as username. Set-up the exact same email address as a user within Organizr.

Choose the following Organizr `Auth Proxy` settings in the Organizr settings:
* Auth Proxy: On
* Auth Proxy Whitelist: `0.0.0.0/0`
* Auth Proxy Header Name: `X-Forwarded-User`

When adding tabs, use the following setup:
* Type: `iFrame`
* Tab Url: https://<service>.croneter-test.duckdns.org

### Pi-Hole
See https://www.smarthomebeginner.com/run-pihole-in-docker-on-ubuntu-with-reverse-proxy/ for configuration tipps. 


Pihole uses the user `root`: Log in to Linux as a user with sudo-rights, then
```
sudo chown -R root:root /home/dockeruser/config/pihole
```
In Pi-Hole, set `172.29.0.2#5053` as upstream DNS and make sure all other DNS entries are disabled. If that does not work, use `1.1.1.1`



## Other Useful Stuff
### Power Management
List current hard drives with `lsblk`. Use [TLP](https://linrunner.de/en/tlp/docs/tlp-linux-advanced-power-management.html):
```
sudo apt-get update
sudo apt install tlp tlp-rdw 
```
Show the current configuration of TLP with
```
sudo tlp-stat -c
```
See [here for configuration options](https://linrunner.de/en/tlp/docs/tlp-configuration.html). E.g change the config to power down the second of a total of 2 hard drives with `sudo nano /etc/default/tlp` and adding
```
# Spin down the second of 2 hard disks after 5min
DISK_SPINDOWN_TIMEOUT_ON_AC="0 60"
DISK_SPINDOWN_TIMEOUT_ON_BAT="0 60"
```
Check whether the hard disk `/dev/sda` is powered down (wait 5 min!) with
```
sudo hdparm -C /dev/sda
```

### Permissions off for writing/accessing a directory?
Make sure that the user `dockeruser` owns the entire directory (use a user with sudo-rights):
```
sudo chown -R dockeruser:docker <dirname>
```
