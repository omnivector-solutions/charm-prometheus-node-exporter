#!/usr/bin/python3
"""Prometheus."""
import json
import logging

from ops.framework import Object


logger = logging.getLogger(__name__)


class Prometheus(Object):
    """Prometheus."""

    def __init__(self, charm, relation):
        """Set the initial values."""
        super().__init__(charm, relation)
        self._charm = charm
        self._relation_name = relation

        self.framework.observe(
            self._charm.on[self._relation_name].relation_created,
            self._on_relation_created
        )

    @property
    def _relation(self):
        return self.framework.model.get_relation(self._relation_name)

    def _on_relation_created(self, event):
        logger.debug("## Relation created with prometheus")
        if self.framework.model.unit.is_leader():
            self.set_scrape_job_info()

    def set_scrape_job_info(self):
        """Set scrape job info on relation data."""
        relation = self.framework.model.get_relation(self._relation_name)
        topology = self._charm.topology
        if relation:
            addresses = self._charm.node_exporter_peer.get_peer_addresses()
            port = self._charm.port
            scrape_jobs = [
                {
                    "job_name": "node_exporter",
                    "metrics_path": "/metrics",
                    "static_configs": [
                        {
                            "targets": [f"{ip}:{port}" for ip in addresses],
                            "labels": {k:v for k,v in topology.items()},
                        }
                    ]
                }
            ]
            app_relation_data = relation.data[self.model.app]
            scrape_jobs = app_relation_data['scrape_jobs'] = json.dumps(scrape_jobs)
