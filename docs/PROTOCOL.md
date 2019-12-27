This document will describe the serial protocol used by the AT&T 26A
Direct Extension Selector Console.

## 1. Communication

The 26A communicates over a serial interface:

| Parameter  | Value  |
|------------|--------|
| Baud       | 10752  |
| Byte Size  | 8 bits |
| Parity     | Odd    |
| Stop Bits  | One    |
| Start Bits | One    |

### 1.1 Reset

The 26A does not include a Power On Reset circuit. Before the 26A is used, a reset cycle should be applied.

The reset pin's behavior is as follows:

| Value     | Meaning |
| --------- | ------- |
| Low (0V)  | Run     |
| High (5V) | Reset   |

To reset the 26A:
1) Raise the Reset pin to High (5V).
2) wait 100 mS (This time is a guess and likely overkill).
3) Lower the Reset pin to Low (0V).

## 2. Datatypes

This section lists off data types used in more than one place. If a datatype is used in only one place, then it will be listed in the message it is used in.

### 2.1 Left Shifted 7-bit integer

A 7-bit integer stored in the lower part of an 8-bit byte (highest order bit is cleared).

    0b0ABCDEFG

The encoded form of this data is sent down the wire, so the sender has to encode the raw data, and the receiver has to decode the encoded data.

The encoding and decoding process is a circular one bit shift on a 7 bit integer, so **a 8 bit integer shift won't work. A custom 7 bit circular left/right shift is required.**

**Encoding Pseudo code (1 bit left shift for 7 bit integer):**

    # BTN_MESSAGE << BTN_ID
    # 0b0ABCDEFG  => 0b0BCDEFGA
    ((b << 1) & 0x7E) | ((b & 0x40) >> 6)

**Decoding Pseudo Code (1 bit right shift for 7 bit integer):**

    # BTN_MESSAGE >> BTN_ID
    # 0b0ABCDEFG  => 0b0GABCDEF
    ((b & 0x7E) >> 1) | ((b & 0x01) << 6)

**Note:** Bit 7 should always be cleared for both the encoded and decoded form.

## 3. Transmissions From the 26A.

The 26A sends several types of messages:

| Name                      | Value | Length | Description                               |
|---------------------------|-------|--------|-------------------------------------------|
| Keep Alive (KA)           | 0xFF  | 1      | Sent every ~26 ms.                        |
| Message Acknowledge (ACK) | 0xFD  | 1      | The 26A received and processed a message. |
| Button Press              | 0xXX  | 1      | A button on the 26A has been pressed.     |
| Command Specific Response |**N/A**|**N/A** | Only one command gets data sent back.     |

### 3.1 Button presses.

Button press messages are Left shifted 7-bit Integers (Datatypes 2.1). Each button press message is one byte long, and can be identified by the highest bit being cleared.

    0b0ABCDEFG

The received button message has to be transformed in order to get the button ID. Read Datatypes 2.1 for information on how to decode the encoded button id.

## 4. Sending commands to the 26A.

All commands sent to the 26A must be sent in a message frame. This frame is only used for sending data to the 26A, and not used when the 26A transmits date.

Message Frame Format:

    MSG:HASH:0xFF

* MSG must start with either 0x85 or 0xA5. **These values always clear and reset the current message frame.**
* MSG can be up to 15 bytes (any longer, and the message buffer wraps around, overwriting the message).
* HASH is the xor of 0x7F all bytes in MSG (**except the first byte**).
* The byte 0xFF is used to mark the end of a message frame, and can not be used for anything else.

If the hash passes, the 26A will reply with the ACK byte (0xFD).

MSG can be one of the following byte sequences.

### 4.1 Command Messages for the 26A.

The following commands can be sent to the 26A by replacing `MSG` in the Message Frame Format with the hex data in the command's Format.

The 26A will respond to all valid Message Frames with an optional message return type, and an `ACK` (0xFG) byte. The 26A will respond to valid Message Frames even if the command message in the Message Frame is not recognized.

**Return Message Format:** `[MESSAGE_RETURN_DATA]:FD`

`MESSAGE_RETURN_DATA` may be 0 bytes long (and usually is).

All bytes in `MESSAGE_RETURN_DATA` must have bit 7 set, and not be 0xFD (ACK). This makes sure that bytes in `MESSAGE_RETURN_DATA` can not be mistaken for button presses or a premature termination of the return data.

The `ACK` byte will not be listed in a command message's return type. Expect it after your command message's return data.

#### 4.1.1 Return state of LED (Only bottom 2 rows, LED 100-119).

Read the state of LED `ID`. Only works for LED 100 <= `ID` <= 119 (bottom two rows of LEDs).

Using this command is harder than just storing the values of leds in a local buffer. There is very little reason to use it (or even support it), particularly because it only works for the bottom 20 leds and not the main 100.

