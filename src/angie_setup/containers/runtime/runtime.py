from pathlib import Path
from typing import Optional

import typer

from .builder import RuntimeBuilder
from angie_setup.core import BuildSpec, load_spec

app = typer.Typer(help="An angie runtime.")

@app.command("build", help="Build an angie runtime.")
def build(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        image_name: Optional[str] = typer.Option("angie", "--image-name", "--n",
                                                 help="Name of new angie runtime image."),
        image_tag: Optional[str] = typer.Option("", "--image-tag", "--t",
                                                help="Optional. Tag of new angie runtime image"),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers.")
):
    """
    Build Angie runtime image.

    :param cache_prefix:
    :param spec_file:
    :param image_name:
    :param image_tag:
    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = RuntimeBuilder(config, cache_prefix, image_name, image_tag)

    builder.build()


@app.command("delete-cache", help="Delete cache images used to build angie runtime image.")
def delete_cache(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers.")
):
    """
    Delete cache images used to build Angie runtime.

    :param spec_file: Path to build spec file.
    :param cache_prefix: Custom prefix for cache layers generated.

    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = RuntimeBuilder(config, cache_prefix)

    builder.prune_cache_images()
