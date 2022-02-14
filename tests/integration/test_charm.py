from xml.etree.ElementPath import ops
import pytest

@pytest.mark.abort_on_fail
async def test_deploy(prometheus_node_exporter_charm, ops_test):
    await ops_test.model.deploy('prometheus2')
    await ops_test.model.deploy(prometheus_node_exporter_charm)
    
    await ops_test.model.relate()
    await ops_test.model.wait_for_idle()
    
    
async def test_status(ops_test):
    unit = ops_test.model.applications["prometheus-node-exporter"].units[0]
    assert unit.workload_status == "active"
