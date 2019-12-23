Tested on Ubuntu Pro 18-04

## Get the server up and running
### Install Docker
Update to latest Linux version
```
sudo apt-get update
sudo apt-get upgrade
```
Enable the official Docker repository by following [this docker.com guide](https://docs.docker.com/install/linux/docker-ce/ubuntu/). Install Docker:
```
sudo apt-get install docker-ce
```
Test docker
```
sudo docker run hello-world
```
Next, install Docker-Compose following [this docker.com guide](https://docs.docker.com/compose/install/). 
Add a new user `dockeruser` and make the user a member of the `docker` user group and switch to the new user. **TEMPORARILY** add the user also to the sudo group
```
sudo adduser dockeruser
sudo usermod -aG docker dockeruser
sudo usermod -aG sudo dockeruser
su dockeruser
```

## Configure Services
### SABNZBD
Add your domain to whitelist. Navigate to your chosen `config_dir`, then
```
cd sabnzbd
nano sabnzbd.ini
```
Add your domain to the `host_whitelist`-entry like this:
```
host_whitelist = <other entries>, sabnzbd.example.duckdns.org
```

### Permissions off for writing/accessing a directory?
```
sudo chown -R dockeruser:docker <dirname>
```

# Cleanup
```
docker volume rm letsencrypt media plex-database
```

# To Review
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
