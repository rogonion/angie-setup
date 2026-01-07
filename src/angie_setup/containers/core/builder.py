from angie_setup.core import BaseBuilder, BuildahContainer, prune_cache_images, BuildSpec


class CoreBuilder(BaseBuilder):
    def __init__(self, config: BuildSpec, cache_prefix: str = ""):
        super().__init__(config, cache_prefix)
        self.image_name = f"{self.config.ProjectName}-core"
        self.image_tag = self.config.Angie.Version

    def _init_cache_prefix(self, cache_prefix: str):
        if len(cache_prefix) > 0:
            self.cache_prefix = cache_prefix
        else:
            self.cache_prefix = f"{self.config.ProjectName}/cache/core/{self.config.Angie.Version}"

    def build(self):
        self.log(f"Starting build for Angie {self.config.Angie.Version} core", style="bold blue")

        current_step = 1
        total_no_of_steps = 6

        with BuildahContainer(
                base_image=self.config.BaseImage,
                image_name=self.image_name,
                config=self.config,
                cache_prefix=self.cache_prefix
        ) as container:
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Installing build dependencies")

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"""
                        zypper --non-interactive refresh &&
                        zypper --non-interactive install """ + " ".join(self.config.Angie.Build.Dependencies)],
                extra_cache_keys={"step": "deps", "packages": sorted(self.config.Angie.Build.Dependencies)}
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Preparing directory {self.config.Angie.Prefix}")

            container.run(["mkdir", "-p", self.config.Angie.Prefix])

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Downloading and Extracting from {self.config.Angie.SourceUrl}")

            tar_path = f"/tmp/angie-{self.config.Angie.Version}.tar.gz"
            src_dir = f"/tmp/angie-{self.config.Angie.Version}"

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"""
                            curl -L '{self.config.Angie.SourceUrl}' -o {tar_path} && 
                            tar -xzf {tar_path} -C /tmp &&
                            rm {tar_path}
                            """
                ],
                extra_cache_keys={
                    "step": "download_extract",
                    "url": self.config.Angie.SourceUrl,
                    "prefix": self.config.Angie.Prefix
                }
            )

            current_step += 1
            self.log(f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Configuring compilation")

            configure_args = ["./configure",
                              f"--prefix={self.config.Angie.Prefix}"] + self.config.Angie.Build.Flags

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"cd {src_dir} && {' '.join(configure_args)}"
                ],
                extra_cache_keys={"step": "configure", "flags": sorted(self.config.Angie.Build.Flags)}
            )

            current_step += 1
            self.log(f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Compiling and installing")

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"cd {src_dir} && make -j$(nproc) && make install",
                ],
                extra_cache_keys={"step": "compile", "version": self.config.Angie.Version}
            )
            container.run(["sh", "-c", f"find {self.config.Angie.Prefix}/sbin -type f -exec strip --strip-all {{}} +"])

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Verifying installation and committing.")

            try:
                angie_bin = f"{self.config.Angie.Prefix}/sbin/angie"
                container.run(["test", "-x", angie_bin])
                container.run([angie_bin, "-v"])

                self.log(f"Verification successful: Found {angie_bin}", style="bold green")
            except Exception:
                self.log("[bold red]Verification Failed[/bold red]: Pulsar binary missing in extraction path.")
                raise

            container.configure([
                ("--label", f"org.angie.version={self.config.Angie.Version}"),
                ("--label", f"org.angie.prefix={self.config.Angie.Prefix}"),
            ])

            image_name_tag = self.image_name + ":" + self.image_tag
            container.commit(image_name_tag)

            self.log(f"Image tagged as: [green]{image_name_tag}[/green]")

    def prune_cache_images(self):
        prune_cache_images(self.config.Buildah.Path, self.cache_prefix)