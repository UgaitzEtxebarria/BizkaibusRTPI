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

```python
try:
    api = await BizkaibusAPI.create(BizkaibusLanguages.EU, "0296")
except ValueError:
    print("The API could not be initialized")
except ConnectionError:
    print("Connection error while contacting the Bizkaibus service")
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
