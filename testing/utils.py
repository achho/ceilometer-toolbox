import io
import os

import numpy as np
from matplotlib.figure import Figure
from PIL import Image
from PIL import ImageChops


def assert_plot_is_equal(
        fig: Figure,
        baseline: str,
        diff_th: float = 0.0,
) -> None:
    with io.BytesIO() as current_img_bytes:
        fig.savefig(
            current_img_bytes,
            format='jpeg',
            bbox_inches='tight',
            dpi=120,
        )
        with (
                Image.open(baseline) as baseline_img,
                Image.open(current_img_bytes) as current_img,
        ):
            baseline_array = np.array(baseline_img)
            current_array = np.array(current_img)

    diff = baseline_array - current_array
    diff_sum = np.abs(diff).sum()
    diff_sum_normed = diff_sum / baseline_array.size
    # this is only executed when a test fails
    if diff_sum_normed > diff_th:  # pragma: no cover
        diff = ImageChops.difference(baseline_img, current_img)
        diff_binary = np.array(diff)
        diff_binary[diff_binary > 0] = 255
        yellow = Image.new('RGB', diff.size, ('yellow'))
        yellow_diff = ImageChops.multiply(yellow, Image.fromarray(diff_binary))
        result = ImageChops.blend(yellow_diff, current_img, 0.2)

        # save to a folder to have a look at the diff
        os.makedirs('.pytest-img-comp', exist_ok=True)
        name, _ = os.path.splitext(os.path.basename(baseline))
        baseline_img.save(
            os.path.join('.pytest-img-comp', f'{name}_baseline.jpeg'),
        )
        current_img.save(
            os.path.join('.pytest-img-comp', f'{name}_current_img.jpeg'),
        )
        diff_path = os.path.join('.pytest-img-comp', f'{name}_diff_img.jpeg')
        result.save(diff_path)
        raise AssertionError(
            f'{diff_sum_normed} > {diff_th}: images differ (see: {diff_path})',
        )
