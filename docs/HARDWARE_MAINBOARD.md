# AT&T 26A Main Board

![26A MAINBOARD FRONT](./images/AT&T_26A_MAINBOARD_FRONT.jpg)

![26A MAINBOARD BACK](./images/AT&T_26A_MAINBOARD_BACK.jpg)


## Pinout (10-pin)

![26A MAIN BOARD CABLE PINS](./images/10_pins.png)

![26A MAIN BOARD CONNECTOR ORIENTATION](./images/AT&T_26A_MAINBOARD_CONNECTOR.jpg)

| Pin | Purpose | Voltage |
| --- | ------- | ------- |
|  1  | GND     | GND     |
|  2  | VCC     | 5 VDC   |
|  3  | VCC     | 5 VDC   |
|  4  | GND     | GND     |
|  5  | TX      | 5 VDC   |
|  6  | GND     | GND     |
|  7  | RX      | 5 VDC   |
|  8  | GND     | GND     |
|  9  | Reset   | 5 VDC   |
|  10 | GND     | GND     |

## Components

![26A MAIN BOARD BACK ANNOTATED](./images/AT&T_26A_MAINBOARD_BACK_ANNOTATED.jpg)

1) Microcontroller
	* ![microcontroller](./images/SC87C51CCA44.jpg)
	* Model: SC87C51CCA44
	* Type: Intel 8051
	* Footprint: CPLC44
2) Connector Port IO Buffer (Octal buffer/line driver)
	* ![WP90531L6](./images/WP90531L6.jpg)
	* Model: WP90531L6 (74HC244 compatible)
	* Only 3 out of 8 drivers are used.
3) 8-bit Registers
	* ![WP90532L6](./images/WP90532L6.jpg)
	* Model: WP90532L6 (SN74S32 compatible)
4) Hex Inverter (Open Drain)
	* Model: MM74HCT05M
5) Crystal Resonator
6) Power & Data Connector
7) Column Driver Transistors
8) Row Driver Transistors

## Power Usage

With all leds at full power, the 26A draws about 0.30 A of
current. For my 5.11V usb port, that ended up being 1.53W.
