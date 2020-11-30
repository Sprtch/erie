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
    uri: <database uri>

erie:
    redis: <redis default channel>
    devices:
        - <device_name>:
            type: "serial"
            id:  <device_id in /dev/serial/by-id/>
            baudrate: <device baudrate>
            redis:  <device redis channel>
        - <device_name>:
            type: "evdev"
            id: <device_id in /dev/input/by-id/>
```

## Commands

The program can detect formatted input commands scanned from a barcode scanner.
The commands are prefixed with `SPRTCHCMD:` and have the following
structure

```
SPRTCHCMD:<cmd_name>:<arguments>
```

There are two types of commands scannable.

* The one that change the mode the barcode scanner the command is scanned from, is operating in.
* The one that modify the behaviour of the next scanned barcode.

### Mode

The mode a barcode scanner is operating in define how the scanned barcode will be
handled by the program.
The mode of a scanner is changeable by scanning the following command with the
scanner and is unique to each scanner device.

#### Print Mode: `SPRTCHCMD:MODE:PRINT`

In this mode the scanned barcodes will be directly sent
to the printer through redis.

The print mode is the default mode. 

#### Inventory Mode: `SPRTCHCMD:MODE:INVENTORY`

In this mode the scanned barcodes will get logged to the `inventory` table in
the database. 
If the entry already exists in the database it will update the entry to
increment the count.

### Function

The 'function' category group all the commands that are gonna get queued and
executed once the program receive a barcode.

#### Multiplier: `SPRTCHCMD:MULTIPLIER:<multiplier>`

Depending on the current mode the program is operating in, it will multiply 
the next action on a barcode (by default an action is applied 1 time) by the 
number passed in the argument of the command.

* In print mode, it will multiply the number of barcode that get printed.
* In inventory mode, it will multiply the number time we log the next barcode.

This command can get stacked before being executed once a barcode is received.
Scanning the command `SPRTCHCMD:MULTIPLIER:2` and then `SPRTCHCMD:MULTIPLIER:3`
will apply the next action `6` time.

#### Clear: `SPRTCHCMD:CLEAR:0`

Clear the queued functions.

## Useful Links

* [LS3578Product Reference Guide](https://topresale.ru/download/Zebra_Motorola_LS3578_%D0%A1%D0%BF%D1%80%D0%B0%D0%B2%D0%BE%D1%87%D0%BD%D0%BE%D0%B5_%D1%80%D1%83%D0%BA%D0%BE%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%BE.pdf)
* [Product reference guide](https://www.zebra.com/content/dam/zebra_new_ia/en-us/manuals/barcode-scanners/ds3578-prg-en.pdf)
