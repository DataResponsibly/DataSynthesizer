# History

## 0.1.0 - 2020-06-11

* First release on PyPI.

## 0.1.1 - 2020-07-05

### Bugs Fixed

* Numpy error when synthesising data with unique identifiers. - [Issue #23](https://github.com/DataResponsibly/DataSynthesizer/issues/23) by @raids

## 0.1.2 - 2020-07-19

### Bugs Fixed

* infer_distribution() for string attributes fails to sort index of varying types. - [Issue #24](https://github.com/DataResponsibly/DataSynthesizer/issues/24) by @raids

## 0.1.3 - 2020-09-13

### Bugs Fixed

* The dataframes are not appended into the full space in get_noisy_distribution_of_attributes(). - [Issue #26](https://github.com/DataResponsibly/DataSynthesizer/issues/26) by @zjroth

## 0.1.4 - 2021-01-14

### Bugs Fixed

* Fix a bug in candidate key identification.

## 0.1.5 - 2021-03-11

### What's New

* Downgrade required Python from >=3.8 to >=3.7.

## 0.1.6 - 2021-03-11

### What's New

* Update example notebooks.

## 0.1.7 - 2021-03-31

### Bugs Fixed

* Fixed an error in Laplace noise parameter. - [Issue #34](https://github.com/DataResponsibly/DataSynthesizer/issues/34) by @ganevgv

## 0.1.8 - 2021-04-09

### Bugs Fixed

* The randomness seeding is effective across the entire project now.

## 0.1.9 - 2021-07-18

### Bugs Fixed

* Optimized the datetime datatype detection.

## 0.1.10 - 2021-11-15

### Bugs Fixed

* Seed the randomness in `greedy_bayes()`.

## 0.1.11 - 2022-03-31

### Bugs Fixed

* Fixed a bug in DateTime generation. - [Issue #37](https://github.com/DataResponsibly/DataSynthesizer/issues/37) by @artemgur

## 0.1.12 - 2023-10-17

### Bugs Fixed

* Support Python 3.11+ and pandas 2.0+. - [Issue #40](https://github.com/DataResponsibly/DataSynthesizer/issues/41) by @artemgur
* Added empty file creation before saving files. - [Issue #41](https://github.com/DataResponsibly/DataSynthesizer/issues/41) by @PepijndeReus

## 0.1.13 - 2023-10-18

### Bugs Fixed

* Support pandas 2.0+.