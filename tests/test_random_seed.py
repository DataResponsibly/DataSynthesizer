from pathlib import Path

from DataSynthesizer.DataDescriber import DataDescriber


def describe(seed=None):
    describer = DataDescriber()
    describer.describe_dataset_in_independent_attribute_mode(
        Path(__file__).parent / 'data' / 'adult_tiny.csv', epsilon=1.0, seed=seed)
    return describer.data_description


def test_default_runs_use_fresh_noise():
    # two default runs must not produce identical noisy distributions
    assert describe() != describe()


def test_explicit_seed_is_reproducible():
    assert describe(seed=42) == describe(seed=42)
