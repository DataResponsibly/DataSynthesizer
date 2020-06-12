from bisect import bisect_right
from typing import Union

import numpy as np
from dateutil.parser import parse
from pandas import Series, concat

from DataSynthesizer.datatypes.AbstractAttribute import AbstractAttribute
from DataSynthesizer.datatypes.utils.DataType import DataType
from DataSynthesizer.lib.utils import normalize_given_distribution


def is_datetime(value: str):
    """Find whether a value is a datetime. Here weekdays and months are categorical values instead of datetime."""
    weekdays = {'mon', 'monday', 'tue', 'tuesday', 'wed', 'wednesday', 'thu', 'thursday', 'fri', 'friday',
                'sat', 'saturday', 'sun', 'sunday'}
    months = {'jan', 'january', 'feb', 'february', 'mar', 'march', 'apr', 'april', 'may', 'may', 'jun', 'june',
              'jul', 'july', 'aug', 'august', 'sep', 'sept', 'september', 'oct', 'october', 'nov', 'november',
              'dec', 'december'}

    value_lower = value.lower()
    if (value_lower in weekdays) or (value_lower in months):
        return False
    try:
        parse(value)
        return True
    except ValueError:
        return False


# TODO detect datetime formats
class DateTimeAttribute(AbstractAttribute):
    def __init__(self, name: str, is_candidate_key, is_categorical, histogram_size: Union[int, str], data: Series):
        super().__init__(name, is_candidate_key, is_categorical, histogram_size, data)
        self.is_numerical = True
        self.data_type = DataType.DATETIME
        epoch_datetime = parse('1970-01-01')
        self.timestamps = self.data_dropna.map(lambda x: int((parse(x) - epoch_datetime).total_seconds()))

    def infer_domain(self, categorical_domain=None, numerical_range=None):
        if numerical_range:
            self.min, self.max = numerical_range
            self.distribution_bins = np.array([self.min, self.max])
        else:
            self.min = float(self.timestamps.min())
            self.max = float(self.timestamps.max())
            if self.is_categorical:
                self.distribution_bins = self.data_dropna.unique()
            else:
                self.distribution_bins = np.array([self.min, self.max])

        self.distribution_probabilities = np.full_like(self.distribution_bins, 1 / self.distribution_bins.size)

    def infer_distribution(self):
        if self.is_categorical:
            distribution = self.data_dropna.value_counts()
            for value in set(self.distribution_bins) - set(distribution.index):
                distribution[value] = 0
            distribution.sort_index(inplace=True)
            self.distribution_probabilities = normalize_given_distribution(distribution)
            self.distribution_bins = np.array(distribution.index)
        else:
            distribution = np.histogram(self.timestamps, bins=self.histogram_size, range=(self.min, self.max))
            self.distribution_probabilities = normalize_given_distribution(distribution[0])

    def encode_values_into_bin_idx(self):
        """Encode values into bin indices for Bayesian Network construction.

        """
        if self.is_categorical:
            value_to_bin_idx = {value: idx for idx, value in enumerate(self.distribution_bins)}
            encoded = self.data.map(lambda x: value_to_bin_idx[x], na_action='ignore')
        else:
            encoded = self.timestamps.map(lambda x: bisect_right(self.distribution_bins, x) - 1, na_action='ignore')
            encoded = concat([encoded, self.data], axis=1).iloc[:, 0]

        encoded.fillna(len(self.distribution_bins), inplace=True)
        return encoded.astype(int, copy=False)

    def generate_values_as_candidate_key(self, n):
        return np.arange(self.min, self.max, (self.min - self.max) / n)

    def sample_values_from_binning_indices(self, binning_indices):
        column = super().sample_values_from_binning_indices(binning_indices)
        column[~column.isnull()] = column[~column.isnull()].astype(int)
        return column
