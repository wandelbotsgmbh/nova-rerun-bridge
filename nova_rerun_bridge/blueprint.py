import rerun as rr
import rerun.blueprint as rrb

from nova_rerun_bridge import colors
from nova_rerun_bridge.consts import TIME_INTERVAL_NAME


def configure_joint_line_colors():
    """
    Log the visualization lines for joint limit boundaries.
    """

    for i in range(1, 7):
        prefix = "motion/joint"
        color = colors.colors[i - 1]

        rr.log(
            f"{prefix}_velocity_lower_limit_{i}",
            rr.SeriesLine(color=[176, 49, 40], name=f"joint_velocity_lower_limit_{i}", width=4),
            timeless=True,
        )
        rr.log(
            f"{prefix}_velocity_upper_limit_{i}",
            rr.SeriesLine(color=[176, 49, 40], name=f"joint_velocity_upper_limit_{i}", width=4),
            timeless=True,
        )

        rr.log(
            f"{prefix}_acceleration_lower_limit_{i}",
            rr.SeriesLine(color=[176, 49, 40], name=f"joint_acceleration_lower_limit_{i}", width=4),
            timeless=True,
        )
        rr.log(
            f"{prefix}_acceleration_upper_limit_{i}",
            rr.SeriesLine(color=[176, 49, 40], name=f"joint_acceleration_upper_limit_{i}", width=4),
            timeless=True,
        )

        rr.log(
            f"{prefix}_position_lower_limit_{i}",
            rr.SeriesLine(color=[176, 49, 40], name=f"joint_position_lower_limit_{i}", width=4),
            timeless=True,
        )
        rr.log(
            f"{prefix}_position_upper_limit_{i}",
            rr.SeriesLine(color=[176, 49, 40], name=f"joint_position_upper_limit_{i}", width=4),
            timeless=True,
        )

        rr.log(
            f"{prefix}_torque_limit_{i}",
            rr.SeriesLine(color=[176, 49, 40], name=f"joint_torques_lower_limit_{i}", width=4),
            timeless=True,
        )

    for i in range(1, 7):
        prefix = "motion/joint"
        color = colors.colors[i - 1]

        rr.log(
            f"{prefix}_velocity_{i}",
            rr.SeriesLine(color=color, name=f"joint_velocity_{i}", width=2),
            timeless=True,
        )
        rr.log(
            f"{prefix}_velocity_{i}",
            rr.SeriesLine(color=color, name=f"joint_velocity_{i}", width=2),
            timeless=True,
        )

        rr.log(
            f"{prefix}_acceleration_{i}",
            rr.SeriesLine(color=color, name=f"joint_acceleration_{i}", width=2),
            timeless=True,
        )
        rr.log(
            f"{prefix}_acceleration_{i}",
            rr.SeriesLine(color=color, name=f"joint_acceleration_{i}", width=2),
            timeless=True,
        )

        rr.log(
            f"{prefix}_position_{i}",
            rr.SeriesLine(color=color, name=f"joint_position_{i}", width=2),
            timeless=True,
        )
        rr.log(
            f"{prefix}_position_{i}",
            rr.SeriesLine(color=color, name=f"joint_position_{i}", width=2),
            timeless=True,
        )

        rr.log(
            f"{prefix}_torque_{i}",
            rr.SeriesLine(color=color, name=f"joint_torques_{i}", width=2),
            timeless=True,
        )


def configure_tcp_line_colors():
    """
    Configure time series lines for motion data.
    """
    series_specs = [
        ("tcp_velocity", [136, 58, 255], 2),
        ("tcp_acceleration", [136, 58, 255], 2),
        ("tcp_orientation_velocity", [136, 58, 255], 2),
        ("tcp_orientation_acceleration", [136, 58, 255], 2),
        ("time", [136, 58, 255], 2),
        ("location_on_trajectory", [136, 58, 255], 2),
        ("tcp_acceleration_lower_limit", [176, 49, 40], 4),
        ("tcp_acceleration_upper_limit", [176, 49, 40], 4),
        ("tcp_orientation_acceleration_lower_limit", [176, 49, 40], 4),
        ("tcp_orientation_acceleration_upper_limit", [176, 49, 40], 4),
        ("tcp_velocity_limit", [176, 49, 40], 4),
        ("tcp_orientation_velocity_limit", [176, 49, 40], 4),
    ]
    for name, color, width in series_specs:
        rr.log(f"motion/{name}", rr.SeriesLine(color=color, name=name, width=width), timeless=True)


