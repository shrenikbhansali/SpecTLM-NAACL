import unittest
from unittest.mock import patch
from types import SimpleNamespace
from ops.queue import gpu_idle_busy, remap_resume_path


class QueueGuardTests(unittest.TestCase):
    def test_low_memory_busy_gpu_is_rejected(self):
        with patch('ops.queue.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='983, 100\n1234\n')):
            self.assertTrue(gpu_idle_busy('heck-srv1',3))

    def test_idle_allocated_process_rejected(self):
        with patch('ops.queue.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='5, 0\n1234\n')):
            self.assertTrue(gpu_idle_busy('heck-srv1',3))

    def test_idle_empty_admitted(self):
        with patch('ops.queue.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='2, 0\n')):
            self.assertFalse(gpu_idle_busy('heck-srv1',3))

    def test_query_error_fails_closed(self):
        with patch('ops.queue.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')):
            self.assertTrue(gpu_idle_busy('heck-srv1',3))

    def test_resume_remap_is_prefix_scoped(self):
        mapping=['/old/root=/new/root']
        self.assertEqual(remap_resume_path('/old/root/artifacts/run',mapping),'/new/root/artifacts/run')
        self.assertEqual(remap_resume_path('/old/root2/run',mapping),'/old/root2/run')
        self.assertEqual(remap_resume_path('/old/root/artifacts/run',[]),'/old/root/artifacts/run')


if __name__=='__main__':unittest.main()
