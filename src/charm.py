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

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus


from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider


JOBS = [
    {
        "static_configs": [
            {
                "targets": ["*:9100"]
            }
        ]
    }
]

logger = logging.getLogger(__name__)


class NodeExporterCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        """Initialize charm."""
        super().__init__(*args)
        self.metrics_endpoint = MetricsEndpointProvider(self, jobs=JOBS)

        # juju core hooks
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.stop, self._on_stop)

    def _on_install(self, event):
        logger.debug("## Installing charm")
        self.unit.status = MaintenanceStatus("Installing node-exporter")
        self._set_charm_version()
        _install_node_exporter(
            self.model.config.get('listen-address'),
            self.model.config.get("node-exporter-version")
        )

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

        _render_sysconfig(self.model.config.get("listen-address"))
        subprocess.call(["systemctl", "restart", "node_exporter"])
        #self._on_set_scrape_job_info(event)

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


def _install_node_exporter(listen_address: str, version: str, arch: str = "amd64"):
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
    _render_sysconfig(listen_address)


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


def _render_sysconfig(listen_address: str) -> None:
    """Render the sysconfig file.

    `context` should contain the following keys:
        listen_address: a string specifiyng the address to listen to, e.g. 0.0.0.0:9100
    """
    logger.debug("## Writing sysconfig file")

    charm_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = Path(charm_dir) / "templates" / "node_exporter.tmpl"

    sysconfig = Path("/etc/sysconfig/")
    if not sysconfig.exists():
        sysconfig.mkdir()

    varlib = Path("/var/lib/node_exporter")
    textfile_dir = varlib / "textfile_collector"
    if not textfile_dir.exists():
        textfile_dir.mkdir(parents=True)
    shutil.chown(varlib, user="node_exporter", group="node_exporter")
    shutil.chown(textfile_dir, user="node_exporter", group="node_exporter")

    template_as_string = template_file.read_text()

    target = sysconfig / "node_exporter"
    if target.exists():
        target.unlink()


    target.write_text(template_as_string.format(listen_address=listen_address))


if __name__ == "__main__":
    main(NodeExporterCharm)