def joint_content_lists():
    """
    Generate content lists for joint-related time series.
    """
    velocity_contents = [f"motion/joint_velocity_{i}" for i in range(1, 7)]
    velocity_limits = [f"motion/joint_velocity_lower_limit_{i}" for i in range(1, 7)] + [
        f"motion/joint_velocity_upper_limit_{i}" for i in range(1, 7)
    ]

    accel_contents = [f"motion/joint_acceleration_{i}" for i in range(1, 7)]
    accel_limits = [f"motion/joint_acceleration_lower_limit_{i}" for i in range(1, 7)] + [
        f"motion/joint_acceleration_upper_limit_{i}" for i in range(1, 7)
    ]

    pos_contents = [f"motion/joint_position_{i}" for i in range(1, 7)]
    pos_limits = [f"motion/joint_position_lower_limit_{i}" for i in range(1, 7)] + [
        f"motion/joint_position_upper_limit_{i}" for i in range(1, 7)
    ]

    torque_contents = [f"motion/joint_torque_{i}" for i in range(1, 7)]
    torque_limits = [f"motion/joint_torque_limit_{i}" for i in range(1, 7)]

    return (
        velocity_contents,
        velocity_limits,
        accel_contents,
        accel_limits,
        pos_contents,
        pos_limits,
        torque_contents,
        torque_limits,
    )


def get_default_blueprint(motion_group_list: list):
    """
    get logging blueprints for visualization.
    """

    # Contents for the Spatial3DView
    contents = ["motion/**", "collision_scenes/**"] + [f"{group}/**" for group in motion_group_list]

    time_ranges = rrb.VisibleTimeRange(
        TIME_INTERVAL_NAME,
        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-2),
        end=rrb.TimeRangeBoundary.cursor_relative(seconds=2),
    )
    plot_legend = rrb.PlotLegend(visible=False)

    (
        velocity_contents,
        velocity_limits,
        accel_contents,
        accel_limits,
        pos_contents,
        pos_limits,
        torque_contents,
        torque_limits,
    ) = joint_content_lists()

    return rrb.Blueprint(
        rrb.Horizontal(
            rrb.Spatial3DView(contents=contents, name="3D Nova", background=[20, 22, 35]),
            rrb.Tabs(
                rrb.Vertical(
                    rrb.TimeSeriesView(
                        contents=["motion/tcp_velocity/**", "motion/tcp_velocity_limit/**"],
                        name="TCP velocity",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=[
                            "motion/tcp_acceleration/**",
                            "motion/tcp_acceleration_lower_limit/**",
                            "motion/tcp_acceleration_upper_limit/**",
                        ],
                        name="TCP acceleration",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=[
                            "motion/tcp_orientation_velocity/**",
                            "motion/tcp_orientation_velocity_limit/**",
                        ],
                        name="TCP orientation velocity",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=[
                            "motion/tcp_orientation_acceleration/**",
                            "motion/tcp_orientation_acceleration_lower_limit/**",
                            "motion/tcp_orientation_acceleration_upper_limit/**",
                        ],
                        name="TCP orientation acceleration",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TextLogView(origin="/logs", name="Logs"),
                    name="Trajectory quantities",
                    row_shares=[1, 1, 1, 1, 0.5],
                ),
                rrb.Vertical(
                    rrb.TimeSeriesView(
                        contents=velocity_contents + velocity_limits,
                        name="Joint velocity",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=accel_contents + accel_limits,
                        name="Joint acceleration",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=pos_contents + pos_limits,
                        name="Joint position",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    rrb.TimeSeriesView(
                        contents=torque_contents + torque_limits,
                        name="Joint torque",
                        time_ranges=time_ranges,
                        plot_legend=plot_legend,
                    ),
                    name="Joint quantities",
                ),
                rrb.TimeSeriesView(
                    contents="motion/time",
                    name="Time trajectory",
                    time_ranges=time_ranges,
                    plot_legend=plot_legend,
                ),
                rrb.TimeSeriesView(
                    contents="motion/location_on_trajectory",
                    name="Location on trajectory",
                    time_ranges=time_ranges,
                    plot_legend=plot_legend,
                ),
            ),
            column_shares=[1, 0.3],
        ),
        collapse_panels=True,
    )


def send_blueprint(motion_group_list: list):
    """
    Configure logging blueprints for visualization.
    """

    configure_tcp_line_colors()
    configure_joint_line_colors()

    rr.send_blueprint(get_default_blueprint(motion_group_list))
