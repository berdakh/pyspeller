import threading
import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer, Event


class BufferTestCase(unittest.TestCase):
    def setUp(self):
        self.server = BufferServer(port=0, max_samples=500).start()
        self.client = BufferClient(port=self.server.port).connect()
        self.addCleanup(self.server.stop)
        self.addCleanup(self.client.disconnect)


class TestBufferBasics(BufferTestCase):
    def test_header_is_empty_before_it_is_written(self):
        self.assertIsNone(self.client.get_header())

    def test_put_and_get_data(self):
        self.client.put_header(2, 100.0, labels=['a', 'b'])
        data = np.arange(20, dtype='float32').reshape(10, 2)
        self.client.put_data(data)
        np.testing.assert_allclose(self.client.get_data(0, 9), data)
        np.testing.assert_allclose(self.client.get_data(3, 4), data[3:5])
        self.assertEqual(self.client.poll(), (10, 0))

    def test_ring_buffer_keeps_the_most_recent_samples(self):
        self.client.put_header(1, 100.0)
        for block in range(6):                      # 600 samples into a 500 ring
            self.client.put_data(np.arange(block * 100, (block + 1) * 100,
                                           dtype='float32').reshape(100, 1))
        self.assertEqual(self.client.poll()[0], 600)
        np.testing.assert_allclose(self.client.get_data(599, 599), [[599.0]])
        np.testing.assert_allclose(self.client.get_data(100, 100), [[100.0]])
        with self.assertRaises(IOError):            # fell out of the ring
            self.client.get_data(0, 0)

    def test_events_are_stamped_with_the_current_sample(self):
        self.client.put_header(1, 100.0)
        self.client.put_data(np.zeros((7, 1), dtype='float32'))
        self.client.send_event('stimulus.tgtFlash', 1)
        events = self.client.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].sample, 7)
        self.assertEqual(events[0].value, 1)

    def test_explicit_event_sample_is_kept(self):
        self.client.put_header(1, 100.0)
        self.client.put_events([Event('marker', 'x', sample=3)])
        self.assertEqual(self.client.get_events()[0].sample, 3)

    def test_event_cursor_returns_only_new_events(self):
        self.client.put_header(1, 100.0)
        self.client.reset_event_cursor()
        self.client.send_event('a', '1')
        self.assertEqual([e.type for e in self.client.new_events()], ['a'])
        self.assertEqual(self.client.new_events(), [])
        self.client.send_event('b', '2')
        self.assertEqual([e.type for e in self.client.new_events()], ['b'])

    def test_wait_blocks_until_data_arrives(self):
        self.client.put_header(1, 100.0)
        writer = BufferClient(port=self.server.port).connect()
        self.addCleanup(writer.disconnect)
        threading.Timer(0.2, lambda: writer.put_data(
            np.zeros((5, 1), dtype='float32'))).start()
        nsamples, _ = self.client.wait(0, 0xFFFFFFFF, 3000)
        self.assertEqual(nsamples, 5)

    def test_wait_times_out_without_data(self):
        self.client.put_header(1, 100.0)
        self.assertEqual(self.client.wait(0, 0xFFFFFFFF, 100), (0, 0))

    def test_flush_events(self):
        self.client.put_header(1, 100.0)
        self.client.send_event('a', '1')
        self.client._request(0x303, b'')             # FLUSH_EVT
        self.assertEqual(self.client.get_events(), [])

    def test_wrong_channel_count_is_refused(self):
        self.client.put_header(2, 100.0)
        with self.assertRaises(IOError):
            self.client.put_data(np.zeros((4, 3), dtype='float32'))

    def test_several_clients_share_the_buffer(self):
        self.client.put_header(1, 100.0)
        other = BufferClient(port=self.server.port).connect()
        self.addCleanup(other.disconnect)
        other.put_data(np.ones((4, 1), dtype='float32'))
        np.testing.assert_allclose(self.client.get_data(0, 3), np.ones((4, 1)))

    def test_wait_for_header(self):
        writer = BufferClient(port=self.server.port).connect()
        self.addCleanup(writer.disconnect)
        threading.Timer(0.2, lambda: writer.put_header(4, 250.0)).start()
        header = self.client.wait_for_header(timeout=3.0)
        self.assertEqual((header.nchannels, header.fsample), (4, 250.0))


if __name__ == '__main__':
    unittest.main()


class TestEventDelivery(BufferTestCase):
    """No event may be lost because another one was being waited for."""

    def setUp(self):
        super().setUp()
        self.client.put_header(1, 100.0)
        self.client.reset_event_cursor()
        self.writer = BufferClient(port=self.server.port).connect()
        self.addCleanup(self.writer.disconnect)

    def test_waiting_for_one_event_keeps_the_others(self):
        self.writer.send_event('speller.edit', 'DEL')
        self.writer.send_event('classifier.prediction', 'I')
        self.writer.send_event('stimulus.sequence', 'end')

        first = self.client.wait_for_event('speller.edit', timeout=2)
        self.assertEqual(first.value, 'DEL')
        # the two events that arrived in the same batch are still to come
        rest = [(e.type, e.value) for e in self.client.new_events(timeout_ms=500)]
        self.assertEqual(rest, [('classifier.prediction', 'I'),
                                ('stimulus.sequence', 'end')])

    def test_a_second_wait_sees_an_event_from_the_first_batch(self):
        self.writer.send_event('a', '1')
        self.writer.send_event('b', '2')
        self.assertEqual(self.client.wait_for_event('a', timeout=2).value, '1')
        self.assertEqual(self.client.wait_for_event('b', timeout=2).value, '2')

    def test_resetting_the_cursor_drops_what_was_held_back(self):
        self.writer.send_event('a', '1')
        self.writer.send_event('b', '2')
        self.client.wait_for_event('a', timeout=2)
        self.client.reset_event_cursor()
        self.assertEqual(self.client.new_events(timeout_ms=100), [])
