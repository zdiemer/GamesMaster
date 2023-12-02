# Games Master

A collection of data collection scripts in python.

## Setup

```sh
$ pip install -r src/requirements.txt
```

Create the config.json file.

```sh
$ touch static/config.json
```

```json
{
    "mobyGamesApiKey": "...",
    "giantBombApiKey": "...",
    "igdbClientId": "...",
    "igdbClientSecret": "...",
    "steamWebApiKey": "...",
    "priceChartingApiKey": "..."
}
```

## Running Parsers

1. Configure the `if __name__ == "__main__":` block of `excel_parser.py` according to desired settings.
2. Run `python ./src/excel_parser.py` from the root of the project.

## Running App

The application stack is run via docker compose, it can be brought up from scratch via some initialization scripts:

```sh
$ sh init.sh
```

and then everything can be brought down with:

```sh
$ sh reset.sh
```

## (setup) Django commands ran

Initialization:

```sh
$ django-admin startproject game_manager
```