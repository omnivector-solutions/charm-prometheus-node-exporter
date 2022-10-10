#!/usr/bin/env python3
"""NodeExporter Peer."""
import copy
import json
import logging
import subprocess

from ops.framework import EventBase, EventSource, Object, ObjectEvents

logger = logging.getLogger()


class NodeExporterPeerAvailableEvent(EventBase):
    """Emmited in the relation_changed event when a peer comes online."""


class NodeExporterPeerRelationEvents(ObjectEvents):
    """PrometheusNodeExporter peer relation events."""

    node_exporter_peer_available = EventSource(
        NodeExporterPeerAvailableEvent
    )


class NodeExporterPeer(Object):
    """NodeExporterPeer Interface."""

    on = NodeExporterPeerRelationEvents()

    def __init__(self, charm, relation_name):
        """Initialize and observe."""
        super().__init__(charm, relation_name)
        self._charm = charm
        self._relation_name = relation_name

        self.framework.observe(
            self._charm.on[self._relation_name].relation_changed,
            self._on_relation_changed,
        )

    def _on_relation_changed(self, event):
        if self.framework.model.unit.is_leader():
            self.on.node_exporter_peer_available.emit()

    @property
    def _relation(self):
        return self.framework.model.get_relation(self._relation_name)

    def get_peer_addresses(self):
        relation = self._relation
        peer_addresses = []
        for unit in _get_active_peers(self._relation_name):
            unit_data = relation.data[unit]
            peer_addresses.append(unit_data["ingress-address"])
        peer_addresses.append(relation.data[self.model.unit]["ingress-address"])
        return peer_addresses


def _related_units(relid):
    """List of related units."""
    units_cmd_line = ["relation-list", "--format=json", "-r", relid]
    return json.loads(subprocess.check_output(units_cmd_line).decode("UTF-8")) or []


def _relation_ids(reltype):
    """List of relation_ids."""
    relid_cmd_line = ["relation-ids", "--format=json", reltype]
    return json.loads(subprocess.check_output(relid_cmd_line).decode("UTF-8")) or []


def _get_active_peers(relation_name):
    """Return the active_units."""
    active_units = []
    for rel_id in _relation_ids(relation_name):
        for unit in _related_units(rel_id):
            active_units.append(unit)
    return active_units
