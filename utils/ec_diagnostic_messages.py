#!/usr/bin/env python3
'''
ec_diagnostic_messages.py

read diagnostic messages from EtherCAT slaves.
usage:
    ./ec_diagnostic_messages.py [-m MASTERID] [-s SLAVEID]

example:
    ./ec_diagnostic_messages.py -s2

reads all diagnostic messages from EtherCAT slave 2 on master 0

run in test mode
    ./ec_diagnostic_messages.py -t

---
Author: Felix Maier (felix.maier@psi.ch)
Date: March 27, 2025
'''

# pylint: disable-msg=C0103
# vim: ts=4 sw=4 et
import argparse
import re
import subprocess
import sys
import time
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta


# -------------------------------------------------------------------------------------------------
# ReadDiagMessages
# -------------------------------------------------------------------------------------------------
class ReadDiagMessage:

    # configure diagnostic sdos
    SDO_MAX_MSG = {"index": "0x10f3", "subindex": "0x01", "type": "uint8"}
    SDO_START_MSG = {"index": "0x10f3", "subindex": "0x06", "type": "octet_string"}
    SDO_DEVICE_NAME = {"index": "0x1008", "subindex": "0x00", "type": "string"}
    SDO_VENDOR_ID = {"index": "0x1018", "subindex": "0x01", "type": "uint32"}
    SDO_PRODUCT_CODE = {"index": "0x1018", "subindex": "0x02", "type": "uint32"}

    def __init__(self):
        self.id_master = 0
        self.id_slave = 1
        self.messages = list()
        self.device_name = ""
        self.device_vendor_id = 0
        self.device_product_code = 0

    def run(self, master_id, slave_id):
        ''' coordinate '''
        self.id_master = master_id
        self.id_slave = slave_id
        self.read_device_information()
        self.print_device_information()
        self.read_diag_messages()

        # sorted by descending time
        self.messages = sorted(self.messages, key=lambda x: x['time'], reverse=True)

        self.print_diagnostic_messages()

    @staticmethod
    def get_number_from_respond(respond, datatype):
        '''
        convert returned string from ethercat command to integer
        '''

        respond = respond.decode()

        regex = ""
        base_system = 0
        if datatype == "int":
            regex = re.compile(r'(\d+)$')
            base_system = 10
        if datatype == "hex":
            regex = re.compile(r'^(0x[a-zA-Z0-9]+)')
            base_system = 16

        match = regex.search(respond)
        if match is None:
            sys.exit("error: cannot find " + datatype + " part in respond")

        return int(match.group(), base=base_system)

    def read_device_information(self):
        self.device_name = self.read_sdo(self.SDO_DEVICE_NAME)
        self.device_vendor_id = self.read_sdo(self.SDO_VENDOR_ID)
        self.device_vendor_id = self.get_number_from_respond(self.device_vendor_id, "hex")
        self.device_product_code = self.read_sdo(self.SDO_PRODUCT_CODE)
        self.device_product_code = self.get_number_from_respond(self.device_product_code, "hex")

    def read_diag_messages(self):
        ''' read all diagnosis messages from slave '''

        max_msg_no = self.get_number_from_respond(self.read_sdo(self.SDO_MAX_MSG), "int")
        start_index = int(self.SDO_START_MSG['subindex'], base=16) # hex to int

        for idx in range(start_index, start_index + max_msg_no):
            sdo = self.SDO_START_MSG
            sdo["subindex"] = hex(idx)
            readMsg = self.read_sdo(sdo)

            if any(byte != 0 for byte in readMsg):
                msg = self.parse_msg(readMsg)

                dynamic = None
                if any(byte != 0 for byte in msg["dynamic"]):
                    dynamic = msg["dynamic"]

                msg["text"] = MsgCatalog.get(
                    self.device_vendor_id,
                    self.device_product_code,
                    msg["text_id"],
                    dynamic)

                self.messages.append(msg)

    def read_sdo(self, sdo):
        ''' read sdo from slave '''
        command = "/opt/etherlab/bin/ethercat -m" + str(self.id_master)
        command += " -p" + str(self.id_slave)
        command += " --type " + sdo["type"]
        command += " upload " + sdo["index"] + " " + sdo["subindex"]

        try:
            return subprocess.check_output(command, shell=True)
        except:
            sys.exit("error while calling: " + command)

    def parse_msg(self, raw_msg):
        return {
            #"diag_code": hex(int.from_bytes(raw_msg[0:4], byteorder='little')),
            "flags":     hex(int.from_bytes(raw_msg[4:6], byteorder='little')),
            "text_id":   format(int.from_bytes(raw_msg[6:8], byteorder='little'), '#06x'),
            "time":      self.decode_ethercat_time(int.from_bytes(raw_msg[8:16], byteorder='little')),
            "dynamic":   raw_msg[16:]
        }

    @staticmethod
    def decode_ethercat_time(ns):
        ''' convert ethercat nanoseconds to absolute time '''
        # dt is based on UNIX epoche 01.01.1970
        dt = datetime.fromtimestamp(ns / 1000000000)

        # days = 01.01.2000 - 01.01.1970 = 10957 days
        is_day_light_saving = time.localtime().tm_isdst
        if is_day_light_saving is True:
            dt = dt + timedelta(days=10957, hours=-1)
        else:
            dt = dt + timedelta(days=10957)

        return dt

    def print_device_information(self):
        ''' print some device information '''
        print("\nDEVICE INFORMATION:\n" + "="*19 + "\n")
        print("name:\t\t" + ((self.device_name).decode()).rstrip())
        print("master id:\t" + str(self.id_master))
        print("slave id:\t" + str(self.id_slave))
        print("vendor id:\t" + hex(self.device_vendor_id))
        print("product id:\t" + hex(self.device_product_code))
        print("host time:\t" + str(datetime.now()))

    def print_diagnostic_messages(self):
        ''' print table with the read diagnostic messages '''

        print("\n\nDIAGNOSTIC MESSAGES:\n" + "="*20)

        # calculate width of each column ------------
        col_width = OrderedDict({"time": 4, "text_id": 7, "text": 4,
                                 "flags": 5, "dynamic": 7})

        for msg in self.messages:
            for key, val in msg.items():
                value = val
                if isinstance(val, bytes):
                    value = val.hex()

                col_width[key] = max(len(str(key)), len(str(value)), col_width[key])

        col_width = {k: v+2 for k, v in col_width.items()}

        # print table -------------------------------
        print(self.generateTableLine(col_width, col_width, True))
        for msg in self.messages:
            print(self.generateTableLine(msg, col_width))
        print()

    @staticmethod
    def generateTableLine(data, col_width, is_header=False):
        ''' returns data formatted as table row / header '''

        row = ""
        for key, _ in col_width.items():
            text = key if is_header is True else data[key]
            width = col_width[key]

            if isinstance(text, bytes):
                text = "0x" + text.hex()
            else:
                text = str(text)

            row += text.ljust(width)

        return row


