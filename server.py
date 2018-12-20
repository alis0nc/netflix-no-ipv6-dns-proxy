#!/usr/bin/env python

from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server
from os import environ

DNS_PORT = 53
LISTEN_ADDRESS = '::'

class BlockNetflixAAAAResolver(object):
    def __init__(self, blackhole_address):
        self.blackhole_address = blackhole_address

    def __shouldBlock(self, query):
        parts = query.name.name.split(b'.')
        if len(parts) < 2:
            return False
        penultimateDomainPart = parts[-2]

        return query.type == dns.AAAA and penultimateDomainPart in (b'netflix', b'nflximg', b'nflxext', b'nflxvideo', b'nflxso')

    def query(self, query, timeout=None):
        if self.__shouldBlock(query):
            results = []

            if self.blackhole_address is not None:
                results.append(
                    dns.RRHeader(
                        name=query.name.name,
                        type=dns.AAAA,
                        payload=dns.Record_AAAA(address=blackhole)
                    )
                )

            return defer.succeed((results, [], []))
        else:
            return defer.fail(error.DomainError())

def main(resolv_conf, upstream_dns_host, upstream_dns_port, blackhole_address):
    print resolv_conf
    factory = server.DNSServerFactory(
        clients=[
            BlockNetflixAAAAResolver(blackhole_address),
            client.Resolver(
                servers=[(upstream_dns_host, int(upstream_dns_port))],
                resolv=resolv_conf
            )
        ]
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(DNS_PORT, protocol, interface=LISTEN_ADDRESS)
    reactor.listenTCP(DNS_PORT, factory, interface=LISTEN_ADDRESS)

    reactor.run()

if __name__ == '__main__':
    raise SystemExit(main(
        environ.get('RESOLV_CONF', None),
        environ.get('UPSTREAM_DNS_HOST', None),
        environ.get('UPSTREAM_DNS_PORT', 53),
        environ.get('BLACKHOLE_ADDRESS', None)
    ))
