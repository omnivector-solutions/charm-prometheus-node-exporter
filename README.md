# Prometheus Node Exporter Charm

Prometheus [node exporter](https://github.com/prometheus/node_exporter) for
machine metrics.

## Quickstart

Deploy the `prometheus-node-exporter` charm and relate it to the units you want
to export the metrics:

```bash
$ juju deploy prometheus-node-exporter
$ juju relate prometheus-node-exporter foo
```

The charm can register it's scrape target with Prometheus via relation to the
[Prometheus charm](https://charmhub.io/prometheus2):

```bash
$ juju relate prometheus-node-exporter prometheus2
```

## Developing

We supply a `Makefile` with a target to build the charm:

```bash
$ make charm
```

## Testing
Run `tox -e ALL` to run unit + integration tests and verify linting.

## Contact

**We want to hear from you!**

Email us @ [info@omnivector.solutions](mailto:info@omnivector.solutions)

## Bugs

In the case things aren't working as expected, please
[file a bug](https://github.com/omnivector-solutions/charm-prometheus-node-exporter/issues).

## License

The charm is maintained under the MIT license. See `LICENSE` file in this
directory for full preamble.

Copyright &copy; Omnivector Solutions 2021
