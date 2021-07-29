#!/bin/python3

import socket
import winsound
from wakeup import interpret


def calc(bytearray):
    check = 0
    for i in bytearray:
        check = AddToCRC(i, check)
    return check


def AddToCRC(b, crc):
    # This function came from https://gist.github.com/eaydin/768a200c5d68b9bc66e7
    if (b < 0):
        b += 256
    for i in range(8):
        odd = ((b ^ crc) & 1) == 1
        crc >>= 1
        b >>= 1
        if (odd):
            crc ^= 0x8C
    return crc


def init(host='', port=5005):
    sock.bind((host, port))
    # optional: set host to this computer's IP address


def receive(buffersize=1024):
    data, addr = sock.recvfrom(buffersize)
    return(data, addr)


def end():
    sock.close()


def main():
    recvport = 5606
    try:
        init(port=recvport)
        okay = True
    except:
        print(f'Port {recvport} is already open by another application. \
Aborting.')
        okay = False
    while okay:
        data, addr = receive()
        winsound.Beep(1500, 60)
        batt_data = data[4:40]
        batt_data_first35 = batt_data[0:35]
        received_crc = batt_data[35]
        calculated_crc = calc(batt_data_first35)
        if received_crc == calculated_crc:
            print(f"From {addr} Recv Port: \
{recvport} Bytes: {len(data)}")
            (voltage, current, power, highcell, lowcell, difference, percent, temperatures) = interpret(batt_data)
        else:
            print(f"CRC doesn't match. expected: {hex(calculated_crc)} got {hex(received_crc)}")

    end()


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if __name__ == "__main__":
    main()
