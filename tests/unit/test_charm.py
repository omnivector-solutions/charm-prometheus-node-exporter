#!/usr/bin/env python3

"""COS Proxy Charm Test."""

import charm
import subprocess
import unittest
from ops.testing import Harness
from unittest.mock import patch


@patch.object(subprocess, "call", new=lambda *args, **kwargs: None)
class COSProxyCharmTest(unittest.TestCase):
    """Charm test."""

    def setUp(self):
        """Set the harness up."""
        self.harness = Harness(charm.NodeExporterCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_prometheus_relation(self):
        """Check that the charm and prom are related."""
        charm = self.harness.charm
        prometheus = charm.prometheus

        # relation created evt
        with patch.object(prometheus, 'set_host_port') as mock:
            rel_id = self.harness.add_relation(
                prometheus._relation_name,
                'prometheus')
            key_values = {"ingress-address": "127.4.5.6"}
            self.harness.add_relation_unit(rel_id, "prometheus/1")
            self.harness.update_relation_data(
                rel_id,
                charm.unit.name,
                key_values
            )

        # verify that it would have been called
        mock.assert_called_once()
        # call it
        prometheus.set_host_port()

        # verify the databag contents
        rel_data = self.harness.get_relation_data(rel_id, charm.unit.name)
        assert rel_data == {
            'ingress-address': '127.4.5.6',
            'hostname': '127.4.5.6',
            'port': '9100',
            'metrics_path': '/metrics'
        }
