# ceilometer-toolbox

This is a unified collection of state-of-the-art tools for processing ceilometer data.
This makes use of the following tools:

1. [raw2l1](https://github.com/ACTRIS-CCRES/raw2l1)
2. [stratfinder](https://gitlab.in2p3.fr/ipsl/sirta/mld/stratfinder/stratfinder)
   (Kotthaus et al. 2020)
3. [stratfinder-qc](https://gitlab.in2p3.fr/ipsl/sirta/mld/stratfinder/qc-sf-python)

It builds a file tree to easily store and access data from multiple sensors, hiding
multi-file and multi-folder complexity and making it easily accessible from python.

## installation

via https

```bash
pip install git+https://github.com/RUBclim/ceilometer-toolbox
```

via ssh

```bash
pip install git+ssh://git@github.com/RUBclim/ceilometer-toolbox
```

## Getting started

1. Locate the root folder where all ceilometer data is stored in. It is important that
   the date matches this format: `{prefix}{file_date:%Y%m%d}_*.nc`. If a custom way of
   deriving raw data between two dates is needed, the `Ceilometer.glob_day_raw_data`
   methods needs to be overridden after inheriting from `Ceilometer`.

   ```
   ├── ceilometer-data
   │   ├── live_20260217_150920.nc
   │   ├── live_20260217_151420.nc
   │   ├── live_20260217_151920.nc
   ...
   ```

1. Create a `CeilometerArchive` instance and point it at a folder where you want to
   store the data.

   ```python
   from ceilometer_toolbox import CeilometerArchive

   archive = CeilometerArchive('ceilometer-output')
   ```

1. Create a `Ceilometer` instance and pass the previously created `archive` to it.

   ```python
   from ceilometer_toolbox import Ceilometer

   ceilometer = Ceilometer(
       device_id='IA',
       input_dir='ceilometer-input',
       archive=archive,
       raw2l1_config_file='example_configs/raw2l1_cl61.conf',
       stratfinder_config_file='example_configs/stratfinder_settings_cl61.json',
       stratfinder_qc_value_config_file='example_configs/values_qc.toml',
       stratfinder_qc_metadata_file='example_configs/STRATFINDER_metadata.toml',
   )
   ```

1. You may provide all config files for the respective tools when creating the instance,
   they will be used for processing in the respective steps, may, however, also be
   overwritten. Please see the respective tool for a full documentation on the
   configuration.

1. Now start processing the raw data to L1:

   ```python
   ceilometer.process_raw_files(start_date='2026-05-06', end_date='2026-05-07', jobs=1)
   ```

   This will run `raw2l1`, reading from the `input_dir` specified. `jobs` can control
   concurrency which will spawn multiple processes running raw2l1 in parallel. Note that
   this is an IO-heavy tasks. Excessively high concurrency may lead to slower
   performance. Especially when the target or source is a mounted network drive.

1. Now run `stratfinder` on the L1 data. This cannot be run in parallel, since it
   depends on files from the previous day, which may not be ready.

   ```python
   ceilometer.process_l1_files(start_date='2026-05-06')

   ```

   For this step you will have to have `docker` installed and the `stratfinder` image
   built. Please see [STRATfinder-docker](https://github.com/RUBclim/STRATfinder-docker)
   for instruction

1. Finally run the quality control on the `stratfinder` output

   ```python
   ceilometer.process_stratfinder_qc(start_date='2026-05-06')
   ```

1. Now a file tree should be present (`device_id` &rarr; `year` &rarr; `month` &rarr;
   `day/file type`):

   ```
   ├── ceilometer-output
   │   └── IA
   │       └── 2026
   │           └── 05
   │               ├── 20260503_L1.nc
   │               ├── 20260503_L2A_beta.nc
   │               ├── 20260503_L2A_stratfinder.nc
   │               └── 20260503_L2B_stratfinder.nc

   ```

## Accessing data

The data is stored in a tree-like structure so filesystem performance remains high and
access to ranges of data is fast. The `CeilometerArchive` instance allows interaction
with the file tree, fully hiding its complexity.

Any range of data can be accessed with a context manager like this:

```python
with archive.open_dataset(
    device_id='IA',
    file_type='L2A_stratfinder',
    start_date=datetime(2026, 5, 1),
    end_date=datetime(2026, 5, 3),
) as ds:
    ...
```

This will find and read all files needed to cover the range. This uses `dask` and this
way avoids reading all files into memory at once, hence, long time periods can be loaded
without the need for a lot of RAM.

## Plotting data

The toolbox also comes with simple plotting functions for plotting $\beta$ and the
linear depolarization ratio (CL61).

```python
ceilometer.beta_plot(
    start_date=datetime(2026, 4, 28),
    end_date=datetime(2026, 5, 2),
    show_mlh=True,
    show_ablh=True,
    show_cbh=True,
    alt_max=2500,
    output_path='beta_plot.png',
)
```

![](beta_plot.png)

This automatically applies resampling (nearest) to allow plotting longer time series
This can, however, be changes by passing a different function via `resampler=` e.g.
using averages instead which are computationally much more expensive. The QC-Flags are
automatically taken into account and excluded, unless you set `filter_qc=False`.

The maximum altitude can be set via `alt_max`. The linear depolarization plot has a
similar interface, however, omitting the MLH, ABLH and CBH options.

```
ceilometer.ldr_plot(
    start_date=datetime(2026, 4, 28),
    end_date=datetime(2026, 5, 2),
    alt_max=2500,
    output_path='ldr_plot.png',
)
```

![](ldr_plot.png)

## References

Kotthaus, S., Haeffelin, M., Drouin, M.-A., Dupont, J.-C., Grimmond, S., Haefele, A.,
Hervo, M., Poltera, Y., & Wiegner, M. (2020). Tailored Algorithms for the Detection of
the Atmospheric Boundary Layer Height from Common Automatic Lidars and Ceilometers
(ALC). Remote Sensing, 12(19), 3259. https://doi.org/10.3390/rs12193259
