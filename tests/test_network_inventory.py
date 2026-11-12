"""Tests for read-only LEOS network inventory."""

import unittest
from unittest.mock import patch

from control_center import network


class NetworkTests(unittest.TestCase):
    def test_default_route_is_decoded_from_proc(self):
        route = "Iface Destination Gateway Flags RefCnt Use Metric\nwlan0 00000000 0101A8C0 0003 0 0 0\n"
        with patch.object(network, "_read", return_value=route):
            self.assertEqual(network._default_route(), ("wlan0", "192.168.1.1"))

    def test_default_route_falls_back_to_ipv6_on_ipv6_only_networks(self):
        route_files = {
            "/proc/net/route": "Iface Destination Gateway Flags RefCnt Use Metric\n",
            "/proc/net/ipv6_route": (
                "0" * 32 + " 00 " + "0" * 32 + " 00 "
                + "fe800000000000000000000000000001 "
                + "00000000 00000000 00000000 00000001 wlan0\n"
            ),
        }
        with patch.object(
            network, "_read",
            side_effect=lambda path: route_files.get(str(path), ""),
        ):
            self.assertEqual(network._default_route(), ("wlan0", "fe80::1"))

    def test_default_route_requires_an_active_ipv4_route(self):
        route = (
            "Iface Destination Gateway Flags RefCnt Use Metric\n"
            "eth0 00000000 0101A8C0 0002 0 0 0\n"
        )
        with patch.object(
            network, "_read",
            side_effect=lambda path: route if str(path) == "/proc/net/route" else "",
        ):
            self.assertEqual(network._default_route(), ("", ""))

    def test_dns_servers_are_unique_and_limited(self):
        content = "nameserver 1.1.1.1\nnameserver 8.8.8.8\nnameserver 1.1.1.1\n"
        with patch.object(network, "_read", return_value=content):
            self.assertEqual(network._dns_servers(), ["1.1.1.1", "8.8.8.8"])

    def test_wireless_details_parse_ssid_and_signal(self):
        output = "Connected to aa:bb\n\tSSID: LEOS-WIFI\n\tsignal: -52 dBm\n"
        with patch.object(network, "_run", return_value=output):
            self.assertEqual(
                network._wireless_details("wlan0"),
                {"ssid": "LEOS-WIFI", "signal": "-52 dBm"},
            )

    def test_rates_use_counter_delta_and_never_go_negative(self):
        with (
            patch.object(network.Path, "iterdir", return_value=[network.Path("/sys/class/net/eth0")]),
            patch.object(network, "_read", side_effect=lambda path: {
                "/sys/class/net/eth0/operstate": "up",
                "/sys/class/net/eth0/statistics/rx_bytes": "3000",
                "/sys/class/net/eth0/statistics/tx_bytes": "1000",
                "/proc/net/route": "Iface Destination Gateway Flags RefCnt Use Metric\n",
                "/etc/resolv.conf": "",
            }.get(str(path), "")),
            patch.object(network, "_default_route", return_value=("", "")),
            patch.object(network, "_wireless_details", return_value={"ssid": "Non connecté", "signal": "—"}),
            patch.object(network, "_run", return_value="eth0 UP 192.168.1.5/24"),
        ):
            result = network.collect_network_snapshot({"eth0": (952, 2000)}, 2.0)
        self.assertEqual(result["interfaces"][0]["downloadRate"], "1.0 Ko/s")
        self.assertEqual(result["interfaces"][0]["uploadRate"], "0 o/s")

    def test_missing_interfaces_are_reported_as_offline(self):
        with (
            patch.object(network.Path, "iterdir", side_effect=OSError),
            patch.object(network, "_default_route", return_value=("", "")),
            patch.object(network, "_dns_servers", return_value=[]),
            patch.object(network, "_wireless_details", return_value={"ssid": "Non connecté", "signal": "—"}),
        ):
            result = network.collect_network_snapshot()
        self.assertEqual(result["status"], "Hors ligne")
        self.assertEqual(result["interfaces"], [])
        self.assertEqual(result["gateway"], "Non détectée")


if __name__ == "__main__":
    unittest.main()
