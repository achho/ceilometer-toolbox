from matplotlib.colors import LinearSegmentedColormap


def _make_ldr_cmap() -> LinearSegmentedColormap:
    colors = [
        '#ffffff',
        '#ccd2ff', '#ccd2ff', '#ccd2ff', '#ccd2ff', '#bfc7ff',
        '#bfc7ff', '#bfc7ff', '#bfc7ff', '#808fff', '#808fff',
        '#808fff', '#808fff', '#899fff', '#899fff', '#899fff',
        '#899fff', '#4058ff', '#4058ff', '#4058ff', '#4058ff',
        '#0020ff', '#0020ff', '#0020ff', '#0020ff', '#0040ff',
        '#0040ff', '#0040ff', '#0040ff', '#0080ff', '#0080ff',
        '#0080ff', '#0080ff', '#009fff', '#009fff', '#009fff',
        '#009fff', '#009fff', '#00bfff', '#00bfff', '#00bfff',
        '#00bfff', '#00dfff', '#00dfff', '#00dfff', '#0060ff',
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
    ]
    # Non-uniform mapping so the gradient matches the reference colorbar:
    #   idx  57 (#40ffbf, end of cyan)  -> position 0.24/0.7 (data value 0.24)
    #   idx 149 (#ff0000, start of red) -> position 0.47/0.7 (data value 0.47)
    _anchors = [(0, 0.0), (57, 0.24 / 0.7), (149, 0.47 / 0.7), (202, 1.0)]

    def _pos(i: int) -> float:
        for j in range(len(_anchors) - 1):
            i0, p0 = _anchors[j]
            i1, p1 = _anchors[j + 1]
            if i <= i1:
                return p0 + (i - i0) / (i1 - i0) * (p1 - p0)
        return 1.0  # pragma: no cover

    return LinearSegmentedColormap.from_list(
        name='ldr_cmap',
        colors=[(_pos(i), c) for i, c in enumerate(colors)],
        N=256,
    )


LDR_CMAP = _make_ldr_cmap()
