#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import shutil
from pathlib import Path

import pytest
from pytest_operator.plugin import OpsTest


@pytest.fixture(scope="module")
async def prometheus_node_exporter_charm(ops_test: OpsTest) -> Path:
    """Charm used for integration testing."""
    charm = await ops_test.build_charm(".")
    return charm
