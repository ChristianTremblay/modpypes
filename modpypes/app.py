#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Application
===========
"""

from bacpypes.debugging import class_debugging, ModuleLogger

from bacpypes.comm import PDU, Client, Server, ServiceAccessPoint, bind
from bacpypes.tcp import TCPClientDirector, TCPServerDirector, StreamToPacket

from pdu import MPDU, request_types, response_types, ExceptionResponse

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   ModbusException
#


class ModbusException(RuntimeError):

    """Helper class for exceptions."""

    _exceptionText = {
        ExceptionResponse.ILLEGAL_FUNCTION: "illegal function",
        ExceptionResponse.ILLEGAL_DATA_ADDRESS: "illegal data address",
        ExceptionResponse.ILLEGAL_DATA_VALUE: "illegal data value",
        ExceptionResponse.ILLEGAL_RESPONSE_LENGTH: "illegal response length",
        ExceptionResponse.ACKNOWLEDGE: "acknowledge",
        ExceptionResponse.SLAVE_DEVICE_BUSY: "slave device busy",
        ExceptionResponse.NEGATIVE_ACKNOWLEDGE: "negative acknowledge",
        ExceptionResponse.MEMORY_PARITY_ERROR: "memory parity error",
        ExceptionResponse.GATEWAY_PATH_UNAVAILABLE:
        "gateway path unavailable",
        ExceptionResponse.GATEWAY_TARGET_DEVICE_FAILED_TO_RESPOND:
        "gateway target device failed to respond",
        }

    def __init__(self, errCode, *args):
        self.errCode = errCode
        text = ModbusException._exceptionText.get(
            errCode,
            "unknown exception %d" % errCode,
            )
        self.args = (text,) + args

#
#   stream_to_packet
#


def stream_to_packet(data):
    """
    Chop a stream of data into MODBUS packets.

    :param data: stream of data
    :returns: a tuple of the data that is a packet with the remaining
        data, or ``None``
    """
    if len(data) < 6:
        return None

    pktlen = (ord(data[4]) << 8) + ord(data[5]) + 6
    if (len(data) < pktlen):
        return None

    return (data[:pktlen], data[pktlen:])


#
#   ModbusServiceAccessPoint
#


@class_debugging
class ModbusServiceAccessPoint(Client, Server, ServiceAccessPoint):
    """
    A service access point so applications can be both a client and
    a server.
    """

    def __init__(self, port=502, sapID=None):
        if _debug: ModbusServiceAccessPoint._debug("__init__ port=%r sapID=%r", port, sapID)
        Client.__init__(self)
        Server.__init__(self)
        ServiceAccessPoint.__init__(self, sapID)

        # create and bind the client side
        self.clientDirector = TCPClientDirector()
        bind(self, StreamToPacket(stream_to_packet), self.clientDirector)

        # create and bind the server side
        self.serverDirector = TCPServerDirector(port)
        bind(self.serverDirector, StreamToPacket(stream_to_packet), self)

    def indication(self, pdu):
        """Got some data from a client."""
        if _debug: ModbusServiceAccessPoint._debug("indication %r", pdu)

        mpdu = MPDU()
        mpdu.decode(pdu)
        if _debug: ModbusServiceAccessPoint._debug("    - mpdu: %r", mpdu)

        # we don't know anything but MODBUS
        if (mpdu.mpduProtocolID != 0):
            return

        # clients shouldn't be sending exceptions
        if (mpdu.mpduFunctionCode >= 128):
            return

        # map the function code
        klass = request_types.get(mpdu.mpduFunctionCode, None)
        if not klass:
            # create an error for now
            resp = ExceptionResponse(
                mpdu.mpduFunctionCode,
                ExceptionResponse.ILLEGAL_FUNCTION,
                )

            # match the transaction information
            resp.pduDestination = mpdu.pduSource
            resp.mpduTransactionID = mpdu.mpduTransactionID

            # return the response to the device
            self.response(pdu)

        req = klass()
        req.decode(mpdu)
        if _debug: ModbusServiceAccessPoint._debug("    - req: %r", req)

        # pass it along to the service element
        self.sap_request(req)

    def confirmation(self, pdu):
        """Got some data from the server."""
        if _debug: ModbusServiceAccessPoint._debug("confirmation %r", pdu)

        mpdu = MPDU()
        mpdu.decode(pdu)
        if _debug: ModbusServiceAccessPoint._debug("    - mpdu: %r", mpdu)

        # we don't know anything but MODBUS
        if (mpdu.mpduProtocolID != 0):
            return

        # may be sending a problem
        if (mpdu.mpduFunctionCode >= 128):
            klass = ExceptionResponse
        else:
            klass = response_types.get(mpdu.mpduFunctionCode, None)
            if not klass:
                return

        resp = klass()
        resp.decode(mpdu)
        if _debug: ModbusServiceAccessPoint._debug("    - resp: %r", resp)

        # pass it along to the service element
        self.sap_response(resp)

    def sap_indication(self, req):
        """Got a request from the ASE."""
        if _debug: ModbusServiceAccessPoint._debug("sap_indication %r", req)

        mpdu = MPDU()
        req.encode(mpdu)
        if _debug: ModbusServiceAccessPoint._debug("    - mpdu: %r", mpdu)

        pdu = PDU()
        mpdu.encode(pdu)
        if _debug: ModbusServiceAccessPoint._debug("    - pdu: %r", pdu)

        # pass it along to the device
        self.request(pdu)

    def sap_confirmation(self, resp):
        """Got a response from the ASE."""
        if _debug: ModbusServiceAccessPoint._debug("sap_confirmation %r", resp)

        mpdu = MPDU()
        resp.encode(mpdu)
        if _debug: ModbusServiceAccessPoint._debug("    - mpdu: %r", mpdu)

        pdu = PDU()
        mpdu.encode(pdu)
        if _debug: ModbusServiceAccessPoint._debug("    - pdu: %r", pdu)

        # return the response to the device
        self.response(pdu)

#
#   ModbusClient
#

@class_debugging
class ModbusClient(Client, Server):

    """This class simplifies building MODBUS client applications.  All of
    the PDUs are MODBUS.
    """

    def __init__(self, **kwargs):
        """Initialize a MODBUS client."""
        if _debug: ModbusClient._debug("__init__ %r", kwargs)
        Client.__init__(self)
        Server.__init__(self)

        # create and bind the client side
        self.clientDirector = TCPClientDirector(**kwargs)
        bind(self, StreamToPacket(stream_to_packet), self.clientDirector)

    def indication(self, req):
        """Got a request from the application."""
        if _debug: ModbusClient._debug("indication %r", req)

        # encode it as a generic MPDU
        mpdu = MPDU()
        req.encode(mpdu)
        if _debug: ModbusClient._debug("    - mpdu: %r", mpdu)

        # encode it as a PDU
        pdu = PDU()
        mpdu.encode(pdu)
        if _debug: ModbusClient._debug("    - pdu: %r", pdu)

        # pass it along to the device
        self.request(pdu)

    def confirmation(self, pdu):
        """Got a response from the server."""
        if _debug: ModbusClient._debug("confirmation %r", pdu)

        # generic decode
        mpdu = MPDU()
        mpdu.decode(pdu)
        if _debug: ModbusClient._debug("    - mpdu: %r", mpdu)

        # we don't know anything but MODBUS
        if (mpdu.mpduProtocolID != 0):
            return

        # may be sending a problem
        if (mpdu.mpduFunctionCode >= 128):
            klass = ExceptionResponse
        else:
            klass = response_types.get(mpdu.mpduFunctionCode, None)
            if not klass:
                return

        resp = klass()
        resp.decode(mpdu)
        if _debug: ModbusClient._debug("    - resp: %r", resp)

        # pass it along to the application
        self.response(resp)

#
#   ModbusServer
#

@class_debugging
class ModbusServer(Client, Server):

    def __init__(self, port=502, **kwargs):
        if _debug: ModbusServer._debug("__init__ port=%r %r", port, kwargs)
        Client.__init__(self)
        Server.__init__(self)

        # create and bind
        self.serverDirector = TCPServerDirector(('', port), **kwargs)
        bind(self, StreamToPacket(stream_to_packet), self.serverDirector)

    def confirmation(self, pdu):
        """This is a request from a client."""
        if _debug: ModbusServer._debug("confirmation %r", pdu)

        # generic decoding
        mpdu = MPDU()
        mpdu.decode(pdu)
        if _debug: ModbusServer._debug("    - mpdu: %r", mpdu)

        # we don't know anything but MODBUS
        if (mpdu.mpduProtocolID != 0):
            return

        # clients shouldn't be sending exceptions
        if (mpdu.mpduFunctionCode >= 128):
            return

        # map the function code
        klass = request_types.get(mpdu.mpduFunctionCode, None)
        if not klass:
            # create an error for now
            resp = ExceptionResponse(
                mpdu.mpduFunctionCode,
                ExceptionResponse.ILLEGAL_FUNCTION,
                )

            # match the transaction information
            resp.pduDestination = mpdu.pduSource
            resp.mpduTransactionID = mpdu.mpduTransactionID
            if _debug: ModbusServer._debug("    - resp: %r", resp)

            # return the response to the device
            self.request(resp)

        req = klass()
        req.decode(mpdu)
        if _debug: ModbusServer._debug("    - req: %r", req)

        # pass it along to the application
        self.response(req)

    def indication(self, resp):
        """This is a response from the application."""
        if _debug: ModbusServer._debug("indication %r", resp)

        # encode as a generic MPDU
        mpdu = MPDU()
        resp.encode(mpdu)
        if _debug: ModbusServer._debug("    - mpdu: %r", mpdu)

        # encode as a generic PDU
        pdu = PDU()
        mpdu.encode(pdu)
        if _debug: ModbusServer._debug("    - pdu: %r", pdu)

        # return the response to the device
        self.request(pdu)
