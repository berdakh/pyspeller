import unittest

import numpy as np

from pyspeller.buffer import protocol as P
from pyspeller.buffer.protocol import Event, Header


class TestProtocol(unittest.TestCase):
    def test_message_header_roundtrip(self):
        raw = P.pack_message(P.GET_HDR, b'abc')
        version, command, size, endian = P.unpack_message_header(raw)
        self.assertEqual((version, command, size, endian), (1, P.GET_HDR, 3, '<'))

    def test_byte_order_is_detected(self):
        raw = P.pack_message(P.PUT_DAT, b'', endian='>')
        _, command, _, endian = P.unpack_message_header(raw)
        self.assertEqual((command, endian), (P.PUT_DAT, '>'))

    def test_bad_version_is_rejected(self):
        with self.assertRaises(P.ProtocolError):
            P.unpack_message_header(b'\x09\x00\x01\x01\x00\x00\x00\x00')

    def test_header_roundtrip_with_labels(self):
        hdr = Header(3, 256.0, P.DATATYPE_FLOAT32, ['Fz', 'Cz', 'Pz'])
        out = Header.deserialize(hdr.serialize())
        self.assertEqual((out.nchannels, out.fsample), (3, 256.0))
        self.assertEqual(out.labels, ['Fz', 'Cz', 'Pz'])

    def test_event_roundtrip_string_and_numbers(self):
        for value in ['hello', 7, 2.5, np.array([1.0, 2.0, 3.0])]:
            evt = Event('stimulus.test', value, sample=42, duration=3)
            out, used = Event.deserialize(evt.serialize())
            self.assertEqual(used, len(evt.serialize()))
            self.assertEqual(out.sample, 42)
            self.assertEqual(out.duration, 3)
            if isinstance(value, np.ndarray):
                np.testing.assert_allclose(out.value, value)
            else:
                self.assertEqual(out.value, value)

    def test_several_events_in_one_buffer(self):
        events = [Event('a', 1, sample=1), Event('b', 'two', sample=2)]
        raw = b''.join(e.serialize() for e in events)
        self.assertEqual(Event.deserialize_many(raw), events)

    def test_data_roundtrip(self):
        data = np.arange(12, dtype='float32').reshape(4, 3)
        out = P.deserialize_data(P.serialize_data(data))
        np.testing.assert_allclose(out, data)
        self.assertEqual(out.dtype, np.dtype('float32'))

    def test_truncated_data_packet_is_rejected(self):
        raw = P.serialize_data(np.zeros((4, 3), dtype='float32'))
        with self.assertRaises(P.ProtocolError):
            P.deserialize_data(raw[:20])


if __name__ == '__main__':
    unittest.main()
