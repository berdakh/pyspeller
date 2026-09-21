"""FieldTrip buffer (V1) wire protocol: constants, (de)serialisation.

This is a complete, dependency-light implementation of the protocol used by
the rest of buffer_bci, so the pure-python server/client here stay wire
compatible with the C/java/matlab clients of the main framework.
"""
import struct

import numpy as np

VERSION = 1

PUT_HDR = 0x101
PUT_DAT = 0x102
PUT_EVT = 0x103
PUT_OK = 0x104
PUT_ERR = 0x105
GET_HDR = 0x201
GET_DAT = 0x202
GET_EVT = 0x203
GET_OK = 0x204
GET_ERR = 0x205
FLUSH_HDR = 0x301
FLUSH_DAT = 0x302
FLUSH_EVT = 0x303
FLUSH_OK = 0x304
FLUSH_ERR = 0x305
WAIT_DAT = 0x402
WAIT_OK = 0x404
WAIT_ERR = 0x405

DATATYPE_CHAR = 0
DATATYPE_UINT8 = 1
DATATYPE_UINT16 = 2
DATATYPE_UINT32 = 3
DATATYPE_UINT64 = 4
DATATYPE_INT8 = 5
DATATYPE_INT16 = 6
DATATYPE_INT32 = 7
DATATYPE_INT64 = 8
DATATYPE_FLOAT32 = 9
DATATYPE_FLOAT64 = 10
DATATYPE_UNKNOWN = 0xFFFFFFFF

CHUNK_CHANNEL_NAMES = 1

# fieldtrip datatype -> numpy dtype name, indexed by the datatype code
NUMPY_TYPE = ['uint8', 'uint8', 'uint16', 'uint32', 'uint64',
              'int8', 'int16', 'int32', 'int64', 'float32', 'float64']
WORD_SIZE = [1, 1, 2, 4, 8, 1, 2, 4, 8, 4, 8]
_NP_TO_FT = {'uint8': DATATYPE_UINT8, 'uint16': DATATYPE_UINT16,
             'uint32': DATATYPE_UINT32, 'uint64': DATATYPE_UINT64,
             'int8': DATATYPE_INT8, 'int16': DATATYPE_INT16,
             'int32': DATATYPE_INT32, 'int64': DATATYPE_INT64,
             'float32': DATATYPE_FLOAT32, 'float64': DATATYPE_FLOAT64}

HEADER_SIZE = 8  # bytes of a request/response header


class ProtocolError(IOError):
    """Raised when a peer sends something that is not valid protocol."""


def numpy_to_ft_type(dtype):
    """FieldTrip datatype code for a numpy dtype (raises for unsupported)."""
    name = np.dtype(dtype).name
    if name not in _NP_TO_FT:
        raise ProtocolError('unsupported data type: %s' % name)
    return _NP_TO_FT[name]


def pack_message(command, payload=b'', endian='<'):
    """A complete request/response message: 8 byte header + payload."""
    return struct.pack(endian + 'HHI', VERSION, command, len(payload)) + payload


def unpack_message_header(raw, endian=None):
    """(version, command, payload_size, endian) from the 8 byte header.

    When `endian` is None the byte order is detected from the version field,
    exactly like the C server does, so little- and big-endian peers interoperate.
    """
    if len(raw) < HEADER_SIZE:
        raise ProtocolError('short message header')
    for order in ([endian] if endian else ['<', '>']):
        version, command, size = struct.unpack(order + 'HHI', raw[:HEADER_SIZE])
        if version == VERSION:
            return version, command, size, order
    raise ProtocolError('bad protocol version in message header')


class Header:
    """Dataset description: channel count, sample rate, sample type."""

    def __init__(self, nchannels=0, fsample=0.0, data_type=DATATYPE_FLOAT32,
                 labels=None, nsamples=0, nevents=0):
        self.nchannels = int(nchannels)
        self.fsample = float(fsample)
        self.data_type = int(data_type)
        self.labels = list(labels) if labels else []
        self.nsamples = int(nsamples)
        self.nevents = int(nevents)

    @property
    def dtype(self):
        return np.dtype(NUMPY_TYPE[self.data_type])

    def __repr__(self):
        return ('Header(nchannels=%d, fsample=%g, nsamples=%d, nevents=%d, type=%s)'
                % (self.nchannels, self.fsample, self.nsamples, self.nevents,
                   NUMPY_TYPE[self.data_type]))

    def serialize(self, endian='<'):
        chunks = b''
        if self.labels:
            names = b''.join(l.encode('utf8') + b'\0' for l in self.labels)
            chunks = struct.pack(endian + 'II', CHUNK_CHANNEL_NAMES, len(names)) + names
        return struct.pack(endian + 'IIIfII', self.nchannels, self.nsamples,
                           self.nevents, self.fsample, self.data_type,
                           len(chunks)) + chunks

    @staticmethod
    def deserialize(buf, endian='<'):
        if len(buf) < 24:
            raise ProtocolError('short header packet')
        nchans, nsamp, nevt, fsamp, dtype, chunk_size = struct.unpack(
            endian + 'IIIfII', buf[:24])
        hdr = Header(nchans, fsamp, dtype, nsamples=nsamp, nevents=nevt)
        offset, end = 24, min(len(buf), 24 + chunk_size)
        while offset + 8 <= end:
            chunk_type, chunk_len = struct.unpack(endian + 'II', buf[offset:offset + 8])
            offset += 8
            body = buf[offset:offset + chunk_len]
            offset += chunk_len
            if chunk_type == CHUNK_CHANNEL_NAMES:
                labels = body.decode('utf8', 'replace').split('\0')
                hdr.labels = labels[:hdr.nchannels]
        return hdr


