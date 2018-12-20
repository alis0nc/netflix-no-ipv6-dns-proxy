# netflix-no-ipv6-dns-proxy

This is a DNS server that intentionally returns an empty result set for any
AAAA query for netflix.com or any subdomain thereof.  The intent is to force
Netflix to use IPv4 in cases where Netflix has blocked IPv6 access --
specifically, for [Hurricane Electric users who find Netflix giving them the
error](https://forums.he.net/index.php?topic=3564.0):

> You seem to be using an unblocker or proxy. Please turn off any of these
> services and try again. For more help, visit netflix.com/proxy.

Note that this server **does not** in any way circumvent Netflix's block
against these IPv6 address ranges; all it does is force Netflix to use the IPv4
Internet.

I also considered null-routing the Netflix IPv6 address ranges, but many (all?)
Netflix services are deployed in Amazon Web Services, so there's no good way to
reliably null-route Netflix without null-routing all of AWS.  Dealing with the
problem in the DNS process allows us to precisely block exactly what we want
blocked (\*.netflix.com) and nothing that we don't want blocked.

## Dependencies

The only dependency is Twisted Names for Python.

## Installation and Configuration

1. Clone the repository.
1. Build the Docker image with `docker build -t netflix-dns-proxy .`
1. Set the proper environment variables:
    * `BLACKHOLE_ADDRESS`: Set this to an IPv6 address and all blocked queries
      will return this address instead of an empty result set. The Android Netflix
      client has (for me) started getting testy when AAAA queries return nothing.
      Set this to an address in an unreachable route to resolve that issue.  I
      suggest `100::1` as this is within the RFC6666-specified discard prefix, and
      null-routing the `100::/64` address range on your router.
    * `UPSTREAM_DNS_HOST`: Set this to the upstream DNS host, if you are only
      using a single one.
    * `UPSTREAM_DNS_PORT`: Set this to the upstream DNS port, if it's not 53.
    * `RESOLV_CONF`: If you are using multiple upstream DNS servers, you will
      have to set this to the path to the `resolv.conf` file that describes them.
      I suggest using a Docker volume to persist this.
1. Run the Docker container with exporting the environment variables:
   `docker run --rm -p 10053:53 -p 10053:53/udp -e UPSTREAM_DNS_HOST -e UPSTREAM_DNS_PORT -e RESOLV_CONF -e BLACKHOLE_ADDRESS --name netflix-proxy netflix-proxy:latest`



The Netflix apps for Chromecast and Android have started **ignoring the DNS
servers announced over DHCP and will send queries directly to 8.8.8.8 and/or
8.8.4.4**. If you are running this proxy on your network's default gateway,
simply configure the LAN-facing interface with these addresses to force all
queries to them to be handled by the proxy. If you are running the DNS proxy
on another box, you will have to configure your router to NAT DNS requests to
these addresses to that other box.

Alternatively, if you block the Google Public DNS servers at the router level
this will force a Chromecast device to fallback to the DNS servers pushed via DHCP.

An example of achieving this with `iptables`:

```
iptables -I FORWARD --destination 8.8.8.8 -j REJECT
iptables -I FORWARD --destination 8.8.4.4 -j REJECT
```

Note that if you are using dnsmasq and its built-in DHCP server, and you
reconfigure it to listen on a port other than 53 for DNS, it will stop
advertising itself as a DNS server to DHCP clients.  Put `dhcp-option=6,$IP` in
`dnsmasq.conf` (changing `$IP` to the server's LAN IP) to fix this.  Note that
this will not work when dnsmasq is serving multiple different DHCP ranges,
unless you use an IP address that is reachable from all of those networks.
