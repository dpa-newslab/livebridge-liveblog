# livebridge-liveblog

[![Build Status](https://travis-ci.org/dpa-newslab/livebridge-liveblog.svg?branch=master)](https://travis-ci.org/dpa-newslab/livebridge-liveblog)
[![Coverage Status](https://coveralls.io/repos/github/dpa-newslab/livebridge-liveblog/badge.svg?branch=master)](https://coveralls.io/github/dpa-newslab/livebridge-liveblog?branch=master)
[![PyPi](https://badge.fury.io/py/livebridge-liveblog.svg)](https://pypi.python.org/pypi/livebridge-liveblog)

A [Liveblog](https://www.sourcefabric.org/en/liveblog/) plugin for [Livebridge](https://github.com/dpa-newslab/livebridge).

It allows to use [Sourcefabric Liveblog](https://github.com/liveblog/liveblog) 3.0 and above as a **source** or a **target** (experimental) for [Livebridge](https://github.com/dpa-newslab/livebridge).

## Installation
**Python>=3.5** is needed.
```sh
pip3 install livebridge-liveblog
```
The plugin will be automatically detected and included from **livebridge** at start time, but it has to be available in **[PYTHONPATH](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)**

See http://livebridge.readthedocs.io/en/latest/plugins.html#installing-plugins for more infos.

## Plugin specific control file parameters

Under **bridges**:
* **source_id** - Blog-ID/Hash of the Liveblog
* **endpoint** - API endpoint of the Liveblog
* **verify_ssl** - SSL check for source, default **true**
* **source_check_interval** - Interval in seconds for blog status checks (open/closed), defaults to **600**

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

Under **targets**: - **(experimental feature)**
* **target_id** - Blog-ID/Hash of the Liveblog
* **endpoint** - API endpoint of the Liveblog
* **draft** - *optional* saves new posts at the target blog as **drafts**.
* **submit** - *optional* saves new posts at the target bplog as **contributions**.
* **verify_ssl** - SSL check for target, default **true**

*Warning: When a posting got edited in the target liveblog, the post cannot longer be edited/deleted via Livebridge.*


**Example:**
```
bridges:
    - channel: "channelname"
      type: "acme"
      label: "Example"
      targets:
        - source_id: "56fceedda505e600f7195cch"
          type: "liveblog"
          endpoint: "https://liveblog.pro/api/"
          draft: True
          label: "Example-Target"
```

See http://livebridge.readthedocs.io/en/latest/control.html for more infos.

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
