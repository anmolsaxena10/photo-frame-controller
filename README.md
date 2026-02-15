## PlatformIO Commands

All in one:
    pio run -t upload && pio device monitor

Build:

    pio run
    pio run -e esp32dev
    pio run -t clean

Upload:

    pio run -t upload
    pio run -e esp32dev -t upload

Monitor:

    pio device monitor
    pio device monitor -p /dev/ttyUSB0 -b 115200

Clean:

    pio run -t clean

Full clean:

    rm -rf .pio

Test:

    pio test
    pio test -e esp32dev

List devices:

    pio device list

Package managemenr:

    pio lib install "bblanchon/ArduinoJson@^6.21.3"
    pio lib update

Manage PIO:

    pio --version
    pio system info

## WSL Device setup

    usbipd list
    usbipd bind --busid 1-1
    usbipd attach --busid 1-1 --wsl
    wsl --shutdown
    ls /dev/ttyUSB*
