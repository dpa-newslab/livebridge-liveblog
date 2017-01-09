# livebridge-liveblog

[![Build Status](https://travis-ci.org/dpa-newslab/livebridge-liveblog.svg?branch=master)](https://travis-ci.org/dpa-newslab/livebridge-liveblog)
[![Coverage Status](https://coveralls.io/repos/github/dpa-newslab/livebridge-liveblog/badge.svg?branch=master)](https://coveralls.io/github/dpa-newslab/livebridge-liveblog?branch=master)

A [Liveblog](https://www.sourcefabric.org/en/liveblog/) plugin for [Livebridge](https://github.com/dpa-newslab/livebridge).

It allows to use [Sourcefabric Liveblog](https://github.com/liveblog/liveblog) 3.0 and above as a source for [Livebridge](https://github.com/dpa-newslab/livebridge).

## Installation
**Python>=3.5** is needed.
```sh
pip3 install livebridge-liveblog
```
The plugin will be automatically detected and included from **livebridge** at start time, but it has to be available in **[PYTHONPATH](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)**

See https://pythonhosted.org/livebridge/plugins.html#installing-plugins for more infos.

## Plugin specific control file parameters

Under **bridges:**:
* **source_id** - Blog-ID/Hash of the Liveblog
* **endpoint** - API endpoint of the Liveblog

**Example:**
```
bridges:
    - source_id: "56fceedda505e600f7195cch"
      endpoint: "https://liveblog.pro/api/"
      type: "liveblog"
      label: "Example"
      targets:
        - type: "acme"
          channel: "channelname"
```

See https://pythonhosted.org/livebridge/control.html for more infos.

## Testing
**Livebridge** uses [py.test](http://pytest.org/) and [asynctest](http://asynctest.readthedocs.io/) for testing.

Run tests:

```sh
    py.test -v tests/
```

Run tests with test coverage:

```sh
    py.test -v --cov=livebridge_liveblog --cov-report=html tests/
```

[pytest-cov](https://pypi.python.org/pypi/pytest-cov) has to be installed. In the example above, a html summary of the test coverage is saved in **./htmlcov/**.

## License
Copyright 2016 dpa-infocom GmbH

Apache License, Version 2.0 - see LICENSE for details
