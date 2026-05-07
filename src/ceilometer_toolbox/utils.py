from datetime import datetime
from datetime import time
from datetime import timedelta
from typing import NamedTuple

import pandas as pd
import xarray as xr
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap
from solpos import solpos
from solpos import SolposResult


def get_solpos(
        date: datetime,
        *,
        lat: float,
        lon: float,
        utcoffset: float | None = None,
        press: float = 1013.25,
        temp: float = 12,
) -> SolposResult:
    '''convenience function around :func:`solpos.solpos`, returning all results
    calculated by the SOLPOS 2.0 function.

    The most commonly (and in this project) used values are:

    - the azimuth angle :math:`\\theta_{a}`, ``SolposResult.azim``
    - the solar declination zenith angle :math:`\\delta` of the solar noon
      at the equator
    - the elevation angle :math:`\\theta_{el}`, ``SolposResult.elevetr`` ( no
      atmospheric correction) or ``SolposResult.elevref`` (refracted)
    - the zenith angle :math:`\\theta_{z}`, ``SolposResult.zenetr`` (no
      atmospheric correction) or ``SolposResult.zenref`` (refracted)
    - the extraterrestrial (top of the atmosphere) direct normal solar
      radiation :math:`I_{0}`, ``SolposResult.etrn``


    :param date: date for which the data should be calculated. If the date is
        timezone aware, ``utcoffset`` is not needed.
    :param lat: latitude of the position for which the data should be
        calculated
    :param lon: longitude of the position for which the data should be
        calculated
    :param utcoffset: utc-offset of the provided datetime in hours if the
        datetime object is not timezone aware
    :param press: atmospheric surface pressure (not reduced), default:
        1013.25 mbar.
    :param temp: temperature in celsius default: 12 °C

    :return: a :class:`solpos.SolposResult` object with all data calculated by
        SOLPOS 2.0
    '''
    if (
            (
                date.tzinfo is None or
                date.utcoffset() is None
            ) and
            utcoffset is None
    ):
        raise ValueError(
            f'date: {date} has no timezone, please make it timezone aware or '
            f"specify a value to the argument 'utcoffset' containing the "
            f'timezone offset',
        )
    elif utcoffset is None:
        offset_delta = date.utcoffset()
        # we checked above that date is timezone aware
        assert offset_delta is not None
        utcoffset = offset_delta.total_seconds() / 60 / 60
    else:
        pass

    solpos_data = solpos(
        *date.timetuple()[:6],
        timezone=utcoffset,
        latitude=lat,
        longitude=lon,
        press=press,
        temp=temp,
    )
    return solpos_data


class SolarTimes(NamedTuple):
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime


def _get_relevant_times(d: datetime, lat: float, lon: float) -> SolarTimes:
    """Get the sunrise, sunset, and solar noon times for a given date."""
    res = get_solpos(d, lat=lat, lon=lon, utcoffset=0)
    day_start = datetime.combine(d.date(), time.min)
    return SolarTimes(
        sunrise=day_start + timedelta(minutes=res.sretr),
        sunset=day_start + timedelta(minutes=res.ssetr),
        solar_noon=(
            datetime.combine(d, datetime.min.time()) +
            timedelta(hours=12, minutes=res.tstfix)
        ),
    )


def resample_dataset(ds: xr.Dataset, delta: timedelta) -> xr.Dataset:
    """Resample the dataset to a lower temporal resolution based on the
    total time of the plot.

    This is necessary to make the plotting faster and avoid exhausting the
    memory when plotting long time periods. The resampling is done by taking
    the nearest value to the resampled time points. The resampling is only done
    on the time.

    :param ds: The dataset to resample. This should have a time coordinate.
    :param delta: The total time of the plot. This is used to determine the
        resampling frequency. The larger the delta, the lower the temporal
        resolution of the plot, and thus the faster the plotting. The
        resampling frequencies are chosen to limit the number of time points
        to ~10k, which is a reasonable number for plotting without exhausting
        the memory or making or the plotting too slow. The resampling
        frequencies are as follows:
        - If delta < 1 day: resample to 90s
        - If delta < 2 days: resample to 2min
        - If delta < 4 days: resample to 3min
        - If delta < 7 days: resample to 5min
        - If delta < 14 days: resample to 10min
        - If delta < 21 days: resample to 15min
        - If delta < 30 days: resample to 30min
    """
    # we want to make sure that we limit the data for plotting ot ~10k time
    # points otherwise the plotting becomes very slow. The lowest smallest we
    # expect to plot is 24h and a max of 30 days.
    if delta < timedelta(days=1, minutes=1):
        return ds.resample(time='90s').nearest()
    if delta < timedelta(days=2, minutes=1):
        return ds.resample(time='2min').nearest()
    if delta < timedelta(days=4, minutes=1):
        return ds.resample(time='3min').nearest()
    if delta < timedelta(days=7, minutes=1):
        return ds.resample(time='5min').nearest()
    if delta < timedelta(days=14, minutes=1):
        return ds.resample(time='10min').nearest()
    if delta < timedelta(days=21, minutes=1):
        return ds.resample(time='15min').nearest()
    if delta < timedelta(days=30, minutes=1):
        return ds.resample(time='30min').nearest()
    else:
        raise ValueError(
            f'delta: {delta} is too large for resampling, please limit the '
            f'time range of the plot to a maximum of 30 days',
        )


