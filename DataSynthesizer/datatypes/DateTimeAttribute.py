import numpy as np
from dateutil.parser import parse
from pandas import Series

from DataSynthesizer.datatypes.AbstractAttribute import AbstractAttribute
from DataSynthesizer.datatypes.utils.DataType import DataType
from DataSynthesizer.lib.utils import normalize_given_distribution


def is_datetime(date_string):
    """Find whether a value is of type datetime.

    Here it regards weekdays and months as categorical strings instead of converting them into timestamps.
    """
    weekdays = [("Mon", "Monday"),
                ("Tue", "Tuesday"),
                ("Wed", "Wednesday"),
                ("Thu", "Thursday"),
                ("Fri", "Friday"),
                ("Sat", "Saturday"),
                ("Sun", "Sunday")]
    months = [("Jan", "January"),
              ("Feb", "February"),
              ("Mar", "March"),
              ("Apr", "April"),
              ("May", "May"),
              ("Jun", "June"),
              ("Jul", "July"),
              ("Aug", "August"),
              ("Sep", "Sept", "September"),
              ("Oct", "October"),
              ("Nov", "November"),
              ("Dec", "December")]
    for entry in weekdays + months:
        for value in entry:
            if date_string.lower() == value.lower():
                return False
    try:
        parse(date_string)
        return True
    except ValueError:
        return False


class DateTimeAttribute(AbstractAttribute):
    def __init__(self, name, is_candidate_key=False, is_categorical=False, histogram_size=20):
        super().__init__(name, is_candidate_key, is_categorical, histogram_size)
        self.is_numerical = True
        self.data_type = DataType.DATETIME

    def infer_domain(self, column):
        assert isinstance(column, Series)
        self.data = column
        self.data_dropna = self.data.dropna()
        self.missing_rate = (self.data.size - self.data_dropna.size) / self.data.size
        epoch_datetime = parse('1970-01-01')
        timestamps = self.data_dropna.map(lambda x: int((parse(x)-epoch_datetime).total_seconds()))
        self.min = float(timestamps.min())
        self.max = float(timestamps.max())

        if self.is_categorical:
            distribution = self.data_dropna.value_counts()
            distribution.sort_index(inplace=True)
            self.distribution_probabilities = normalize_given_distribution(distribution).tolist()
            self.distribution_bins = np.array(distribution.index).tolist()
        else:
            distribution = np.histogram(timestamps, bins=self.histogram_size)
            self.distribution_probabilities = normalize_given_distribution(distribution[0]).tolist()
            bins = distribution[1][:-1].tolist()
            bins[0] = bins[0] - 0.001 * (bins[1] - bins[0])
            self.distribution_bins = bins

    def generate_values_as_candidate_key(self, n):
        return np.arange(self.min, self.max, (self.min - self.max) / n)

    def sample_values_from_binning_indices(self, binning_indices):
        column = super().sample_values_from_binning_indices(binning_indices)
        column[~column.isnull()] = column[~column.isnull()].astype(int)
        return column