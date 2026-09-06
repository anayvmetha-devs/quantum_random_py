# How the quantum random-number simulator works

## The quantum model

Prepare k qubits in `|0>`, apply a Hadamard gate H to each, and measure each qubit.
H changes `|0>` to `(|0> + |1>) / sqrt(2)`. Squaring either amplitude's magnitude
gives a measurement probability of one half. See
[IBM's explanation of the Hadamard gate](https://quantum.cloud.ibm.com/learning/en/courses/use-a-qc-today/quantum-mechanics-basics).

For this particular circuit the qubits are independent: every k-bit string has
probability `1 / 2**k`. Interpret the measured string as an unsigned binary integer.
For example, `10100011` means 128 + 32 + 2 + 1 = 163. With eight bits, the possible
integers are 0 through 255, inclusive. Every sample represents a fresh preparation.

Python's `getrandbits(k)` directly samples this known uniform distribution. We do
not construct a state vector or execute quantum hardware. This shortcut works
because these qubits are independent and the circuit is fixed; it cannot represent
arbitrary entangled circuits. This simulator does not provide physical quantum
randomness. Neither mode should be used as a cryptographic random-number source.

## Walk through the code

`validate(bits, count)` rejects invalid widths and counts before work begins.
The 64-bit limit bounds the size of each value and keeps the example manageable.
Booleans are rejected explicitly because they are also integer instances in Python.

`quantum_numbers` creates a local `random.Random` object and retains its
`getrandbits` method. It returns a generator expression: values are produced on
demand. Calling it does not allocate a list of all requested numbers. The seed
allows repeatable experiments in the same Python environment and algorithm;
it is not a quantum setting. The module's global random state is unchanged.

`summarize` consumes one value at a time. It keeps an integer sum, a count of one
bits, at most eight preview values, and at most sixteen histogram counts.
`value.bit_count()` efficiently counts the set bits without building a binary
string. Binary strings are formatted only for the small preview.

The bin index is `value >> max(0, bits - 4)`. For eight-bit numbers this divides
the range into sixteen groups of sixteen values: 0–15, 16–31, and so on. For one
through four bits, each integer has its own bin. All bins have equal width.

`Summary` is a small dataclass holding these statistics. `main` parses command-line
options, runs both sampling methods, and formats the results after sampling.

The baseline uses `randrange(2**bits)`. Both methods use Python's same PRNG family;
different seeds make the demonstration use different seeded streams, not different
physical randomness sources. A smoother histogram does not establish that one
generator is better. Each bar is scaled to the largest simulated bin; the numeric
percentages are fractions of all samples and are the right basis for comparison.

## Efficiency choices

| Choice | Why it helps |
|---|---|
| One `getrandbits(k)` call per number | Avoids a Python loop for each individual qubit |
| Direct distribution sampling | Avoids a `2**k`-amplitude quantum state vector |
| Lazy stream and bounded histogram | Memory does not scale as a list of N outcomes |
| `bit_count()` | Avoids string conversion when counting one bits |
| Cached random method | Avoids repeated method lookup in the loop |
| Print after aggregation | Keeps terminal I/O outside the measured sampling loop |

For N samples with k bounded by 64, the program takes O(N) time under the usual
practical integer-cost model and retains a constant number of aggregate values.
Strictly, arbitrary-size integer sums/counters need O(log N + k) bits as counts
grow. The program does not allocate an O(N) outcomes list or O(2**k) histogram.
Floating-point summary means may be rounded for large 64-bit values; sampled
integers remain exact. Python's PRNG also has fixed internal state and overhead.

## Measured results

On this Windows machine with Python 3.11.2, September 5, 2026, the median of five
runs with 100,000 eight-bit samples was:

| Sampling and aggregation | Median elapsed time |
|---|---:|
| `getrandbits` circuit model, seed 42 | 19.65 ms |
| `randrange` baseline, seed 43 | 45.78 ms |

This is a Python implementation comparison, not a quantum speedup. The timer
includes generator setup and aggregation and excludes terminal printing. Local
load, Python version, and machine hardware affect the numbers. These are small
development measurements, not a comprehensive benchmark.

To reproduce the timing procedure from the repository folder:

```python
import statistics
from quantum_random import summarize

print(statistics.median(summarize(8, 100000, 42).elapsed for _ in range(5)))
print(statistics.median(summarize(8, 100000, 43, True).elapsed for _ in range(5)))
```

Separate `tracemalloc` runs reported peak tracked Python allocations of 3,800 bytes
for 1,000 samples and 4,312 bytes for 100,000 samples in the circuit-model path.
These are allocations during the call, not total process memory. They are
consistent with bounded aggregates rather than retaining every result.

## Interpret and verify

For k bits, the expected mean is `(2**k - 1) / 2`; the expected fraction of one
bits is 50%. For eight bits and sixteen bins, each bin has expected frequency
6.25%. Finite runs fluctuate. A 100,000-sample run with seed 42 produced mean
127.4768 and a one-bit fraction of about 49.9976% on the tested environment.

Run `python -m unittest -v`. All eight tests passed. They check widths, exact
counts, repeatability, isolation of global random state, lazy consumption,
aggregation, both comparison modes, invalid input, and command-line behavior.
They do not prove randomness; there is no flaky requirement for exact balance.

Try `--bits 1`, `--bits 4`, and `--bits 16` to watch the grouping change. Increase
`--count` to compare statistical variation with elapsed time. Keep the same seed
for a repeatable experiment, or omit it for varying runs.
