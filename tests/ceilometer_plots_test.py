import os
from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta
from unittest import mock

import numpy as np
import pytest
import xarray as xr
from ceilometer_toolbox.data import CeilometerArchive
from ceilometer_toolbox.device import Ceilometer

from testing.utils import assert_plot_is_equal

_HERE = os.path.dirname(__file__)
_ROOT = os.path.join(_HERE, '..')
TESTING_OUTPUT = os.path.abspath(os.path.join(_ROOT, 'testing', 'output'))
PLOT_BASELINE = os.path.abspath(
    os.path.join(_ROOT, 'testing', 'plot_baseline'),
)


@pytest.fixture
def ceilometer():
    archive = CeilometerArchive(TESTING_OUTPUT)
    return Ceilometer(
        device_id='IA',
        input_dir='/dev/null',
        archive=archive,
    )


# ---------------------------------------------------------------------------
# beta_plot
# ---------------------------------------------------------------------------

def test_beta_plot_1d(tmp_path, ceilometer):
    fig = ceilometer.beta_plot(
        start_date=datetime(2026, 3, 25, 23, 0),
        end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
        output_path=str(tmp_path / 'L1_beta_1d.jpg'),
    )
    assert_plot_is_equal(
        fig,
        baseline=os.path.join(PLOT_BASELINE, 'L1_beta_1d.jpg'),
    )


def test_beta_plot_1d_alt_max(tmp_path, ceilometer):
    fig = ceilometer.beta_plot(
        start_date=datetime(2026, 3, 25, 23, 0),
        end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
        output_path=str(tmp_path / 'L1_beta_1d_alt_max.jpg'),
        alt_max=4500,
    )
    assert_plot_is_equal(
        fig,
        baseline=os.path.join(PLOT_BASELINE, 'L1_beta_1d_alt_max.jpg'),
    )


def test_beta_plot_30d(tmp_path, ceilometer):
    fig = ceilometer.beta_plot(
        start_date=datetime(2026, 3, 25, 23, 0),
        end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=30),
        output_path=str(tmp_path / 'L1_beta_30d.jpg'),
    )
    assert_plot_is_equal(
        fig,
        baseline=os.path.join(PLOT_BASELINE, 'L1_beta_30d.jpg'),
    )


def test_beta_plot_show_ablh(tmp_path, ceilometer):
    strat_ds = xr.Dataset(
        data_vars={
            'ABLH': (['time'], np.array([500.0, 600.0])),
            'MLH': (['time'], np.array([400.0, 500.0])),
            'quality_FLAG': (['time'], np.array([0, 0])),
            'precip_FLAG': (['time'], np.array([0, 0])),
        },
        coords={
            'time': [
                np.datetime64('2026-03-25T23:30:00'),
                np.datetime64('2026-03-26T00:30:00'),
            ],
        },
    )

    with mock.patch.object(
        ceilometer.archive,
        'open_dataset',
        side_effect=[
            ceilometer.archive.open_dataset(
                'IA', 'L1',
                start_date=datetime(2026, 3, 25, 23, 0),
                end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
                engine='netcdf4',
                data_vars='minimal',
                compat='override',
                coords='minimal',
            ),
            _fake_ctx(strat_ds),
        ],
    ):
        fig = ceilometer.beta_plot(
            start_date=datetime(2026, 3, 25, 23, 0),
            end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
            output_path=str(tmp_path / 'beta_ablh.jpg'),
            show_ablh=True,
        )
    assert fig is not None


def test_beta_plot_show_mlh_and_cbh(tmp_path, ceilometer):
    strat_ds = xr.Dataset(
        data_vars={
            'MLH': (['time'], np.array([400.0, 500.0])),
            'cloud_base_altitude': (
                ['time', 'altitude'],
                np.array([[1000.0, np.nan], [1100.0, np.nan]]),
            ),
            'quality_FLAG': (['time'], np.array([0, 0])),
            'precip_FLAG': (['time'], np.array([0, 0])),
        },
        coords={
            'time': [
                np.datetime64('2026-03-25T23:30:00'),
                np.datetime64('2026-03-26T00:30:00'),
            ],
            'altitude': [1000.0, 2000.0],
        },
    )

    with mock.patch.object(
        ceilometer.archive,
        'open_dataset',
        side_effect=[
            ceilometer.archive.open_dataset(
                'IA', 'L1',
                start_date=datetime(2026, 3, 25, 23, 0),
                end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
                engine='netcdf4',
                data_vars='minimal',
                compat='override',
                coords='minimal',
            ),
            _fake_ctx(strat_ds),
        ],
    ):
        fig = ceilometer.beta_plot(
            start_date=datetime(2026, 3, 25, 23, 0),
            end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
            output_path=str(tmp_path / 'beta_mlh_cbh.jpg'),
            show_mlh=True,
            show_cbh=True,
        )
    assert fig is not None


def test_beta_plot_filter_qc_false(tmp_path, ceilometer):
    strat_ds = xr.Dataset(
        data_vars={
            'ABLH': (['time'], np.array([500.0])),
            'quality_FLAG': (['time'], np.array([1])),
            'precip_FLAG': (['time'], np.array([0])),
        },
        coords={
            'time': [np.datetime64('2026-03-26T00:00:00')],
        },
    )

    with mock.patch.object(
        ceilometer.archive,
        'open_dataset',
        side_effect=[
            ceilometer.archive.open_dataset(
                'IA', 'L1',
                start_date=datetime(2026, 3, 25, 23, 0),
                end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
                engine='netcdf4',
                data_vars='minimal',
                compat='override',
                coords='minimal',
            ),
            _fake_ctx(strat_ds),
        ],
    ):
        fig = ceilometer.beta_plot(
            start_date=datetime(2026, 3, 25, 23, 0),
            end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
            output_path=str(tmp_path / 'beta_no_qc.jpg'),
            show_ablh=True,
            filter_qc=False,
        )
    assert fig is not None


# ---------------------------------------------------------------------------
# ldr_plot
# ---------------------------------------------------------------------------

def test_ldr_plot_1d(tmp_path, ceilometer):
    fig = ceilometer.ldr_plot(
        start_date=datetime(2026, 3, 25, 23, 0),
        end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
        output_path=str(tmp_path / 'L1_ldr_1d.jpg'),
    )
    assert_plot_is_equal(
        fig,
        baseline=os.path.join(PLOT_BASELINE, 'L1_ldr_1d.jpg'),
    )


def test_ldr_plot_1d_alt_max(tmp_path, ceilometer):
    fig = ceilometer.ldr_plot(
        start_date=datetime(2026, 3, 25, 23, 0),
        end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=1),
        output_path=str(tmp_path / 'L1_ldr_1d_alt_max.jpg'),
        alt_max=4500,
    )
    assert_plot_is_equal(
        fig,
        baseline=os.path.join(PLOT_BASELINE, 'L1_ldr_1d_alt_max.jpg'),
    )


def test_ldr_plot_30d(tmp_path, ceilometer):
    fig = ceilometer.ldr_plot(
        start_date=datetime(2026, 3, 25, 23, 0),
        end_date=datetime(2026, 3, 25, 23, 0) + timedelta(days=30),
        output_path=str(tmp_path / 'L1_ldr_30d.jpg'),
    )
    assert_plot_is_equal(
        fig,
        baseline=os.path.join(PLOT_BASELINE, 'L1_ldr_30d.jpg'),
    )


# ---------------------------------------------------------------------------
# Helper: fake context manager wrapping a dataset
# ---------------------------------------------------------------------------


@contextmanager
def _fake_ctx(ds):
    yield ds
