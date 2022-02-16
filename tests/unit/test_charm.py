#!/usr/bin/env python3

import subprocess
import unittest
from unittest.mock import patch
from ops.testing import Harness
import charm


@patch.object(subprocess, "call", new=lambda *args, **kwargs: None)
class COSProxyCharmTest(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(charm.NodeExporterCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_prometheus_relation(self):
        prometheus = self.harness.charm.prometheus
        rel_name = prometheus._relation_name
        self.assertEqual(prometheus._relation_name, rel_name)

        # relation created evt
        with patch.object(prometheus, 'set_host_port') as mock:
            rel_id = self.harness.add_relation(rel_name, "prometheus2")
        # verify that it would have been called
        mock.assert_called_once()
        # call it
        prometheus.set_host_port()

        assert prometheus._relation
        print(prometheus._relation.data)

        # verify the databag contents
        unit_name = 'prometheus-node-exporter/0'
        relation_databag = prometheus._relation.data[self.harness.charm.model.unit]
        rel_data = self.harness.get_relation_data(rel_id, unit_name)
        self.assertEqual(relation_databag, rel_data)
