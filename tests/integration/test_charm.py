"""Charm integration tests."""

import pytest
from pytest_operator.plugin import OpsTest
from requests import get

from tests.integration.helpers import get_unit_address


@pytest.mark.abort_on_fail
async def test_deploy(prometheus_node_exporter_charm, ops_test: OpsTest):
    """Verify that the deployment is successful."""
    await ops_test.model.deploy('ubuntu', num_units=3)

    # subordinate charms
    await ops_test.model.wait_for_idle(status='active')

    await ops_test.model.deploy(prometheus_node_exporter_charm, num_units=0)
    await ops_test.model.add_relation(
        'prometheus-node-exporter:juju-info',
        'ubuntu:juju-info'
    )
    await ops_test.model.wait_for_idle(status='active')

    # prom2
    await ops_test.model.deploy('prometheus2')
    await ops_test.model.add_relation(
        'prometheus2:scrape',
        'prometheus-node-exporter:prometheus'
    )
    await ops_test.model.wait_for_idle(status='active')


@pytest.mark.xfail
async def test_node_exporter_listening(ops_test):
    """Check that the node exporter is ready."""
    # node exporter does not have units (it's subordinate, so we get the unit
    # address from 'ubuntu' units); the node exporter will be listening at port
    # 9100
    for i in range(3):
        address = get_unit_address(ops_test, "ubuntu", i)
        url = f"http://{await address}:9100/metrics"
        assert get(url).status_code == 200, f'prometheus-node-exporter unreachable at {url}'
