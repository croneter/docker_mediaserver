#!/usr/bin/with-contenv bash

# Remove header
sed -i '/X-Frame-Options/d' /etc/lighttpd/lighttpd.conf

# We stop it, watchdog will restart it with our conf
/etc/init.d/lighttpd stop
