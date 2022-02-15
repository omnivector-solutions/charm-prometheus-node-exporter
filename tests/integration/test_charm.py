from xml.etree.ElementPath import ops
import pytest

from pytest_operator.plugin import OpsTest


@pytest.mark.abort_on_fail
async def test_deploy(prometheus_node_exporter_charm, ops_test: OpsTest):
    await ops_test.model.deploy('ubuntu', num_units=3)
    await ops_test.model.deploy('telegraf', num_units=0)
    
    # subordinate charms
    await ops_test.model.add_relation(
        'telegraf:juju-info', 
        'ubuntu:juju-info'
    )
    await ops_test.model.wait_for_idle(wait_for_active=True)
    
    
    await ops_test.model.deploy(prometheus_node_exporter_charm, num_units=0)
    await ops_test.model.add_relation(
        'prometheus-node-exporter:juju-info',
        'ubuntu:juju-info'
    )
    await ops_test.model.wait_for_idle(wait_for_active=True)

    # prom2
    await ops_test.model.deploy('prometheus2')
    await ops_test.model.add_relation(
        'prometheus2:target',
        'telegraf:prometheus-client'
    )
    await ops_test.model.add_relation(
        'prometheus2:scrape',
        'prometheus-node-exporter:prometheus'
    )
    await ops_test.model.wait_for_idle(wait_for_active=True)
    
    
async def test_status(ops_test):
    unit = ops_test.model.applications["prometheus-node-exporter"].units[0]
    assert unit.workload_status == "active"