# -------------------------------------------------------------------------------------------------
# unit tests
#--------------------------------------------------------------------------------------------------

TEST_DATA = [
    # 0
    bytes([0x00, 0xE0, 0x81, 0x1B, 0x00, 0x00, 0x00, 0x11, 0x0A, 0xFD, 0x4B, 0x0D, 0x04, 0x47, 0x6F, 0x0B, 0x06, 0x00, 0x02, 0x01, 0x06, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00]),
    # 1
    bytes([ 0x00, 0xE0, 0x81, 0x1B, 0x00, 0x00, 0x35, 0x11, 0x2F, 0xB2, 0x61, 0x1B, 0x04, 0x47, 0x6F, 0x0B, 0x06, 0x00, 0xE7, 0x03, 0x06, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00]),
    # 2
    bytes([0x00, 0xE0, 0x81, 0x1B, 0x02, 0x00, 0x00, 0x81, 0x42, 0x3C, 0xA6, 0xAE, 0x66, 0x40, 0x6F, 0x0B, 0x06, 0x00, 0x04, 0x84, 0x06, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00]),
    # 3
    bytes([0x00, 0xE0, 0x81, 0x1B, 0x00, 0x00, 0x03, 0x00, 0xCA, 0xFF, 0xBD, 0x3A, 0xFD, 0x46, 0x6F, 0x0B, 0x06, 0x00, 0x00, 0x00, 0x06, 0x00, 0x02, 0x00, 0x06, 0x00, 0x00, 0x00])

]

TEST_EXPECT = [
        {
            "diag_code": "0x1b81e000", "text_id": "0x1100",
            "decoded_text": "Detection of operation mode completed: 0x%X, %d",
            "product_code": 0x1b813052,
            "vendor_id": 0x2,
        },
        {
            "diag_code": "0x1b81e000", "text_id": "0x1135",
            "decoded_text": "Cycle time o.k.: %d",
            "product_code": 0x1b813052,
            "vendor_id": 0x2,
        },
        {
            "diag_code": "0x1b81e000", "text_id": "0x8100",
            "decoded_text": "Status word set: 0x%X, %d",
            "product_code": 0x1b813052,
            "vendor_id": 0x2,

        },
        {
            "diag_code": "0x1b81e000", "text_id": "0x3",
            "decoded_text": "Initialization: 0x%X, 0x%X, 0x%X",
            "product_code": 0x1b813052,
            "vendor_id": 0x2,
        },
]

def test_decode_text_id():
    t = ReadDiagMessage()

    for cnt, test in enumerate(TEST_DATA):
        x = t.parse_msg(test)
        assert x['text_id'] == TEST_EXPECT[cnt]['text_id']

def test_decode_diag_code():
    t = ReadDiagMessage()

    for cnt, test in enumerate(TEST_DATA):
        x = t.parse_msg(test)
        assert x['diag_code'] == TEST_EXPECT[cnt]['diag_code']

def test_decode_text():
    t = ReadDiagMessage()

    for cnt, test in enumerate(TEST_DATA):
        product_id = TEST_EXPECT[cnt]['product_code']
        vendor_id = TEST_EXPECT[cnt]['vendor_id']

        x = t.parse_msg(test)
        y = MsgCatalog.get(vendor_id, product_id, x['text_id'])
        assert y == TEST_EXPECT[cnt]['decoded_text']