class Event:
    """A buffer event: a (type, value) pair stamped at a sample index."""

    def __init__(self, type='', value='', sample=-1, offset=0, duration=0):
        self.type = type
        self.value = value
        self.sample = int(sample)
        self.offset = int(offset)
        self.duration = int(duration)

    def __repr__(self):
        return 'Event(%r, %r, sample=%d)' % (self.type, self.value, self.sample)

    def __eq__(self, other):
        return (isinstance(other, Event) and self.type == other.type
                and self.value == other.value and self.sample == other.sample
                and self.offset == other.offset and self.duration == other.duration)

    @staticmethod
    def _serialize_field(value, endian):
        """(datatype, numel, bytes) for an event type/value field."""
        if isinstance(value, str):
            raw = value.encode('utf8')
            return DATATYPE_CHAR, len(raw), raw
        if isinstance(value, (bool, np.bool_)):
            value = int(value)
        if isinstance(value, (int, np.integer)):
            return DATATYPE_INT32, 1, struct.pack(endian + 'i', int(value))
        if isinstance(value, (float, np.floating)):
            return DATATYPE_FLOAT64, 1, struct.pack(endian + 'd', float(value))
        arr = np.asarray(value)
        if arr.dtype.kind in 'US':  # list of strings -> newline joined text
            raw = '\n'.join(str(v) for v in arr.ravel()).encode('utf8')
            return DATATYPE_CHAR, len(raw), raw
        if arr.dtype.kind in 'ib':
            arr = arr.astype('int32')
        elif arr.dtype.kind == 'f':
            arr = arr.astype('float64')
        ft = numpy_to_ft_type(arr.dtype)
        raw = arr.astype(arr.dtype.newbyteorder(endian)).tobytes()
        return ft, arr.size, raw

    @staticmethod
    def _deserialize_field(ft_type, numel, raw, endian):
        if ft_type == DATATYPE_CHAR:
            return raw.decode('utf8', 'replace')
        dtype = np.dtype(NUMPY_TYPE[ft_type]).newbyteorder(endian)
        arr = np.frombuffer(raw, dtype=dtype, count=numel).astype(
            np.dtype(NUMPY_TYPE[ft_type]))
        return arr.item() if arr.size == 1 else arr

    def serialize(self, endian='<'):
        t_type, t_numel, t_buf = self._serialize_field(self.type, endian)
        v_type, v_numel, v_buf = self._serialize_field(self.value, endian)
        head = struct.pack(endian + 'IIIIiiiI', t_type, t_numel, v_type, v_numel,
                           self.sample, self.offset, self.duration,
                           len(t_buf) + len(v_buf))
        return head + t_buf + v_buf

    @staticmethod
    def deserialize(buf, endian='<'):
        """(event, bytes_consumed); (None, 0) when the buffer is exhausted."""
        if len(buf) < 32:
            return None, 0
        (t_type, t_numel, v_type, v_numel, sample, offset, duration,
         body_size) = struct.unpack(endian + 'IIIIiiiI', buf[:32])
        if t_type >= len(WORD_SIZE) or v_type >= len(WORD_SIZE):
            raise ProtocolError('event with unknown field type')
        t_size = t_numel * WORD_SIZE[t_type]
        v_size = v_numel * WORD_SIZE[v_type]
        if 32 + body_size > len(buf) or t_size + v_size > body_size:
            raise ProtocolError('event does not fit in the given buffer')
        evt = Event(
            Event._deserialize_field(t_type, t_numel, buf[32:32 + t_size], endian),
            Event._deserialize_field(v_type, v_numel,
                                     buf[32 + t_size:32 + t_size + v_size], endian),
            sample, offset, duration)
        return evt, 32 + body_size

    @staticmethod
    def deserialize_many(buf, endian='<'):
        events, offset = [], 0
        while offset < len(buf):
            evt, used = Event.deserialize(buf[offset:], endian)
            if used == 0:
                break
            events.append(evt)
            offset += used
        return events


def serialize_data(samples, endian='<'):
    """Data packet payload for a [nsamples x nchannels] array."""
    samples = np.atleast_2d(np.asarray(samples))
    ft_type = numpy_to_ft_type(samples.dtype)
    raw = samples.astype(samples.dtype.newbyteorder(endian), copy=False).tobytes()
    nsamp, nchan = samples.shape
    return struct.pack(endian + 'IIII', nchan, nsamp, ft_type, len(raw)) + raw


def deserialize_data(buf, endian='<'):
    """[nsamples x nchannels] array from a data packet payload."""
    if len(buf) < 16:
        raise ProtocolError('short data packet')
    nchan, nsamp, ft_type, body_size = struct.unpack(endian + 'IIII', buf[:16])
    if ft_type >= len(NUMPY_TYPE):
        raise ProtocolError('data packet with unknown sample type')
    dtype = np.dtype(NUMPY_TYPE[ft_type]).newbyteorder(endian)
    expected = nchan * nsamp * WORD_SIZE[ft_type]
    if body_size < expected or len(buf) < 16 + expected:
        raise ProtocolError('truncated data packet')
    arr = np.frombuffer(buf, dtype=dtype, count=nchan * nsamp, offset=16)
    return arr.reshape(nsamp, nchan).astype(np.dtype(NUMPY_TYPE[ft_type]))


def recv_exactly(sock, nbytes):
    """Read exactly nbytes from a socket, or raise if the peer goes away."""
    chunks, got = [], 0
    while got < nbytes:
        chunk = sock.recv(nbytes - got)
        if not chunk:
            raise ProtocolError('connection closed while reading %d bytes' % nbytes)
        chunks.append(chunk)
        got += len(chunk)
    return b''.join(chunks)
