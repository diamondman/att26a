import serial
import time

def shift7_left(b):
    return ((b << 1) & 0x7E) | ((b & 0x40) >> 6)

def shift7_right(b):
    return ((b & 0x7E) >> 1) | ((b & 0x01) << 6)

#for i in range(0,127):
#    if i != att26a.shift7_left(att26a.shift7_right(i)):
#        print("FAIL at %d" % i)

def open_att26a(devname):
    return serial.Serial(devname, baudrate=10752,
                         bytesize=serial.EIGHTBITS, parity=serial.PARITY_ODD,
                         stopbits=serial.STOPBITS_ONE)

def reset_att26a(ser):
    pass

def prepare_msg_frame(msg):
    if len(msg) > 15:
        raise ValueError("msg may not be longer than 15 bytes.")
    h = 0x7F
    for b in msg[1:]:
        h ^= b
    return msg + bytes([h]) + b'\xff'

def read_btn_loop(ser):
    while True:
        buf = ser.read_all().replace(b'\xff', b'')
        if len(buf):
            for b in buf:
                bfixed = shift7_right(b)
                print("%s (%d) => %s (%d)" % (hex(b)[2:].zfill(2), b, hex(bfixed)[2:].zfill(2), bfixed))
        time.sleep(0.2)

def print_all_data(ser):
    buf = b''
    got_any_data = False
    while True:
        tmp = ser.read_all()
        buf += tmp.replace(b'\xff', b'')
        if len(tmp):
            got_any_data = True
        if len(tmp) < 500:
            break
    print("PRE", ":".join((hex(b)[2:] for b in buf)), "" if got_any_data else "NODATA")


def tx(ser, msg, *, sync=True):
    if len(msg) == 0:
        raise ValueError("Message must be at least one byte long.")
    if len(msg) >= 16:
        raise ValueError("Message must be shorter than 16 bytes.")
    if b'\xFF' in msg:
        raise ValueError("Message may not contain a byte of value 0xFF.")

    print_all_data(ser)
    outmsg = prepare_msg_frame(msg)
    print(":".join((hex(b)[2:] for b in outmsg)))
    ser.write(outmsg)
    if sync:
        time.sleep(0.6)
    res = ser.read_all().replace(b'\xff', b'')
    print("RES", ":".join((hex(b)[2:] for b in res)))


# Returns 1 or 2 bytes.
def get_high_led_status(ser, XX):
    # A520:XX
    if 100 > XX or XX >= 120:
        raise ValueError("XX must be 100 <= XX < 120; not %d" % XX)

    tx(ser, b'\xA5\x20' + bytes([shift7_left(XX)]))

# Unknown. No Return.
def msg_8507_XXYY_DATA(ser, XX, YY, DATA):
    # 8507:XXYY:DATA
    # XX is start ledID
    # YY some length
    if XX > 100:
        raise ValueError("XX must be less than 100; not %d" % XX)
    #if YY == 71:
    #    raise ValueError("YY can not be 71.")
    #if len(DATA) > 11:
    #    raise ValueError("DATA may not be longer than 11 bytes.")

    #YY = shift7_left(YY)
    if YY != 70:
        YY -= 1
        if YY == -1: #8 bit rollover
            YY = 0xFF

    tx(ser, b'\x85\x07' + bytes([shift7_left(XX),
                                 YY]) + DATA)

#Sets light state. No Return.
def set_led_state(ser, state, ledID):
    # 852X:YY
    # X sets the state for the led number YY
    if state not in (0x0, 0x8, 0xD, 0xF): #translates to 0-3
        raise ValueError("state can either be 0x0, 0x8, 0xD, or 0xF")
    if ledID >= 120:
        raise ValueError("ledID must be smaller than 120; not %d." % ledID)

    tx(ser, b'\x85' + bytes([0x20 | state, shift7_left(ledID)]), sync=False)

def factory_test_mode_enable(ser, enable):
    if enable:
        tx(ser, b'\x85\x30\x4F')
    else:
        tx(ser, b'\x85\x10\x6F')

def set_IO_enable(ser, enable):
    if enable:
        tx(ser, b'\x85\x40\x3F')
    else:
        tx(ser, b'\x85\x50\x2F')
