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
        prometheus = self.harness.charm.prometheus
        rel_name = prometheus._relation_name
        self.assertEqual(prometheus._relation_name, rel_name)

        # relation created evt
        with patch.object(prometheus, 'set_host_port') as mock:
            self.harness.add_relation(rel_name, 'prometheus')
            rel = self.harness.charm.model.get_relation(rel_name)
            rel_id = rel.id
            key_values = {"private-address": "127.4.5.6"}
            self.harness.add_relation_unit(rel_id, "prometheus/1")
            self.harness.update_relation_data(rel_id, "prometheus/1", key_values)

        # verify that it would have been called
        mock.assert_called_once()
        # call it
        prometheus.set_host_port()

        # verify the databag contents
        unit_name = 'prometheus-node-exporter/0'
        relation_databag = prometheus._relation.data[self.harness.charm.model.unit]
        rel_data = self.harness.get_relation_data(rel_id, unit_name)
        self.assertEqual(relation_databag, rel_data)
