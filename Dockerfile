FROM alpine:3.8

# install dependencies
RUN apk --no-cache add py-twisted py2-pip && \
    pip2 install incremental constantly packaging

# copy code
COPY . /opt/netflix-no-ipv6-dns-proxy/

EXPOSE 53
EXPOSE 53/udp

WORKDIR /opt/netflix-no-ipv6-dns-proxy/
ENTRYPOINT ./server.py
