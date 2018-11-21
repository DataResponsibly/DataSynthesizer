from typing import Union

import numpy as np
from dateutil.parser import parse
from pandas import Series

from datatypes.AbstractAttribute import AbstractAttribute
from datatypes.utils.DataType import DataType
from lib.utils import normalize_given_distribution


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
            self.min = float(self.data_dropna.min())
            self.max = float(self.data_dropna.max())
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
            bins = distribution[1][:-1]
            bins[0] = bins[0] - 0.001 * (bins[1] - bins[0])
            self.distribution_bins = bins

    def generate_values_as_candidate_key(self, n):
        return np.arange(self.min, self.max, (self.min - self.max) / n)

    def sample_values_from_binning_indices(self, binning_indices):
        column = super().sample_values_from_binning_indices(binning_indices)
        column[~column.isnull()] = column[~column.isnull()].astype(int)
        return column
