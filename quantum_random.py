"""Simulate a quantum random-number circuit using Python 3.10+ only.

Circuit: prepare k qubits in |0>, apply H to each, then measure all k.
The ideal result is uniform on 0..2**k-1. This program samples that known
distribution with a classical PRNG, not physical quantum randomness.
Run: python quantum_random.py --bits 8 --count 100000 --seed 42
"""

import argparse
from dataclasses import dataclass
import random
from time import perf_counter
from typing import Iterator


def validate(bits: int, count: int) -> None:
    """Require a 1..64-bit width and a positive sample count."""
    for name, value in (("bits", bits), ("count", count)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
    if not 1 <= bits <= 64:
        raise ValueError("bits must be between 1 and 64")
    if count <= 0:
        raise ValueError("count must be positive")


def quantum_numbers(bits: int, count: int, seed=None) -> Iterator[int]:
    """Return a lazy stream of simulated k-qubit measurement outcomes.

    Validation is immediate. getrandbits(k) samples all k independent bits
    together, avoiding a 2**k-amplitude state vector or a per-qubit loop.
    A local generator leaves the module's global random state unchanged.
    """
    validate(bits, count)
    draw = random.Random(seed).getrandbits
    return (draw(bits) for _ in range(count))


@dataclass(frozen=True)
class Summary:
    """Aggregate statistics with at most 16 bins and 8 example values."""

    bins: tuple[int, ...]
    preview: tuple[int, ...]
    mean: float
    one_fraction: float
    elapsed: float


def summarize(bits: int, count: int, seed=None, baseline=False) -> Summary:
    """Time sampling plus aggregation; optionally use randrange as baseline.

    Both methods use Python's same PRNG family. Neither is quantum hardware.
    Adjacent integer values share a bin when the width exceeds four bits.
    """
    validate(bits, count)
    start = perf_counter()
    size = 1 << bits
    if baseline:
        draw = random.Random(seed).randrange
        values = (draw(size) for _ in range(count))
    else:
        values = quantum_numbers(bits, count, seed)
    bins = [0] * min(size, 16)
    shift = max(0, bits - 4)
    preview = []
    total = ones = 0
    for value in values:
        bins[value >> shift] += 1
        total += value
        ones += value.bit_count()
        if len(preview) < 8:
            preview.append(value)
    return Summary(tuple(bins), tuple(preview), total / count,
                   ones / (bits * count), perf_counter() - start)


def main() -> None:
    """Compare distributions, print examples, and draw a terminal histogram."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bits", type=int, default=8, help="qubits per number: 1..64")
    parser.add_argument("--count", type=int, default=10_000, help="positive sample count")
    parser.add_argument("--seed", type=int, help="optional reproducible seed")
    args = parser.parse_args()
    try:
        validate(args.bits, args.count)
    except (TypeError, ValueError) as error:
        parser.error(str(error))
    quantum = summarize(args.bits, args.count, args.seed)
    # Different seeds avoid using exactly the same seeded stream in both modes.
    # This is not a claim of cryptographic independence.
    other_seed = None if args.seed is None else args.seed + 1
    classic = summarize(args.bits, args.count, other_seed, baseline=True)
    print("Ideal quantum-outcome simulation vs Python randrange")
    print("Both use classical pseudorandomness, not a hardware QRNG.\n")
    for label, result in (("Simulated circuit", quantum), ("randrange", classic)):
        strings = " ".join(format(n, f"0{args.bits}b") for n in result.preview)
        print(f"{label}: first integers {result.preview}")
        print(f"  Bit strings: {strings}")
        print(f"  Mean: {result.mean:.4f}; fraction of 1 bits: {result.one_fraction:.4%}")
        print(f"  Sampling + aggregation: {result.elapsed:.6f} s")
    print(f"Expected mean: {((1 << args.bits) - 1) / 2:.4f}; 1 bits: 50%\n")
    print("Range                      simulated    randrange    simulated bar")
    width, peak = 1 << max(0, args.bits - 4), max(quantum.bins)
    for i, (q, c) in enumerate(zip(quantum.bins, classic.bins)):
        bar = "#" * round(40 * q / peak)
        print(f"{i * width:>10}-{(i + 1) * width - 1:<10}  "
              f"{q / args.count:9.2%}  {c / args.count:9.2%}    {bar}")
    print("Bars scale to the largest simulated bin; percentages use all samples.")


if __name__ == "__main__":
    main()