def add_solar_times(
        ax: Axes,
        ds: xr.Dataset,
        lat: float,
        lon: float,
) -> None:
    """Add vertical lines for sunrise and sunset to the plot.
    :param ax: The axes to add the vertical lines to.
    :param ds: The dataset to get the time range from. This should have a time
        coordinate.
    """
    dates = pd.date_range(
        start=pd.to_datetime(ds.time.min().values).date(),
        end=pd.to_datetime(ds.time.max().values).date(),
        freq='1D',
        tz='UTC',
    )
    # compute solar times using the provided or discovered coordinates
    solar_times = [
        _get_relevant_times(d.to_pydatetime(), lat=lat, lon=lon) for d in dates
    ]
    # add vertical lines for sunrise
    for i, solar_time in enumerate(solar_times):
        ax.axvline(
            solar_time.sunrise,
            color='black',
            lw=1.25,
            linestyle='dotted',
            label='Sunrise' if i == 0 else '',
        )
        ax.axvline(
            solar_time.sunset,
            color='black',
            lw=1,
            linestyle='dashed',
            label='Sunset' if i == 0 else '',
        )
    ax.legend(loc='upper right')


LDR_CMAP = LinearSegmentedColormap.from_list(
    name='ldr_cmap',
    colors=[
        '#ffffff',
        '#ccd2ff', '#ccd2ff', '#ccd2ff', '#ccd2ff', '#bfc7ff',
        '#bfc7ff', '#bfc7ff', '#bfc7ff', '#808fff', '#808fff',
        '#808fff', '#808fff', '#899fff', '#899fff', '#899fff',
        '#899fff', '#4058ff', '#4058ff', '#4058ff', '#4058ff',
        '#0020ff', '#0020ff', '#0020ff', '#0020ff', '#0040ff',
        '#0040ff', '#0040ff', '#0040ff', '#0080ff', '#0080ff',
        '#0080ff', '#0080ff', '#009fff', '#009fff', '#009fff',
        '#009fff', '#009fff', '#00bfff', '#00bfff', '#00bfff',
        '#00bfff', '#00dfff', '#00dfff', '#00dfff', '#00efff',
        '#00ffff', '#00ffff', '#00ffff', '#00ffff', '#20ffdf',
        '#20ffdf', '#20ffdf', '#20ffdf', '#40ffbf', '#40ffbf',
        '#40ffbf', '#40ffbf', '#80ff80', '#80ff80', '#80ff80',
        '#80ff80', '#80ff80', '#80ff80', '#80ff80', '#80ff80',
        '#8fff70', '#8fff70', '#8fff70', '#8fff70', '#8fff70',
        '#9fff60', '#9fff60', '#9fff60', '#9fff60', '#afff50',
        '#afff50', '#afff50', '#afff50', '#bfff40', '#bfff40',
        '#bfff40', '#bfff40', '#cfff30', '#cfff30', '#cfff30',
        '#cfff30', '#efff10', '#efff10', '#efff10', '#efff10',
        '#ffff00', '#ffff00', '#ffff00', '#ffff00', '#ffef00',
        '#ffef00', '#ffef00', '#ffef00', '#ffdf00', '#ffdf00',
        '#ffdf00', '#ffdf00', '#ffd700', '#ffcf00', '#ffcf00',
        '#ffcf00', '#ffcf00', '#ffbf00', '#ffbf00', '#ffbf00',
        '#ffbf00', '#ffaf00', '#ffaf00', '#ffaf00', '#ffaf00',
        '#ff8f00', '#ff8f00', '#ff8f00', '#ff8f00', '#ff8000',
        '#ff8000', '#ff8000', '#ff8000', '#ff7000', '#ff7000',
        '#ff7000', '#ff7000', '#ff6000', '#ff6000', '#ff6000',
        '#ff6000', '#ff5000', '#ff5000', '#ff5000', '#ff5000',
        '#ff5000', '#ff4000', '#ff4000', '#ff4000', '#ff4000',
        '#ff3000', '#ff3000', '#ff3000', '#ff3000', '#ff1000',
        '#ff1000', '#ff1000', '#ff1000', '#ff0000', '#ff0000',
        '#ff0000', '#ff0000', '#ef0000', '#ef0000', '#ef0000',
        '#ef0000', '#df0000', '#df0000', '#df0000', '#df0000',
        '#cf0000', '#cf0000', '#cf0000', '#cf0000', '#bf0000',
        '#bf0000', '#bf0000', '#bf0000', '#bf0000', '#af0000',
        '#af0000', '#af0000', '#af0000', '#8f0000', '#8f0000',
        '#8f0000', '#8f0000', '#800000', '#800000', '#800000',
        '#800000', '#700000', '#700000', '#700000', '#700000',
        '#600000', '#600000', '#600000', '#600000', '#600000',
        '#600000', '#600000', '#600000', '#600000', '#600000',
        '#600000', '#600000', '#600000', '#600000', '#600000',
        '#600000', '#600000',
    ],
    N=256,
)
