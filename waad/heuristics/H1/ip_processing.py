"""This module implements an IP Processing block."""


import ipaddress
from typing import Dict, List, Union


class IPProcessing:
    """This class implements an IP processing block. It classifies IPs between public, private, IPv4, IPv6... 

    Attributes:
        ips (List[str]): List of strings representing the IPs of a dataset.
    """

    def __init__(self, ips: List[str]):
        self.ips = []
        self.others = []
        for ip in ips:
            try:
                temp = ip.split("_")[-1]  # to remove once you are not working with ips prefixed 'priv_' or 'pub_' anymore
                self.ips.append(ipaddress.ip_address(temp))
            except Exception:
                self.others.append(ip)
        self.ipv4s: List[ipaddress.IPv4Address] = []
        self.ipv6s: List[ipaddress.IPv6Address] = []
        self.private_ipv4s: List[ipaddress.IPv4Address] = []
        self.public_ipv4s: List[ipaddress.IPv4Address] = []
        self.loopback_ipv4s: List[ipaddress.IPv4Address] = []
        self.private_ipv6s: List[ipaddress.IPv6Address] = []
        self.public_ipv6s: List[ipaddress.IPv6Address] = []
        self.loopback_ipv6s: List[ipaddress.IPv6Address] = []

    def run(self):
        # Classify into IPv4 and IPv6
        temp = IPProcessing.classify_ipv4_ipv6(self.ips)
        self.ipv4s = temp["IPv4"]
        self.ipv6s = temp["IPv6"]

        # Classify IPv4 into public and private
        temp = IPProcessing.classify_public_private_loopback_ips(self.ipv4s)
        self.private_ipv4s = temp["private"]
        self.public_ipv4s = temp["public"]
        self.loopback_ipv4s = temp["loopback"]

        # Classify IPv6 into public, private and loopback
        temp = IPProcessing.classify_public_private_loopback_ips(self.ipv6s)
        self.private_ipv6s = temp["private"]
        self.public_ipv6s = temp["public"]
        self.loopback_ipv6s = temp["loopback"]

    @staticmethod
    def binary_ip_to_dec(binary_ipv4: str):
        """Convert a binary IPv4 into its corresponding dotted decimal format."""
        return ".".join(str(int(binary_ipv4[i : i + 8], 2)) for i in range(0, 32, 8))

    @staticmethod
    def classify_ipv4_ipv6(ips: List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]) -> Dict[str, List[str]]:
        res: Dict = {"IPv4": [], "IPv6": []}
        for ip in ips:
            if isinstance(ip, ipaddress.IPv4Address):
                res["IPv4"].append(ip)
            elif isinstance(ip, ipaddress.IPv6Address):
                res["IPv6"].append(ip)
        return res

    @staticmethod
    def classify_public_private_loopback_ips(ips: List[Union[ipaddress.IPv4Address, ipaddress.IPv6Address]]) -> Dict[str, List[str]]:
        res: Dict = {"public": [], "private": [], "loopback": []}
        for ip in ips:
            if ip.is_loopback:
                res["loopback"].append(ip)
            else:
                if ip.is_private:
                    res["private"].append(ip)
                elif ip.is_global:
                    res["public"].append(ip)
        return res
