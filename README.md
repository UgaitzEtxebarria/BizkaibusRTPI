# BizkaibusRTPI

Async client to query real-time information of Bizkaibus buses.

## Installation

```bash
pip install bizkaibus
```

## Basic usage

```python
import asyncio

from bizkaibus import BizkaibusAPI
from bizkaibus.Model.BizkaibusLanguages import BizkaibusLanguages


async def main():
    api = await BizkaibusAPI.create(BizkaibusLanguages.EU, "0296")
    timetable = await api.get_timetable()
    print(timetable)

asyncio.run(main())
```

## Get lines for a stop

```python
async def main():
    api = await BizkaibusAPI.create(BizkaibusLanguages.ES, "0296")
    lines = await api.get_lines_on_stop()
    for line in lines:
        print(line)
```

## Error handling

The client raises the following exceptions, all available from `bizkaibus`:

- `BizkaibusConnectionError` when a request times out, cannot connect, receives a non-200 HTTP status, or the service reports a failure.
- `BizkaibusStopNotFoundError` when the requested stop does not exist.
- `BizkaibusParseError` when the service returns malformed or unexpected data.

```python
from bizkaibus import (
    BizkaibusConnectionError,
    BizkaibusParseError,
    BizkaibusStopNotFoundError,
)

try:
    api = await BizkaibusAPI.create(BizkaibusLanguages.EU, "0296")
except BizkaibusStopNotFoundError:
    print("The requested stop does not exist")
except BizkaibusConnectionError:
    print("Could not contact the Bizkaibus service")
except BizkaibusParseError:
    print("The Bizkaibus service returned an invalid response")
```

## Features

- Stop timetable lookup
- Stop line lookup
- Incident retrieval by language
- Async support with `asyncio` and `aiohttp`

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## License

MIT
