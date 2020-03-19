Tested on Ubuntu Pro 18-04

## Get the server up and running
### Install Docker
Update to latest Linux version
```
sudo apt-get update
sudo apt-get upgrade
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
cd ~
git clone https://github.com/croneter/docker_mediaserver ./docker-mediaserver
git fetch --all
git pull --all
```

### Fetch latest update from Github
Any time you want to get the latest code from Github, type
```
docker-compose down
git pull --all
docker-compose up -d
```

## Configure Services

### Make adjustments for your configuration
### Set your environment variables to suit your config
**Alternatively** change your local environment variables permanently (make sure you're logged in as user `dockeruser`):
```
nano ~/.bashrc
exit
su dockeruser
```

Your public domain or IP to reach your home theater. SSL assumes you're using duckdns.org!
```
export HTPC_DOMAIN=example.duckdns.org
```
The port you want Plex to run on, e.g. 32400
```
export HTPC_PLEX_ADVERTISE_PORT=32400
```
The email you want for your SSL certificate:
```
export HTPC_LETSENCRYPT_EMAIL=
```
The Keycloak realm you're setting up:
```
export HTPC_KEYCLOAK_REALM=
```
```

export HTPC_CONFIG_DIR=<path to folder>
export HTPC_DOWNLOAD_DIR=
export HTPC_MOVIE_DIR=
export HTPC_SHOW_DIR=
export HTPC_MUSIC_DIR=
export HTPC_PICTURE_DIR=
```

### Adapt all environment files
Set-up your values in the docker environment file:
```
cp .env.example .env
nano .env
```
Set-up your secrets (sensitive stuff you'd NEVER want to leak). Choose any secure password for `keycloak_admin_pwd.txt`.
```
mkdir secrets
nano ./secrets/keycloak_admin_pwd.txt
```

## Run everything
To get everything up and running, be sure to be in your `~/docker_mediaserver` folder and type
```
docker-compose up -d
```

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
* Grab a Plex claim token from [plex.tv/claim](https://www.plex.tv/claim) - it will only be valid for 4 minutes!!
* Paste the claim token into a new file `./secrets/plex_claim.txt` and start your Plex stack.
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

### Permissions off for writing/accessing a directory?
Make sure that the user `dockeruser` owns the entire directory (use a user with sudo-rights):
```
sudo chown -R dockeruser:docker <dirname>
```

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

### Get Pi-Hole to work

#### Build DNS over HTTPS image
In the `dns-over-https` directory, do
```
docker build -t dns-over-https .
```
Then
```
docker tag dns-over-https:latest dns-over-https:staging
```

#### Rest
See https://www.smarthomebeginner.com/run-pihole-in-docker-on-ubuntu-with-reverse-proxy/. 

Create empty files before starting docker, otherwise empty directories instead of files are created. 
```
cd ~/config
mkdir pihole
mkdir pihole/log
touch ~/config/pihole/log/pihole.log
```
Pihole uses the user `root`: Log in as root, then
```
sudo chown -R root:root /home/dockeruser/config/pihole
```
In Pi-Hole, set `172.29.0.2#5053` as upstream DNS.
