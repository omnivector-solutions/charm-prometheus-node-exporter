#!/usr/bin/python3
"""Prometheus."""
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
        self.set_host_port()

    def set_host_port(self):
        """Set hostname and port in the relation data."""
        logger.debug("## set_host_port")

        if self._relation:
            relation_data = self._relation.data.get(self.model.unit)
            if relation_data:
                port = self._charm.port
                host = relation_data['ingress-address']
                logger.debug(f"## Setting host and port in prometheus {host}:{port}")

                relation_data['hostname'] = host
                relation_data['port'] = port
                relation_data['metrics_path'] = "/metrics"
