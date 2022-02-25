"""Helpers for the tests."""

from pytest_operator.plugin import OpsTest


async def get_unit_address(ops_test: OpsTest, app_name: str, unit_num: int) -> str:
    """Find unit address for any application.

    Args:
        ops_test: pytest-operator plugin
        app_name: string name of application
        unit_num: integer number of a juju unit
    Returns:
        unit address as a string
    """
    status = await ops_test.model.get_status()
    try:
        app = status["applications"][app_name]
    except KeyError:
        raise RuntimeError(f"application {app_name} does not exist")
    try:
        address = app["units"][f"{app_name}/{unit_num}"]["public_address"]
    except KeyError:
        raise RuntimeError(
            f"unit {app_name}/{unit_num} not found. "
            f"Try with one of {app['units']}"
        )
    return address
