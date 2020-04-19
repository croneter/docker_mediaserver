FROM docker.elastic.co/beats/filebeat:7.6.2
COPY setup-filebeat.sh /usr/share/filebeat/setup-filebeat.sh
USER root
RUN chown root:filebeat /usr/share/filebeat/setup-filebeat.sh
RUN chmod +x /usr/share/filebeat/setup-filebeat.sh
USER filebeat