**Format:** `A520:XX`

* __ID (XX)__ - The ID of the LED to query the state of.
	* **Type:** 7-bit Left Shifted Integer (**Datatype 2.1**).
	* **Range:** 100 <= XX <= 119.

**Returns:** Encoded Button `STATE` and Button `RetID`.
* __Format:__ `0b10SSCNNN [0b100MMMMM] `
* __Length:__ 1 byte if C == 0, 2 bytes if C == 1.
* __SS:__ Button `STATE` (two bit enumeration):
	* **0b00**: OFF
	* **0b01**: BLINK STEADY
	* **0b10**: BLINK QUICK
	* **0b11**: ON
* __C:__ Length marker. Read the __Length__ section for more details.
* __NNN:__ 3 bit `RetID` If C == 0, `0b111` if C == 1.
* __MMMMM:__ 5 bit `RetID` if C == 1.
* __Notes:__
	* __RetID:__ `ID` = `RetID` + 100.

#### 4.1.2 Set LED range ON/OFF (LEDs 0-99 only).

Set the state of `COUNT` LEDs, starting at LED number `ID`.

Only the ON and OFF state may be assigned to LEDs using this command. Each LED is independently assigned using the `DATA` bit-field.

If 0 <= `ID` <= 99, and `ID` + `COUNT` > 100, then the LED values written to LED 100 and above will wrap back around and start counting up again from LED 0.

**Format:** `8507:XXYY:DATA`

* __ID (XX)__ - The ID of the LED to query the state of.
	* **Type:** 7-bit Left Shifted Integer (**Datatype 2.1**).
	* **Range:** 0 <= XX <= 99.
* __COUNT (YY)__ - The number of LEDs to set (and the number of state bits in `STATES`.
	* **Type:** 7-bit Integer (non shifted).
	* **Range:** 1 <= YY <= 70; 72 <= YY <= 76. The value 71 is not supported (seems to be obfuscation).
    * **Encoding:** if YY != 70, subtract 1 from YY (YY if YY == 70 else YY - 1).
* __STATES (DATA)__ - Bit-field containing the LED ON/OFF states to be set.
	* **Type:** Bit-field array. Each byte contains 7 bits of the bit-fields (in the byte's low bits).
	* **Length:** ceil(`COUNT` / 7.0) bytes. Max 11 bytes.
	* **Bit Values:** 0=OFF; 1=ON
	* **Bit Mapping:** For the bytes `0b0ABCDEFG 0b0HIJKLMN`
		* Bit A maps to LED `ID`.
		* Bit B maps to LED `ID` + 1
		* ......
		* Bit G maps to LED `ID` + 6
		* Bit H maps to LED `ID` + 7
		* ......

#### 4.1.3 Set LED state.

Set the state of a single LED.

**Format:** `852X:YY`

* __STATE (X)__ - New state for LED.
	* **Type:** Enumeration (Half-byte, Nibble).
	* 4 possible LED values:
		* **0x0**: OFF
		* **0x8**: BLINK STEADY
		* **0xD**: BLINK QUICK
		* **0xF**: ON
* __LEDID (YY)__ - The ID of the LED to set the state of.
	* **Type:** 7-bit Left Shifted Integer (**Datatype 2.1**).
	* **Range:** 0 <= XX <= 119.

#### 4.1.4 Enable factory test

Enable Factory Test Mode if it is currently disabled, otherwise, no effect.

Factory Test Mode causes the 26A to Ignore the current stored state of the LEDs and flashes a test pattern. The test pattern cycles through all rows of LEDs from top to bottom, illuminating all LEDs on the current row. This mode is useful to check that all LEDs are working.

Factory Test Mode is **disabled** by default.

The test pattern will only show if the IO driver is enabled.

LED states can be changed on the 26A while in factory test mode. These changes will not be displayed until Factory Test Mode is disabled.

**Format:** `8510:6F`

#### 4.1.5 Disable factory test

Disable factory test if factory test is enabled, otherwise, no effect.

When Factory Test Mode is turned off, the 26A will resume showing the LED states set by the user.

**Format:** `8530:4F`

#### 4.1.6 Enable IO driver

Enables the LED and button driver if it is currently disabled, otherwise, no effect.

The IO driver is **enabled** by default.

Enabling the IO driver after previously disabling it will show any changes made to the LED states while the IO driver was disabled, but button presses during that time are lost forever.

**Format:** `8540:3F`

#### 4.1.7 Disable IO driver

Disable the LED and button driver if it is currently enabled, otherwise, no effect.

While the IO driver is disabled, all LEDs will be off, and no button presses will be reported. The state of the IO driver does not effect the ability to set or read LED states, but changes will not appear on the 26A's display until the IO driver is enabled.

**Format:** `8550:2F`
