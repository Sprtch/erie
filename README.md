# Erie

Erie is python daemon handling the incoming messages from multiple barcode
scanners and send them to the [printer](https://github.com/Sprtch/victoria).

## Usage

This package is made to be ran as a daemon on the raspberry pi.
The [firmware](https://github.com/Sprtch/buildroot) with buildroot handle the
build process and the configuration.

During development process launch the script can with the following
command to log in the console.

```txt
> source venv/bin/activate
> venv/bin/python erie -h
usage: [-h] [--no-daemon] [--logfile LOGFILE] [--debug] [--pid PID] [-c CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  --no-daemon           Does not start the program as a daemon
  --logfile LOGFILE     Log destination
  --debug               Set the log level to show debug messages
  --pid PID             Pid destination
  -c CONFIG, --config CONFIG
                        Config file location
> venv/bin/python erie --no-daemon
```

In development mode its recommended to launch _erie_ with the `--debug` option.
The _debug_ mode automatically handle the incoming data from the command line
to avoid to have to use a barcode scanner to input data.

## Config

The program is configurable by passing a `.yaml` file as argument (with ` c` argument) formatted in the following way:

```
despinassy:
    uri: str

erie:
    redis: str
    devices:
        - (str):
            type: "serial"
            id: str
            baudrate: int
        - (str):
            type: "evdev"
            id: str
```

## Useful Links

* [LS3578Product Reference Guide](https://topresale.ru/download/Zebra_Motorola_LS3578_%D0%A1%D0%BF%D1%80%D0%B0%D0%B2%D0%BE%D1%87%D0%BD%D0%BE%D0%B5_%D1%80%D1%83%D0%BA%D0%BE%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%BE.pdf)
* [Product reference guide](https://www.zebra.com/content/dam/zebra_new_ia/en-us/manuals/barcode-scanners/ds3578-prg-en.pdf)
