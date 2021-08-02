#!/usr/bin/env python3
# Copyright 2021 Omnivector Solutions.
# See LICENSE file for licensing details.

"""Prometheus Node Exporter Charm."""

import logging
import os
import shlex
import shutil
import subprocess
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib import request

from jinja2 import Environment, FileSystemLoader

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus

from prometheus_node_exporter import Prometheus

logger = logging.getLogger(__name__)


class NodeExporterCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        """Initialize charm."""
        super().__init__(*args)

        self.prometheus = Prometheus(self, "prometheus")

        # juju core hooks
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.stop, self._on_stop)

        # action hooks
        self.framework.observe(self.on.get_labels_action, self._on_get_labels_action)

    @property
    def port(self):
        """Return the port that node-exporter listens to."""
        return self.model.config.get("listen-address").split(":")[1]

    def _on_install(self, event):
        logger.debug("## Installing charm")
        self.unit.status = MaintenanceStatus("Installing node-exporter")
        self._set_charm_version()
        _install_node_exporter(self.model.config.get("node-exporter-version"))

        self.unit.status = ActiveStatus("node-exporter installed")

    def _on_upgrade_charm(self, event):
        """Perform upgrade operations."""
        logger.debug("## Upgrading charm")
        self.unit.status = MaintenanceStatus("Upgrading node-exporter")
        self._set_charm_version()

        self.unit.status = ActiveStatus("node-exporter upgraded")

    def _on_config_changed(self, event):
        """Handle configuration updates."""
        logger.debug("## Configuring charm")

        params = dict()
        params["listen_address"] = self.model.config.get("listen-address")

        logger.debug(f"## Configuration options: {params}")
        _render_sysconfig(params)
        subprocess.call(["systemctl", "restart", "node_exporter"])

        self.prometheus.set_relation_data()

    def _on_start(self, event):
        logger.debug("## Starting daemon")
        subprocess.call(["systemctl", "start", "node_exporter"])
        self.unit.status = ActiveStatus("node-exporter started")

    def _on_stop(self, event):
        logger.debug("## Stopping daemon")
        subprocess.call(["systemctl", "stop", "node_exporter"])
        subprocess.call(["systemctl", "disable", "node_exporter"])
        _uninstall_node_exporter()

    def _set_charm_version(self):
        """Set the application version for Juju Status."""
        self.unit.set_workload_version(Path("version").read_text().strip())

    def assemble_labels(self) -> dict:
        """Parse configs and actions to assemble metrics labels."""

        labels = self.model.config.get("labels").replace('', '')
        logger.debug(f"## got {labels} from config")

        return labels

    def _on_get_labels_action(self, event) -> None:
        labels = self.assemble_labels()
        event.set_results(labels)


def _install_node_exporter(version: str, arch: str = "amd64"):
    """Download appropriate files and install node-exporter.

    This function downloads the package, extracts it to /usr/bin/, create
    node-exporter user and group, and creates the systemd service unit.

    Args:
        version: a string representing the version to install.
        arch: the hardware architecture (e.g. amd64, armv7).
    """

    logger.debug(f"## Installing node_exporter {version}")

    # Download file
    url = f"https://github.com/prometheus/node_exporter/releases/download/v{version}/node_exporter-{version}.linux-{arch}.tar.gz"
    logger.debug(f"## Downloading {url}")
    output = Path("/tmp/node-exporter.tar.gz")
    fname, headers = request.urlretrieve(url, output)

    # Extract it
    tar = tarfile.open(output, 'r')
    with TemporaryDirectory(prefix="omni") as tmp_dir:
        logger.debug(f"## Extracting {tar} to {tmp_dir}")
        tar.extractall(path=tmp_dir)

        logger.debug("## Installing node_exporter")
        source = Path(tmp_dir) / f"node_exporter-{version}.linux-{arch}/node_exporter"
        shutil.copy2(source, "/usr/bin/node_exporter")

    # clean up
    output.unlink()

    _create_node_exporter_user_group()
    _create_systemd_service_unit()
    _render_sysconfig({"listen_address": "0.0.0.0:9100"})


def _uninstall_node_exporter():
    logger.debug("## Uninstalling node-exporter")

    # remove files and folders
    Path("/usr/bin/node_exporter").unlink()
    Path("/etc/systemd/system/node_exporter.service").unlink()
    Path("/etc/sysconfig/node_exporter").unlink()
    shutil.rmtree(Path("/var/lib/node_exporter/"))

    # remove user and group
    user = "node_exporter"
    group = "node_exporter"
    subprocess.call(["userdel", user])
    subprocess.call(["groupdel", group])


def _create_node_exporter_user_group():
    logger.debug("## Creating node_exporter group")
    group = "node_exporter"
    cmd = f"groupadd {group}"
    subprocess.call(shlex.split(cmd))

    logger.debug("## Creating node_exporter user")
    user = "node_exporter"
    cmd = f"useradd --system --no-create-home --gid {group} --shell /usr/sbin/nologin {user}"
    subprocess.call(shlex.split(cmd))


def _create_systemd_service_unit():
    logger.debug("## Creating systemd service unit for node_exporter")
    charm_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = Path(charm_dir) / "templates"

    service = "node_exporter.service"
    shutil.copyfile(template_dir / service, f"/etc/systemd/system/{service}")

    subprocess.call(["systemctl", "daemon-reload"])
    subprocess.call(["systemctl", "enable", service])


def _render_sysconfig(context: dict) -> None:
    """Render the sysconfig file.

    `context` should contain the following keys:
        listen_address: a string specifiyng the address to listen to, e.g. 0.0.0.0:9100
    """
    logger.debug("## Writing sysconfig file")

    charm_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = Path(charm_dir) / "templates"
    template_file = "node_exporter.tmpl"

    sysconfig = Path("/etc/sysconfig/")
    if not sysconfig.exists():
        sysconfig.mkdir()

    varlib = Path("/var/lib/node_exporter")
    textfile_dir = varlib / "textfile_collector"
    if not textfile_dir.exists():
        textfile_dir.mkdir(parents=True)
    shutil.chown(varlib, user="node_exporter", group="node_exporter")
    shutil.chown(textfile_dir, user="node_exporter", group="node_exporter")

    environment = Environment(loader=FileSystemLoader(template_dir))
    template = environment.get_template(template_file)

    target = sysconfig / "node_exporter"
    if target.exists():
        target.unlink()
    target.write_text(template.render(context))


if __name__ == "__main__":
    main(NodeExporterCharm)