# -------------------------------------------------------------------------------------------------
# MsgCatalog
# -------------------------------------------------------------------------------------------------
class MsgCatalog:

    MSG_LUT = {
        # default applies to all devices, can be overwritten by key of device
        (0x0, 0x0): {
            0x0001: "No error",
            0x0002: "Communication established",
            0x0003: "Initialization: 0x%X, 0x%X, 0x%X",
            0x1000: "Information: 0x%X, 0x%X, 0x%X",
            0x4000: "Warning: 0x%X, 0x%X, 0x%X",
            0x8001: "Error: 0x%X, 0x%X, 0x%X",
            0x8201: "No communication to field-side (Auxiliary voltage missing)",
            0xFFFF: "Debug: 0x%X, 0x%X, 0x%X",
        },
    
        # ['EL5001', 'EL5001-0010', 'EL5001-0011', 'EL5001-0012', 'EL5001-0090']
        (0x2, 0x13893052): {
            0x1303: "Encoder Supply ok",
            0x8350: "Data Length Mismatch (Channel %d, Expect: %d, Received: %d)",
        },
    
        # ['EL5031-0011']
        (0x2, 0x13a73052): {
            0x1303: "Encoder Supply ok",
            0x1304: "Encoder initialization successfully, channel: %X",
            0x1305: "Sent command encoder reset, channel: %X",
            0x8303: "Encoder supply error",
            0x8304: "Encoder communication error, channel: %X",
            0x8305: "EnDat2.2 is not supported, channel: %X",
            0x8306: "Delay time, tolerance limit exceeded, 0x%X, channel: %X",
            0x8307: "Delay time, maximum value exceeded, 0x%X, channel: %X",
            0x8308: "Unsupported ordering designation, 0x%X, channel: %X (only 02 and 22 is supported)",
            0x8309: "Encoder CRC error, channel: %X",
            0x830A: "Temperature %X could not be read, channel: %X",
            0x830B: "Oversampling error, channel: %X",
        },
    
        # ['EL5032', 'EL5032-0090']
        (0x2, 0x13a83052): {
            0x1303: "Encoder Supply ok",
            0x1304: "Encoder initialization successfully, channel: %X",
            0x1305: "Sent command encoder reset, channel: %X",
            0x8303: "Encoder supply error",
            0x8304: "Encoder communication error, channel: %X",
            0x8305: "EnDat2.2 is not supported, channel: %X",
            0x8306: "Delay time, tolerance limit exceeded, 0x%X, channel: %X",
            0x8307: "Delay time, maximum value exceeded, 0x%X, channel: %X",
            0x8308: "Unsupported ordering designation, 0x%X, channel: %X (only 02 and 22 is supported)",
            0x8309: "Encoder CRC error, channel: %X",
            0x830A: "Temperature %X could not be read, channel: %X",
        },
    
        # ['EL5042']
        (0x2, 0x13b23052): {
            0x1303: "Encoder Supply ok",
            0x1304: "Encoder initialization successfully, channel: %X",
            0x8302: "general encoder error, channel: %X",
            0x8303: "Encoder supply error",
            0x8304: "Encoder communication error, channel: %X",
            0x830B: "Encoder Watchdog Error, channel: %X",
            0x830C: "Encoder Single-Cycle-Data Error, channel: %X",
        },
    
        # ['EL5072']
        (0x2, 0x13d03052): {
            0x117F: "Information: 0x%X",
            0x417F: "Warning: 0x%X",
            0x470E: "Overtemprature in device %d°C",
            0x8003: "Configuration error: 0x%X",
            0x8104: "Error: allowed temprature exeeded",
            0x810B: "Supply voltage Up too low or missing",
            0x817F: "Error: 0x%X",
            0x8581: "Wire broken Ch %d",
            0x8613: "Overload detected Ch %d, excitation voltage off",
            0x8623: "Short circuit detected Ch %d, excitation voltage off",
            0x8624: "Overload current Ch 1 + Ch 2 detected, excitation voltage off",
            0x8706: "Channel %d saturation",
            0x8707: "Channel %d overload",
            0x870A: "Channel %d range error",
            0x4101: "Overtemperature in device %d°C",
        },
    
        # ['EL5102']
        (0x2, 0x13ee3052): {
            0x4302: "Maximum frequency of the input signal is nearly reached (channel %d)",
            0x4303: "Limit counter value was reduced because of the PDO configuration (channel %d)",
            0x4304: "Reset counter value was reduced because of the PDO configuration (channel %d)",
            0x817F: "Internal hardware error (%d)",
            0x8303: "Encoder power missing (channel %d)",
            0x8310: "Initialisation error",
            0x8311: "Maximum frequency of the input signal is exceeded (channel %d)",
            0x8312: "Encoder plausibility error (channel %d)",
            0x8313: "Configuration error (channel %d)",
            0x8314: "Synchronisation error",
            0x8315: "Error status input (channel %d)",
            0x831B: "Open circuit or short circuit track A (channel %d)",
            0x831C: "Open circuit or short circuit track B (channel %d)",
            0x831D: "Open circuit or short circuit track C (channel %d)",
        },
    
        # ['EL5112']
        (0x2, 0x13f83052): {
            0x4302: "Maximum frequency of the input signal is nearly reached (channel %d)",
            0x4303: "Limit counter value was reduced because of the PDO configuration (channel %d)",
            0x4304: "Reset counter value was reduced because of the PDO configuration (channel %d)",
            0x817F: "Internal hardware error (%d)",
            0x8303: "Encoder power missing (channel %d)",
            0x8310: "Initialisation error",
            0x8311: "Maximum frequency of the input signal is exceeded (channel %d)",
            0x8312: "Encoder plausibility error (channel %d)",
            0x8313: "Configuration error (channel %d)",
            0x8314: "Synchronisation error",
            0x8315: "Error status input (channel %d)",
            0x831B: "Open circuit or short circuit track A (channel %d)",
            0x831C: "Open circuit or short circuit track B (channel %d)",
            0x831D: "Open circuit or short circuit track C (channel %d)",
        },
    
        # ['EL5122']
        (0x2, 0x14023052): {
            0x4302: "Maximum frequency of the input signal is nearly reached (channel %d)",
            0x4303: "Limit counter value was reduced because of the PDO configuration (channel %d)",
            0x4304: "Reset counter value was reduced because of the PDO configuration (channel %d)",
            0x817F: "Internal hardware error (%d)",
            0x8303: "Encoder power missing (channel %d)",
            0x8310: "Initialisation error",
            0x8311: "Maximum frequency of the input signal is exceeded (channel %d)",
            0x8312: "Encoder plausibility error (channel %d)",
            0x8313: "Configuration error (channel %d)",
            0x8314: "Synchronisation error",
            0x8315: "Error status input (channel %d)",
            0x831B: "Open circuit or short circuit track A (channel %d)",
            0x831C: "Open circuit or short circuit track B (channel %d)",
            0x831D: "Open circuit or short circuit track C (channel %d)",
        },
    
        # ['EL5131']
        (0x2, 0x140b3052): {
            0x4302: "Maximum frequency of the input signal is nearly reached (channel %d)",
            0x4303: "Limit counter value was reduced because of the PDO configuration (channel %d)",
            0x4304: "Reset counter value was reduced because of the PDO configuration (channel %d)",
            0x817F: "Internal hardware error (%d)",
            0x8303: "Encoder power missing (channel %d)",
            0x8310: "Initialisation error",
            0x8311: "Maximum frequency of the input signal is exceeded (channel %d)",
            0x8312: "Encoder plausibility error (channel %d)",
            0x8313: "Configuration error (channel %d)",
            0x8314: "Synchronisation error",
            0x8315: "Error status input (channel %d)",
            0x8318: "Error output (channel %d, output %d)",
            0x8319: "Error PDOs for threshold base not active (channel %d, output %d)",
            0x831B: "Open circuit or short circuit track A (channel %d)",
            0x831C: "Open circuit or short circuit track B (channel %d)",
            0x831D: "Open circuit or short circuit track C (channel %d)",
        },

        # ['EL7031', 'EL7031-0030']
        (0x2, 0x1b773052): {
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x1100: "Detection of operation mode completed: 0x%X, %d",
            0x1135: "Cycle time o.k.: %d",
            0x1300: "Position set: %d, %d",
            0x1400: "Drive is calibrated:  %d, %d",
            0x4300: "Subincrements deactivated:  %d, %d",
            0x4400: "Drive is not calibrated:  %d, %d",
            0x4401: "Starttype not supported: 0x%X, %d",
            0x4402: "Command rejected: %d, %d",
            0x4405: "Invalid modulo subtype: %d, %d",
            0x4410: "Target overrun: %d, %d",
            0x8100: "Status word set: 0x%X, %d",
            0x8101: "Operation mode incompatible to PDO interface: 0x%X, %d",
            0x8135: "Large cycle time: %d",
            0x8200: "Write access error: %d, %d",
            0x82FF: "Bootmode not activated",
            0x8300: "Set position error: 0x%X, %d",
            0x8301: "Encoder increments not configured: 0x%X, %d",
            0x8400: "Incorrect drive configuration: %d",
            0x8401: "Limiting of calibration velocity: %d, %d",
            0x8402: "Emergency stop activated: 0x%X, %d",
            0x8405: "Invalid modulo position: %d",
            0x8415: "Invalid modulo factor: %d",
            0x1401: "Actual drive state: 0x%X, %d",
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4301: "Encoder-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x4416: "Step lost detected at position: 0x%X%X",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8302: "Encoder-Error",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x4403: "Maximum position lag exceeded (%d): channel %d",
            0x8440: "Motor cable not connected",
        },

        # ['EL7037', 'EL7037-0052']
        (0x2, 0x1b7d3052): {
            0x1100: "Detection of operation mode completed: 0x%X, %d",
            0x1135: "Cycle time o.k.: %d",
            0x1201: "Communication re-established",
            0x1300: "Position set: %d, %d",
            0x1400: "Drive is calibrated: %d, %d",
            0x1401: "Actual drive state: 0x%X, %d",
            0x4101: "Terminal-Overtemperature",
            0x4300: "Subincrements deactivated: %d, %d",
            0x4301: "Encoder-Warning",
            0x4400: "Drive is not calibrated: %d, %d",
            0x4401: "Starttype not supported: 0x%X, %d",
            0x4402: "Command rejected: %d, %d",
            0x4405: "Invalid modulo subtype: %d, %d",
            0x4410: "Target overrun: %d, %d",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x4416: "Step lost detected at position: 0x%X%X",
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x8100: "Status word set: 0x%X, %d",
            0x8101: "Operation mode incompatible to PDO interface: 0x%X, %d",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8135: "Large cycle time: %d",
            0x8200: "Write access error: %d, %d",
            0x82FF: "Bootmode not activated",
            0x8300: "Set position error: 0x%X, %d",
            0x8301: "Encoder increments not configured: 0x%X, %d",
            0x8302: "Encoder-Error",
            0x8400: "Incorrect drive configuration: 0x%X, %d",
            0x8401: "Limiting of calibration velocity: %d, %d",
            0x8402: "Emergency stop activated: 0x%X, %d",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8405: "Invalid modulo position: %d",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x8415: "Invalid modulo factor: %d",
            0x8440: "Motor cable not connected",
            0x4403: "Maximum position lag exceeded (%d): channel %d",
            0x8103: "Undervoltage power rail",
        },

        # ['EL7041', 'EL7041-0001', 'EL7041-0052', 'EL7041-1000']
        (0x2, 0x1b813052): {
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x1100: "Detection of operation mode completed: 0x%X, %d",
            0x1135: "Cycle time o.k.: %d",
            0x1300: "Position set: %d, %d",
            0x1400: "Drive is calibrated:  %d, %d",
            0x4300: "Subincrements deactivated:  %d, %d",
            0x4400: "Drive is not calibrated:  %d, %d",
            0x4401: "Starttype not supported: 0x%X, %d",
            0x4402: "Command rejected: %d, %d",
            0x4405: "Invalid modulo subtype: %d, %d",
            0x4410: "Target overrun: %d, %d",
            0x8100: "Status word set: 0x%X, %d",
            0x8101: "Operation mode incompatible to PDO interface: 0x%X, %d",
            0x8135: "Large cycle time: %d",
            0x8200: "Write access error: %d, %d",
            0x82FF: "Bootmode not activated",
            0x8300: "Set position error: 0x%X, %d",
            0x8301: "Encoder increments not configured: 0x%X, %d",
            0x8400: "Incorrect drive configuration: %d",
            0x8401: "Limiting of calibration velocity: %d, %d",
            0x8402: "Emergency stop activated: 0x%X, %d",
            0x8405: "Invalid modulo position: %d",
            0x8415: "Invalid modulo factor: %d",
            0x1401: "Actual drive state: 0x%X, %d",
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4301: "Encoder-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x4416: "Step lost detected at position: 0x%X%X",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8302: "Encoder-Error",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x4403: "Maximum position lag exceeded (%d): channel %d",
            0x8440: "Motor cable not connected",
        },

        # ['EL7047', 'EL7047-0052', 'EL7047-9014']
        (0x2, 0x1b873052): {
            0x1100: "Detection of operation mode completed: 0x%X, %d",
            0x1135: "Cycle time o.k.: %d",
            0x1300: "Position set: %d, %d",
            0x1400: "Drive is calibrated: %d, %d",
            0x1401: "Actual drive state: 0x%X, %d",
            0x4300: "Subincrements deactivated: %d, %d",
            0x4400: "Drive is not calibrated: %d, %d",
            0x4401: "Starttype not supported: 0x%X, %d",
            0x4402: "Command rejected: %d, %d",
            0x4405: "Invalid modulo subtype: %d, %d",
            0x4410: "Target overrun: %d, %d",
            0x4416: "Step lost detected at position: 0x%X%X",
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x8100: "Status word set: 0x%X, %d",
            0x8101: "Operation mode incompatible to PDO interface: 0x%X, %d",
            0x8135: "Large cycle time: %d",
            0x8200: "Write access error: %d, %d",
            0x82FF: "Bootmode not activated",
            0x8300: "Set position error: 0x%X, %d",
            0x8301: "Encoder increments not configured: 0x%X, %d",
            0x8400: "Incorrect drive configuration: 0x%X, %d",
            0x8401: "Limiting of calibration velocity: %d, %d",
            0x8402: "Emergency stop activated: 0x%X, %d",
            0x8405: "Invalid modulo position: %d",
            0x8415: "Invalid modulo factor: %d",
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4301: "Encoder-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8302: "Encoder-Error",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x8440: "Motor cable not connected",
            0x4403: "Maximum position lag exceeded (%d): channel %d",
            0x441C: "STO while the axis was disabled",
            0x8103: "Undervoltage power rail",
            0x841C: "STO while the axis was enabled",
        },

        # ['EL7062']
        (0x2, 0x1b963052): {
            0x4101: "Amplifier-Overtemperature",
            0x4102: "PDO-configuration is incompatible to the selected mode of operation",
            0x4103: "Undervoltage Us",
            0x4104: "Overvoltage Us",
            0x410B: "Error detected, but disabled by suppression mask",
            0x4400: "Calibration data corrupted or missing",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x441E: "Invalid configuration of touchprobe inputs",
            0x4424: "Modes of operation invalid",
            0x8103: "Undervoltage Us",
            0x8104: "Amplifier-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8144: "Hardware fault (%d)",
            0x817F: "Error: 0x%X, 0x%X, 0x%X",
            0x81B0: "Content of PDO 0x%X is invalid: Item 0x%X:%X cannot be mapped",
            0x81B1: "Content of PDO 0x%X is invalid: Item 0x%X:%X has an unsupported length (%d bit)",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x840A: "Overall current threshold exceeded",
            0x840B: "Commutation error",
            0x840C: "Motor not connected",
            0x840F: "Configured Commutation Type requires an encoder, but the feedback interface is disabled.",
            0x8415: "Invalid modulo range",
            0x8417: "Maximum rotating field velocity exceeded",
            0x841F: "Torque limitation too low",
            0x8420: "Teach-In Process (%d) failed",
            0x8421: "Teach-In Process Timeout (DC-Link, ...)",
            0x8422: "Drive configuration missing",
            0x8423: "Invalid process data format (number of singleturn bits+multiturn bits != 32)",
            0x8441: "Maximum following error distance exceeded",
            0x8442: "Encoder-Resolution insufficient",
            0x8443: "Combination of Mode of Operation and Commutation Type is invalid",
            0x8449: "Target position not in modulo range",
            0x8450: "Invalid start type 0x%x",
            0x8451: "Invalid limit switch level",
            0x8452: "Drive error during positioning",
            0x8453: "Latch unit will be used by multiple modules",
            0x8454: "Drive not in control",
            0x8455: "Invalid value for Target acceleration",
            0x8456: "Invalid value for Target deceleration",
            0x8457: "Invalid value for Target velocity",
            0x8458: "Invalid value for Target position",
            0x8459: "Emergency stop active",
            0x845A: "Target position exceeds Modulofactor",
            0x845B: "Drive must be disabled",
            0x845D: "Modulo factor invalid",
            0x845E: "Invalid target position window",
        },

        # ['EL7411']
        (0x2, 0x1cf33052): {
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4102: "PDO-configuration is incompatible to the selected mode of operation",
            0x4107: "Undervoltage Up",
            0x4109: "Overvoltage Up",
            0x410A: "Fan",
            0x410B: "Error detected, but disabled by suppression mask",
            0x4301: "Feedback-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x4418: "Limit: Current",
            0x4419: "Limit: Amplifier I2T-model exceeds 100%%",
            0x441A: "Limit: Motor I2T-model exceeds 100%%",
            0x441B: "Limit: Velocity limitation",
            0x441C: "Voltage on Enable-Input missing",
            0x441D: "Internal hardware error",
            0x441E: "Invalid configuration of touchprobe inputs",
            0x8002: "Communication aborted",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x810A: "Fan",
            0x810B: "Undervoltage Up",
            0x810C: "Overvoltage Up",
            0x8135: "Cycletime has to be a multiple of 125 µs",
            0x8144: "Hardware fault (%d)",
            0x817F: "Error: 0x%X, 0x%X, 0x%X",
            0x8302: "Feedback-Error",
            0x8303: "Encoder supply error",
            0x830D: "Encoder Termination overload",
            0x830E: "Overvoltage on encoder track %s",
            0x830F: "Weak signals on encoder track %s",
            0x8340: "Hallsensor supply error",
            0x8341: "Hallsensor-Error",
            0x8342: "Misalignment of hall sensors (offset: %d°)",
            0x8400: "Encoder disabled",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x840B: "Commutation error",
            0x840C: "Motor not connected",
            0x840F: "An Encoder has to be configured in FOC mode",
            0x8417: "Maximum rotating field velocity exceeded",
            0x841C: "Enable input was disabled while the axis was enabled",
            0x841D: "Internal hardware error",
            0x841E: "Number of encoder increments or number of pole pairs incorrect",
            0x841F: "Torque limitation too low",
            0x8420: "Teach-In Process (%d) failed",
            0x8421: "Teach-In Process Timeout (Enable, DC-Link, ...)",
            0x8441: "Maximum following error distance exceeded",
            0x8442: "Encoder-Resolution insufficient",
            0x8443: "Combination of Mode of Operation and Commutation Type is invalid",
            0x8601: "Supply voltage to low",
            0x8602: "Supply voltage to high",
            0x8450: "Invalid start type 0x%x",
            0x8451: "Invalid limit switch level",
            0x8452: "Drive error during positioning",
            0x8453: "Latch unit will be used by multiple modules",
            0x8454: "Drive not in control",
            0x8455: "Invalid value for Target acceleration",
            0x8456: "Invalid value for Target deceleration",
            0x8457: "Invalid value for Target velocity",
            0x8458: "Invalid value for Target position",
            0x8459: "Emergency stop active",
            0x845A: "Target position exceeds Modulofactor",
            0x845B: "Drive must be disabled",
            0x845C: "No Feedback found",
            0x845D: "Modulo factor invalid",
            0x845E: "Invalid target position window",
        },

        # ['EL7201', 'EL7201-0001', 'EL7201-0010', 'EL7201-0011', 'EL7201-9014', 'EL7201-9015']
        (0x2, 0x1c213052): {
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4301: "Encoder-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8103: "No variable linkage",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8135: "Cycletime has to be a multiple of 125 µs",
            0x8302: "Encoder-Error",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x4102: "Discrepancy in the PDO-Configuration",
            0x4418: "Limit: Current",
            0x4419: "Limit: Amplifier I2T-model exceeds 100%%",
            0x441A: "Limit: Motor I2T-model exceeds 100%%",
            0x441B: "Limit: Velocity limitation",
            0x8417: "Maximum rotating field velocity exceeded",
            0x4417: "Motor-Overtemperature",
            0x8137: "Electronic name plate: CRC error",
            0x8416: "Motor-Overtemperature",
            0x441C: "Voltage on STO-Input missing",
            0x441D: "Interner Hardwarefehler",
            0x8304: "OCT communication error",
            0x841C: "STO while the axis was enabled",
            0x841D: "Internal hardware error",
            0x840B: "Motor error or commutation malfunction",
            0x840C: "Phase failure",
            0x4420: "Cogging compensation not supported (%u)",
            0x8146: "Sync-Mode and PDO-Configuration are not compatible",
            0x8441: "Following error",
            0x8450: "Invalid start type 0x%x",
            0x8451: "Invalid limit switch level",
            0x8452: "Drive error during positioning",
            0x8453: "Latch unit will be used by multiple modules",
            0x8454: "Drive not in control",
            0x8455: "Invalid value for Target acceleration",
            0x8456: "Invalid value for Target deceleration",
            0x8457: "Invalid value for Target velocity",
            0x8458: "Invalid value for Target position",
            0x8459: "Emergency stop active",
            0x845A: "Target position exceeds Modulofactor",
            0x845B: "Drive must be disabled",
            0x845C: "No Feedback found",
            0x845D: "Modulo factor invalid",
            0x845E: "Invalid target position window",
            0x8145: "Sync-Mode and PDO-Configuration are not compatible",
        },
    
        # ['EL7211', 'EL7211-0001', 'EL7211-0010', 'EL7211-0011', 'EL7211-9014', 'EL7211-9015']
        (0x2, 0x1c2b3052): {
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4102: "Discrepancy in the PDO-Configuration",
            0x4301: "Feedback-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x4417: "Motor-Overtemperature",
            0x4418: "Limit: Current",
            0x4419: "Limit: Amplifier I2T-model exceeds 100%%",
            0x441A: "Limit: Motor I2T-model exceeds 100%%",
            0x441B: "Limit: Velocity limitation",
            0x441C: "Voltage on STO-Input missing",
            0x441D: "Interner Hardwarefehler",
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8103: "No variable linkage",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8135: "Cycletime has to be a multiple of 125 µs",
            0x8137: "Electronic name plate: CRC error",
            0x8302: "Feedback-Error",
            0x8304: "OCT communication error",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x8416: "Motor-Overtemperature",
            0x8417: "Maximum rotating field velocity exceeded",
            0x841C: "STO while the axis was enabled",
            0x841D: "Internal hardware error",
            0x840B: "Motor error or commutation malfunction",
            0x840C: "Phase failure",
            0x4420: "Cogging compensation not supported (%u)",
            0x8146: "Sync-Mode and PDO-Configuration are not compatible",
            0x8441: "Following error",
            0x8450: "Invalid start type 0x%x",
            0x8451: "Invalid limit switch level",
            0x8452: "Drive error during positioning",
            0x8453: "Latch unit will be used by multiple modules",
            0x8454: "Drive not in control",
            0x8455: "Invalid value for Target acceleration",
            0x8456: "Invalid value for Target deceleration",
            0x8457: "Invalid value for Target velocity",
            0x8458: "Invalid value for Target position",
            0x8459: "Emergency stop active",
            0x845A: "Target position exceeds Modulofactor",
            0x845B: "Drive must be disabled",
            0x845C: "No Feedback found",
            0x845D: "Modulo factor invalid",
            0x845E: "Invalid target position window",
            0x8145: "Sync-Mode and PDO-Configuration are not compatible",
        },
    
        # ['EL7221', 'EL7221-0001', 'EL7221-9014', 'EL7221-9015']
        (0x2, 0x1c353052): {
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4102: "Discrepancy in the PDO-Configuration",
            0x4301: "Encoder-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x4418: "Limit: Current",
            0x4419: "Limit: Amplifier I2T-model exceeds 100%%",
            0x441A: "Limit: Motor I2T-model exceeds 100%%",
            0x441B: "Limit: Velocity limitation",
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8103: "No variable linkage",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8135: "Cycletime has to be a multiple of 125 µs",
            0x8302: "Encoder-Error",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x8417: "Maximum rotating field velocity exceeded",
            0x4417: "Motor-Overtemperature",
            0x441C: "Voltage on STO-Input missing",
            0x441D: "Interner Hardwarefehler",
            0x8137: "Electronic name plate: CRC error",
            0x8304: "OCT communication error",
            0x840B: "Motor error or commutation malfunction",
            0x840C: "Phase failure",
            0x8416: "Motor-Overtemperature",
            0x841C: "STO while the axis was enabled",
            0x841D: "Internal hardware error",
            0x4420: "Cogging compensation not supported (%u)",
            0x8146: "Sync-Mode and PDO-Configuration are not compatible",
            0x8441: "Following error",
            0x8450: "Invalid start type 0x%x",
            0x8451: "Invalid limit switch level",
            0x8452: "Drive error during positioning",
            0x8453: "Latch unit will be used by multiple modules",
            0x8454: "Drive not in control",
            0x8455: "Invalid value for Target acceleration",
            0x8456: "Invalid value for Target deceleration",
            0x8457: "Invalid value for Target velocity",
            0x8458: "Invalid value for Target position",
            0x8459: "Emergency stop active",
            0x845A: "Target position exceeds Modulofactor",
            0x845B: "Drive must be disabled",
            0x845C: "No Feedback found",
            0x845D: "Modulo factor invalid",
            0x845E: "Invalid target position window",
            0x8145: "Sync-Mode and PDO-Configuration are not compatible",
        },

        # ['EP7041-0000', 'EP7041-0002', 'EP7041-1002', 'EP7041-2002', 'EP7041-3002', 'EP7041-3102', 'EP7041-4032']
        (0x2, 0x1b814052): {
            0x1303: "Encoder Supply ok",
            0x1304: "Encoder initialization successfully, channel: %X",
            0x8201: "No communication to field-side (Auxiliary voltage missing)",
            0x8302: "general encoder error, channel: %X",
            0x8303: "Encoder supply error",
            0x8304: "Encoder communication error, channel: %X",
            0x830B: "Encoder Watchdog Error, channel: %X",
            0x830C: "Encoder Single-Cycle-Data Error, channel: %X",
            0x8002: "Communication aborted",
            0x8003: "Configuration error: 0x%X, 0x%X, 0x%X",
            0x1100: "Detection of operation mode completed: 0x%X, %d",
            0x1135: "Cycle time o.k.: %d",
            0x1300: "Position set: %d, %d",
            0x1400: "Drive is calibrated:  %d, %d",
            0x4300: "Subincrements deactivated:  %d, %d",
            0x4400: "Drive is not calibrated:  %d, %d",
            0x4401: "Starttype not supported: 0x%X, %d",
            0x4402: "Command rejected: %d, %d",
            0x4405: "Invalid modulo subtype: %d, %d",
            0x4410: "Target overrun: %d, %d",
            0x8100: "Status word set: 0x%X, %d",
            0x8101: "Operation mode incompatible to PDO interface: 0x%X, %d",
            0x8135: "Large cycle time: %d",
            0x8200: "Write access error: %d, %d",
            0x82FF: "Bootmode not activated",
            0x8300: "Set position error: 0x%X, %d",
            0x8301: "Encoder increments not configured: 0x%X, %d",
            0x8400: "Incorrect drive configuration: %d",
            0x8401: "Limiting of calibration velocity: %d, %d",
            0x8402: "Emergency stop activated: 0x%X, %d",
            0x8405: "Invalid modulo position: %d",
            0x8415: "Invalid modulo factor: %d",
            0x1401: "Actual drive state: 0x%X, %d",
            0x1201: "Communication re-established",
            0x4101: "Terminal-Overtemperature",
            0x4301: "Encoder-Warning",
            0x4411: "DC-Link undervoltage",
            0x4412: "DC-Link overvoltage",
            0x4413: "I2T Amplifier overload",
            0x4414: "I2T Motor overload",
            0x4415: "Speed limitation active",
            0x4416: "Step lost detected at position: 0x%X%X",
            0x8102: "Invalid combination of Inputs and Outputs PDOs",
            0x8104: "Terminal-Overtemperature",
            0x8105: "PD-Watchdog",
            0x8403: "ADC Error",
            0x8404: "Overcurrent",
            0x8406: "Undervoltage DC-Link",
            0x8407: "Overvoltage DC-Link",
            0x8408: "I2T-Model Amplifier overload",
            0x8409: "I2T-Model motor overload",
            0x4403: "Maximum position lag exceeded (%d): channel %d",
            0x8440: "Motor cable not connected",
            0x441C: "STO while the axis was disabled",
            0x8103: "Undervoltage power rail",
            0x81A0: "Error in sync manager configuration: 0x%X",
            0x841C: "STO while the axis was enabled",
        },
    }

    @classmethod
    def get(cls, vendor_id, product_id, text_id, dynamic_data=None):
        ''' get message text from LUT '''

        # find message catalog for device, textid_to_msg = device catalog
        textid_to_msg = None
        for lut_entry in cls.MSG_LUT:
            if vendor_id == lut_entry[0]:
                is_in_tuple = isinstance(lut_entry[1], tuple) and product_id in lut_entry[1]
                is_in_int = isinstance(lut_entry[1], int) and product_id == lut_entry[1]

                if is_in_tuple or is_in_int:
                    textid_to_msg = cls.MSG_LUT[(lut_entry[0], lut_entry[1])]

        # get msg with text_id from device catalog or default catalog
        msg = ""
        text_id = int(text_id, base=16)
        assert isinstance(text_id, int)

        if text_id in cls.MSG_LUT[(0, 0)]:
            msg = cls.MSG_LUT[(0, 0)][text_id]

        if textid_to_msg is not None and text_id in textid_to_msg:
            msg = textid_to_msg[text_id]

        msg = cls.__add_severity_to_msg(text_id, msg)
        msg = cls.__replace_format_specifiers(msg, dynamic_data)
        return msg


    @classmethod
    def __split_dynamic_field(cls, dynamic):

        field = list()
        fields = list()
        is_marker = False

        # split dynamic data using 0x6 0x0 seperator
        for cnt, b in enumerate(dynamic):
            if is_marker is False:
                field.insert(0, b.to_bytes(length=1))

                if b == 6:
                    is_marker = True

                # no more data
                if (len(dynamic) - 1) == cnt:
                    if field != []:
                        fields.append(field)

                continue

            # check second marker
            if b == 0:
                field = field[1:]
                if field != []:
                    fields.append(field)
                field = list()
                is_marker = False

        # flatten each field in fields
        flatten_field = bytes()
        flatten_fields = list()
        for field in fields:
            for token in field:
                flatten_field += token

            flatten_fields.append(flatten_field)
            flatten_field = bytes()

        return flatten_fields


    @classmethod
    def __replace_format_specifiers(cls, msg, dynamic_data):
        '''
        replace format specifiers like %X, %d in msg with data from
        dynamic_data
        '''

        if dynamic_data is None:
            return msg

        sep_dynamic = cls.__split_dynamic_field(dynamic_data)
        index = 0
        is_format_specifier = False
        replaced_msg = ""

        for token in msg:

            if is_format_specifier is False:
                if token == "%":
                    is_format_specifier = True
                else:
                    replaced_msg += token
                continue

            # handle format specifier, unhandled yet %s, %u
            if token == "%":
                replaced_msg += "%"
            elif token in ("X", "x", "d"):
                replace_val = int.from_bytes(sep_dynamic[index], byteorder='big')

                if token in ("X", "x"):
                    replaced_msg += f"{replace_val:0{2*len(sep_dynamic[index])}x}"
                else: # token == "d"
                    replaced_msg += str(replace_val)
                index += 1
            else:
                replace_msg += token

            is_format_specifier = False

        return replaced_msg

    @classmethod
    def __add_severity_to_msg(cls, text_id, msg):

        ret_val = msg

        if text_id < 0x2000:
            ret_val = "(info) " + msg

        elif text_id >= 0x4000 and text_id < 0x5000:
            ret_val = "(warning) " + msg

        elif text_id >= 0x8000 and text_id < 0x9000:
            ret_val = "(error) " + msg

        return ret_val


# -------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(
        prog="ec_diagnostic_messages",
        usage="ec_diagnostic_messages [-h] [-m MASTERID] [-s SLAVEID]",
        description="read diagnostic messages from EtherCAT slaves")

    arg_parser.add_argument('-m', help="EtherCAT master id (default=0)", type=int, default=0)
    arg_parser.add_argument('-s', help="EtherCAT slave id (default=1)", type=int, default=1)
    arg_parser.add_argument('-v', action='version', version='ec_diagnostic_messages v1.1.0')
    arg_parser.add_argument('-t', action='store_true', help="test mode")
    ARGS = arg_parser.parse_args()

    if ARGS.t is False:
        diag_reader = ReadDiagMessage()
        diag_reader.run(ARGS.m, ARGS.s)
    else:
        import pytest
        pytest.main([__file__])

