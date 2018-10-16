RECV:
If bit 7 is 0: Button event. ID = (7 bit num)num >> 1
FF = Keep Alive (every ~26 ms).
FD = ACK (The message has been hashed and run. Doesn't mean
          the message is valid, just that the hash worked.)

SEND:
Message format: MSG:HASH:0xFF
MSG must start with either 0x85 or 0xA5.
MSG can be up to 15 bytes.
HASH is the xor of all bytes in MSG with 0x7F (except the first byte).
If hash passes, device will reply with 0xFD.

MSG TYPES:
A520:XX; Return status of led. Only bottom 2 rows.
    XX: 100 <= XX < 120
        7 bit left shift real val to get XX.
8507:XXYY:DATA;
    XX: Smaller than 100. 7bit left shift 1 real value.
    YY: A Length. 70->70; 
        7 bit left shift real val to get YY.
    DATA: Unknown buffer of data.
852X:YY; Set LED state.
    X:  0, 8, D, or F
    YY: Unencoded val has to be less than 120.
        7 bit left shift real val to get YY.
8510:6F; Related to 8530:4F. Enables test
8530:4F; Related to 8510:6F. Disables test
8540:3F; Enables IO (ban read/led drive).
8550:2F; Disables IO (ban read/led drive).




In [10]: att26a.msg_A520_XX(ser, 100)
PRE
a5:20:49:16:ff
RES

In [11]: att26a.msg_A520_XX(ser, 100)
PRE 80:fd
a5:20:49:16:ff
RES 80:fd

In [12]: att26a.set_led_state(ser, 0xf, 100)
PRE
85:2f:49:19:ff
RES

In [13]: att26a.set_led_state(ser, 0xf, 100)
PRE fd
85:2f:49:19:ff
RES

In [14]: att26a.msg_A520_XX(ser, 100)
PRE fd
a5:20:49:16:ff
RES b0:fd

In [15]: att26a.set_led_state(ser, 0xD, 100)
PRE
85:2d:49:1b:ff
RES

In [16]: att26a.msg_A520_XX(ser, 100)
PRE fd
a5:20:49:16:ff
RES a0:fd

In [17]: att26a.msg_A520_XX(ser, 101)
PRE
a5:20:4b:14:ff
RES 81:fd

In [18]: att26a.msg_A520_XX(ser, 102)
PRE
a5:20:4d:12:ff
RES 82:fd

In [19]: att26a.msg_A520_XX(ser, 103)
PRE
a5:20:4f:10:ff
RES 83:fd

In [20]: att26a.msg_A520_XX(ser, 104)
PRE
a5:20:51:e:ff
RES 84:fd

In [21]: att26a.msg_A520_XX(ser, 105)
PRE
a5:20:53:c:ff
RES 85:fd

In [22]: att26a.msg_A520_XX(ser, 106)
PRE
a5:20:55:a:ff
RES 86:fd

In [23]: att26a.msg_A520_XX(ser, 107)
PRE
a5:20:57:8:ff
RES 87:fd

In [24]: att26a.msg_A520_XX(ser, 108)
PRE
a5:20:59:6:ff
RES 8f:88:fd

In [25]: att26a.msg_A520_XX(ser, 109)
PRE
a5:20:5b:4:ff
RES 8f:89:fd

In [26]: att26a.msg_A520_XX(ser, 110)
PRE
a5:20:5d:2:ff
RES 8f:8a:fd

In [27]: att26a.msg_A520_XX(ser, 111)
PRE
a5:20:5f:0:ff
RES 8f:8b:fd

In [28]: att26a.msg_A520_XX(ser, 112)
PRE/Users/jessyexum/src/ATandT_26A_RE/att26a.py
a5:20:61:3e:ff
RES 8f:8c:fd

In [29]: att26a.msg_A520_XX(ser, 113)
PRE
a5:20:63:3c:ff
RES 8f:8d:fd

In [30]: att26a.msg_A520_XX(ser, 114)
PRE
a5:20:65:3a:ff
RES 8f:8e:fd

In [31]: att26a.msg_A520_XX(ser, 115)
PRE
a5:20:67:38:ff
RES 8f:8f:fd

In [32]: att26a.msg_A520_XX(ser, 116)
PRE
a5:20:69:36:ff
RES 8f:90:fd

In [33]: att26a.msg_A520_XX(ser, 117)
PRE
a5:20:6b:34:ff
RES 8f:91:fd

In [34]: att26a.msg_A520_XX(ser, 118)
PRE
a5:20:6d:32:ff
RES 8f:92:fd

In [35]: att26a.msg_A520_XX(ser, 119)
PRE
a5:20:6f:30:ff
RES 8f:93:fd
