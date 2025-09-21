from ray.data import DataContext


def configure_ray_for_repro():
    ctx = DataContext.get_current()
    ctx.execution_options.preserve_order = True
