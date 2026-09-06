# Quantum random-number simulator

Project 2: generate bit strings from an ideal quantum measurement model, convert
them to integers, and compare their distribution with Python's `randrange`.
Python **3.10+**, standard library only; no installation of packages is needed.

## Run

Download this repository, open a terminal in its folder, and run:

```sh
python quantum_random.py --bits 8 --count 100000 --seed 42
```

On Windows, `py` can replace `python`. Omit `--seed` for varying runs. Use `--help`
for options. Supported widths are 1 through 64 bits; counts must be positive.

The output includes eight example integers and bit strings, a mean, the fraction
of one bits, timings, and side-by-side frequency percentages. At most 16 histogram
bins are stored, even for 64-bit numbers.

```python
from quantum_random import quantum_numbers

for number in quantum_numbers(bits=8, count=5, seed=42):
    print(number)
```

This is a **classical simulation**, not a physical quantum random-number source.
Both comparison modes use Python's pseudorandom generator. The quantum content is
the circuit model and its measurement probabilities.

## Documentation and checks

- [GUIDE.md](GUIDE.md): quantum model, code walkthrough, optimization, and measured results.
- [quantum_random.py](quantum_random.py): commented source with function docstrings.
- [test_quantum_random.py](test_quantum_random.py): eight behavioral tests.

```sh
python -m unittest -v
```

All 8 tests passed on Python 3.11.2, Windows, on September 5, 2026. The 100,000-sample
demo also ran successfully. No test requires perfectly uniform random counts.
