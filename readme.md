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
Set-up your values in the docker environment file:
```
cp .env.example .env
nano .env
```
Set-up your secrets (sensitive stuff you'd NEVER want to leak):
```
mkdir secrets
cp plex-secrets.env.example ./secrets/plex-secrets.env
cp traefik-secrets.env.example ./secrets/traefik-secrets.env
```
Then adjust these 2 files as needed with nano:
```
nano ./secrets/plex-secrets.env
nano ./secrets/traefik-secrets.env
```

### Add users
You need to explicitly add users that will be able to login. Let's say you want to add the user `Sherlock` with the password `Holmes`. Get the hashed password like this:
```
htpasswd -nb Sherlock Holmes
```
Copy the output, e.g. `Sherlock:$apr1$C6xAwK9F$J7ozgti6Z6MccTIGMkJQd.` into a file called `userlist.txt`:
```
nano ./secrets/userlist.txt
```

## Run everything
To get everything up and running, be sure to be in your `~/docker_mediaserver` folder and type
```
docker-compose up -d
```

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

### Setup your domain with plex.tv
As we're using a reverse proxy, we need to tell Plex where to reach the PMS from outside the LAN. Make sure everything is up and running with `docker-compose up -d`, then grab `Preferences.xml` from the container and safe it to the current working directory:
```
docker cp plex:"/config/Library/Application Support/Plex Media Server/Preferences.xml" ./Preferences.xml
```
Use `nano` to edit the file and add your domain; use a comma `,` to separate several domains:
```
customConnections="http://your-domain.com:32400"
```
(see e.g. https://github.com/linuxserver/docker-plex/issues/36)
Copy the file back:
```
docker cp ./Preferences.xml plex:"/config/Library/Application Support/Plex Media Server/Preferences.xml" 
```
Restart with `docker-compose down` and `docker-compose up -d`.

### Setup Organizr
Chose a `Personal`-License if you want Radarr, Sonarr, etc. working, i.e. appearing as Homepage options. For Organizr Single Sign On, use an email address as username. Set-up the exact same email address as a user within Organizr.

Choose the following Organizr `Auth Proxy` settings in the Organizr settings:
* Auth Proxy: On
* Auth Proxy Whitelist: `0.0.0.0/0` (behind Traefik anyway)
* Auth Proxy Header Name: `X-Forwarded-User`

When adding tabs, use the following setup:
* Type: `iFrame`
* Tab Url: https://<service>.croneter-test.duckdns.org

### Permissions off for writing/accessing a directory?
Make sure that the user `dockeruser` owns the entire directory (use a user with sudo-rights):
```
sudo chown -R dockeruser:docker <dirname>
```
