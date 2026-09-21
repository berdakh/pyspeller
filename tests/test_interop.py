"""The server must stay wire compatible with the rest of buffer_bci.

This drives the pure-python server with the framework's own FieldTrip client
(dataAcq/buffer/python/FieldTrip.py), the same one the matlab, java and C
clients implement, so a pyspeller buffer can be used by any of them.
"""
import os
import sys
import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer

FIELDTRIP_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'dataAcq', 'buffer', 'python'))


@unittest.skipUnless(os.path.exists(os.path.join(FIELDTRIP_DIR, 'FieldTrip.py')),
                     'the buffer_bci FieldTrip client is not next to this package')
class TestFieldTripInterop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, FIELDTRIP_DIR)
        import FieldTrip
        cls.FieldTrip = FieldTrip

    def setUp(self):
        self.server = BufferServer(port=0).start()
        self.client = self.FieldTrip.Client()
        self.client.connect('localhost', self.server.port)
        self.addCleanup(self.server.stop)
        self.addCleanup(self.client.disconnect)

    def test_fieldtrip_client_reads_a_header_written_by_our_client(self):
        writer = BufferClient(port=self.server.port).connect()
        self.addCleanup(writer.disconnect)
        writer.put_header(3, 256.0, labels=['Fz', 'Cz', 'Pz'])
        header = self.client.getHeader()
        self.assertEqual(header.nChannels, 3)
        self.assertEqual(header.fSample, 256.0)
        self.assertEqual(header.labels, ['Fz', 'Cz', 'Pz'])

    def test_fieldtrip_client_writes_data_our_client_reads(self):
        self.client.putHeader(2, 100.0, self.FieldTrip.DATATYPE_FLOAT32)
        samples = np.arange(8, dtype='float32').reshape(4, 2)
        self.client.putData(samples)
        reader = BufferClient(port=self.server.port).connect()
        self.addCleanup(reader.disconnect)
        np.testing.assert_allclose(reader.get_data(0, 3), samples)

    def test_events_cross_both_ways(self):
        self.client.putHeader(1, 100.0, self.FieldTrip.DATATYPE_FLOAT32)
        self.client.putEvents(self.FieldTrip.Event('stimulus.tgtFlash', '1', 5))
        reader = BufferClient(port=self.server.port).connect()
        self.addCleanup(reader.disconnect)
        events = reader.get_events()
        self.assertEqual((events[0].type, events[0].value, events[0].sample),
                         ('stimulus.tgtFlash', '1', 5))

        reader.send_event('classifier.prediction', 'H')
        received = self.client.getEvents()
        self.assertEqual(received[-1].type, 'classifier.prediction')
        self.assertEqual(received[-1].value, 'H')

    def test_poll_and_wait_answer_the_fieldtrip_client(self):
        self.client.putHeader(1, 100.0, self.FieldTrip.DATATYPE_FLOAT32)
        self.client.putData(np.zeros((6, 1), dtype='float32'))
        self.assertEqual(self.client.poll(), (6, 0))
        self.assertEqual(self.client.wait(0, 0, 100), (6, 0))


if __name__ == '__main__':
    unittest.main()
