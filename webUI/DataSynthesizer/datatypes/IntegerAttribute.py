from DataSynthesizer.datatypes.AbstractAttribute import AbstractAttribute
from DataSynthesizer.datatypes.utils.DataType import DataType


class IntegerAttribute(AbstractAttribute):
    def __init__(self, name, is_candidate_key=False, is_categorical=False, histogram_size=20):
        super().__init__(name, is_candidate_key, is_categorical, histogram_size)
        self.is_numerical = True
        self.data_type = DataType.INTEGER

    def infer_domain(self, column):
        super().infer_domain(column)
        self.min = int(self.min)
        self.max = int(self.max)

    def generate_values_as_candidate_key(self, n):
        return super().generate_values_as_candidate_key(n)

    def sample_values_from_binning_indices(self, binning_indices):
        column = super().sample_values_from_binning_indices(binning_indices)
        column[~column.isnull()] = column[~column.isnull()].astype(int)
        return column
