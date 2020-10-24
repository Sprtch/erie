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
> venv/bin/python erie --no-daemon
```

## Config

## Useful Links

* [LS3578Product Reference Guide](https://topresale.ru/download/Zebra_Motorola_LS3578_%D0%A1%D0%BF%D1%80%D0%B0%D0%B2%D0%BE%D1%87%D0%BD%D0%BE%D0%B5_%D1%80%D1%83%D0%BA%D0%BE%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%BE.pdf)
* [Product reference guide](https://www.zebra.com/content/dam/zebra_new_ia/en-us/manuals/barcode-scanners/ds3578-prg-en.pdf)
