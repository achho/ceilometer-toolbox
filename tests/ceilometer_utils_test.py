"""Tests for ceilometer_toolbox.utils and ceilometer_toolbox.colors."""
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest
import xarray as xr
from ceilometer_toolbox.colors import LDR_CMAP
from ceilometer_toolbox.utils import add_solar_times
from ceilometer_toolbox.utils import get_solpos
from ceilometer_toolbox.utils import resample_dataset
from ceilometer_toolbox.utils import SolarTimes


# ---------------------------------------------------------------------------
# colors
# ---------------------------------------------------------------------------

def test_ldr_cmap_is_importable_and_has_correct_name():
    assert LDR_CMAP.name == 'ldr_cmap'


def test_ldr_cmap_maps_zero_to_white():
    rgba = LDR_CMAP(0.0)
    assert rgba == (1.0, 1.0, 1.0, 1.0)


# ---------------------------------------------------------------------------
# get_solpos
# ---------------------------------------------------------------------------

def test_get_solpos_raises_when_no_timezone_and_no_utcoffset():
    naive = datetime(2026, 3, 25, 12, 0, 0)
    with pytest.raises(ValueError, match='please make it timezone aware'):
        get_solpos(naive, lat=51.45, lon=7.26)


def test_get_solpos_with_utcoffset_kwarg():
    naive = datetime(2026, 3, 25, 12, 0, 0)
    result = get_solpos(naive, lat=51.45, lon=7.26, utcoffset=0)
    assert hasattr(result, 'azim')


def test_get_solpos_with_timezone_aware_datetime():
    aware = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc)
    result = get_solpos(aware, lat=51.45, lon=7.26)
    assert hasattr(result, 'azim')


# ---------------------------------------------------------------------------
# resample_dataset  (every branch)
# ---------------------------------------------------------------------------

def _make_ds(n: int = 10) -> xr.Dataset:
    times = np.array(
        [
            np.datetime64('2026-03-25T00:00:00') +
            np.timedelta64(i * 5, 'm') for i in range(n)
        ],
    )
    return xr.Dataset(
        {'beta': (['time', 'altitude'], np.ones((n, 3)))},
        coords={'time': times, 'altitude': [100.0, 200.0, 300.0]},
    )


def test_resample_dataset_less_than_1_day():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(hours=12))
    assert result is not None


def test_resample_dataset_less_than_2_days():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(days=1, hours=1))
    assert result is not None


def test_resample_dataset_less_than_4_days():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(days=2, hours=1))
    assert result is not None


def test_resample_dataset_less_than_7_days():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(days=4, hours=1))
    assert result is not None


def test_resample_dataset_less_than_14_days():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(days=7, hours=1))
    assert result is not None


def test_resample_dataset_less_than_21_days():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(days=14, hours=1))
    assert result is not None


def test_resample_dataset_less_than_30_days():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(days=21, hours=1))
    assert result is not None


def test_resample_dataset_30_days():
    ds = _make_ds()
    result = resample_dataset(ds, timedelta(days=30))
    assert result is not None


def test_resample_dataset_over_30_days_raises():
    ds = _make_ds()
    with pytest.raises(ValueError, match='too large for resampling'):
        resample_dataset(ds, timedelta(days=31))


# ---------------------------------------------------------------------------
# add_solar_times
# ---------------------------------------------------------------------------

def _make_time_ds() -> xr.Dataset:
    times = np.array([
        np.datetime64('2026-03-25T06:00:00'),
        np.datetime64('2026-03-25T18:00:00'),
    ])
    return xr.Dataset(coords={'time': times})


_FAKE_SOLAR = SolarTimes(
    sunrise=datetime(2026, 3, 25, 6, 0),
    sunset=datetime(2026, 3, 25, 18, 0),
    solar_noon=datetime(2026, 3, 25, 12, 0),
)


def test_add_solar_times_adds_one_pair_per_day():
    # Single day → one sunrise line + one sunset line
    ds = _make_time_ds()
    ax = MagicMock()
    with patch(
        'ceilometer_toolbox.utils._get_relevant_times',
        return_value=_FAKE_SOLAR,
    ):
        add_solar_times(ax, ds, lat=51.45, lon=7.26)
    assert ax.axvline.call_count == 2


def test_add_solar_times_multi_day_labels_only_first():
    # Two days → four axvline calls; only the first pair gets non-empty labels
    times = np.array([
        np.datetime64('2026-03-25T06:00:00'),
        np.datetime64('2026-03-26T18:00:00'),
    ])
    ds = xr.Dataset(coords={'time': times})
    ax = MagicMock()
    with patch(
        'ceilometer_toolbox.utils._get_relevant_times',
        return_value=_FAKE_SOLAR,
    ):
        add_solar_times(ax, ds, lat=51.45, lon=7.26)
    assert ax.axvline.call_count == 4
    calls = ax.axvline.call_args_list
    assert calls[0].kwargs['label'] == 'Sunrise'
    assert calls[1].kwargs['label'] == 'Sunset'
    assert calls[2].kwargs['label'] == ''
    assert calls[3].kwargs['label'] == ''
