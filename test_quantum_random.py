"""Behavioral checks: python -m unittest -v (no third-party packages)."""

from pathlib import Path
import random
import subprocess
import sys
import unittest

from quantum_random import quantum_numbers, summarize


class RandomTests(unittest.TestCase):
    def test_widths_and_count(self):
        for bits in (1, 4, 8, 32, 64):
            with self.subTest(bits=bits):
                values = list(quantum_numbers(bits, 53, seed=42))
                self.assertEqual(len(values), 53)
                self.assertTrue(all(0 <= x < 2**bits for x in values))
                self.assertTrue(any(x >= 2**(bits - 1) for x in values))

    def test_repeatability_and_global_state(self):
        before = random.getstate()
        first = list(quantum_numbers(8, 32, seed=7))
        self.assertEqual(first, list(quantum_numbers(8, 32, seed=7)))
        self.assertEqual(before, random.getstate())

    def test_validation_is_immediate(self):
        for bits, count in ((0, 1), (65, 1), (8, 0), (8, -1)):
            with self.subTest(bits=bits, count=count), self.assertRaises(ValueError):
                quantum_numbers(bits, count)
        for bits, count in ((True, 1), (1.5, 1), (8, False), (8, "2")):
            with self.subTest(bits=bits, count=count), self.assertRaises(TypeError):
                quantum_numbers(bits, count)

    def test_large_stream_is_lazy(self):
        values = quantum_numbers(8, 10**12, seed=3)
        self.assertIs(iter(values), values)
        self.assertTrue(0 <= next(values) < 256)

    def test_summary_matches_stream(self):
        values = list(quantum_numbers(8, 200, seed=9))
        result = summarize(8, 200, seed=9)
        self.assertEqual(result.preview, tuple(values[:8]))
        self.assertAlmostEqual(result.mean, sum(values) / 200)
        self.assertAlmostEqual(result.one_fraction,
                               sum(bin(x).count("1") for x in values) / 1600)
        self.assertEqual(sum(result.bins), 200)
        for i, count in enumerate(result.bins):
            self.assertEqual(count, sum(i * 16 <= x < (i + 1) * 16 for x in values))

    def test_summary_limits_and_baseline(self):
        for bits in (1, 8, 64):
            for baseline in (False, True):
                with self.subTest(bits=bits, baseline=baseline):
                    result = summarize(bits, 100, seed=42, baseline=baseline)
                    self.assertEqual(sum(result.bins), 100)
                    self.assertEqual(len(result.bins), min(2**bits, 16))
                    self.assertEqual(len(result.preview), 8)
                    self.assertTrue(0 <= result.one_fraction <= 1)

    def test_single_sample(self):
        result = summarize(1, 1, seed=0)
        self.assertEqual(sum(result.bins), 1)
        self.assertEqual(len(result.preview), 1)

    def test_cli(self):
        script = str(Path(__file__).with_name("quantum_random.py"))
        result = subprocess.run([sys.executable, script, "--count", "20", "--seed", "42"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Bit strings:", result.stdout)
        result = subprocess.run([sys.executable, script, "--bits", "65"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
