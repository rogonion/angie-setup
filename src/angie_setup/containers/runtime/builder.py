from pathlib import Path
from angie_setup.core import BaseBuilder, BuildSpec, prune_cache_images, BuildahContainer


class RuntimeBuilder(BaseBuilder):
    def __init__(self, config: BuildSpec, cache_prefix: str = "", image_name: str = "", image_tag: str = ""):
        super().__init__(config, cache_prefix)
        self.image_name = image_name if image_name else f"{self.config.ProjectName}-runtime"
        self.image_tag = image_tag if image_tag else self.config.Angie.Version

    def _init_cache_prefix(self, cache_prefix: str):
        self.cache_prefix = cache_prefix if cache_prefix else f"{self.config.ProjectName}/cache/runtime/{self.config.Angie.Version}"

    def build(self):
        self.log(f"Starting build for Angie {self.config.Angie.Version} runtime", style="bold blue")

        current_step = 1

        with BuildahContainer(
                base_image=self.config.BaseImage,
                image_name=self.image_name,
                config=self.config,
                cache_prefix=self.cache_prefix
        ) as container:
            self.log(f"[bold blue]Step {current_step}[/bold blue]: Retrieving angie artifacts")
            container.copy_container_current(
                f"{self.config.ProjectName}-core:{self.config.Angie.Version}",
                self.config.Angie.Prefix,
                self.config.Angie.Prefix
            )

            current_step += 1
            self.log(f"[bold blue]Step {current_step}[/bold blue]: Installing angie runtime dependencies")
            container.run_cached(
                command=[
                    "sh", "-c",
                    f"zypper --non-interactive refresh && "
                    f"zypper --non-interactive install " + " ".join(self.config.Angie.Runtime.Dependencies)
                ],
                extra_cache_keys={"step": "deps", "packages": sorted(self.config.Angie.Runtime.Dependencies)}
            )
            container.run(command=["zypper", "clean", "--all"])

            current_step += 1
            self.log(f"[bold blue]Step {current_step}[/bold blue]: Setting up system user")

            container.run(command=["groupadd", "-r", "-g", str(self.config.Angie.Runtime.Gid), "angie"])
            container.run(
                command=["useradd", "-r", "-u", str(self.config.Angie.Runtime.Uid),
                         "-g", str(self.config.Angie.Runtime.Gid),
                         "-d", self.config.Angie.Prefix,
                         "-s", "/sbin/nologin",
                         "-c", '"Angie Server"', "angie"]
            )

            container.configure([
                ("--label", f"io.angie.user.uid={self.config.Angie.Runtime.Uid}"),
                ("--label", f"io.angie.user.gid={self.config.Angie.Runtime.Gid}"),
                ("--label", f"io.angie.user.name=angie"),
            ])

            current_step += 1
            self.log(f"[bold blue]Step {current_step}[/bold blue]: Setting up directories & permissions")

            container.configure([
                ("--env",
                 f"PATH={self.config.Angie.Prefix}/sbin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
                ("--env", f"ANGIE_HOME={self.config.Angie.Prefix}"),
                ("--env", "LANG=C.UTF-8"),
                ("--env", "LC_ALL=C.UTF-8")
            ])

            # Ensure logs and html directories exist and have permissions
            for d in ["logs", "html", "conf", "client_body_temp", "proxy_temp", "fastcgi_temp", "uwsgi_temp",
                      "scgi_temp"]:
                full_d_dir = f"{self.config.Angie.Prefix}/{d}"
                container.run(["mkdir", "-p", full_d_dir])

            # Only persist logs by default
            container.configure([
                ("--volume", f"{self.config.Angie.Prefix}/logs")
            ])

            container.run(
                command=["chown", "-R",
                         f"{self.config.Angie.Runtime.Uid}:{self.config.Angie.Runtime.Gid}",
                         self.config.Angie.Prefix]
            )

            container.copy_host_container(Path(f"{self.config.Angie.Runtime.Resources}/entrypoint.sh"),
                                          "/usr/local/bin/entrypoint.sh")
            container.run(command=["chmod", "+x", "/usr/local/bin/entrypoint.sh"])

            container.configure([
                ("--entrypoint", '["/usr/local/bin/entrypoint.sh"]'),
                ("--cmd", '["angie"]'),
                ("--user", str(self.config.Angie.Runtime.Uid)),
                ("--port", "80"),
                ("--port", "443")
            ])

            # --- Step 6: Finalize ---
            current_step += 1
            self.log(f"[bold blue]Step {current_step}[/bold blue]: Tagging image.")

            container.configure([
                ("--label", f"org.angie.version={self.config.Angie.Version}"),
                ("--label", f"org.angie.prefix={self.config.Angie.Prefix}"),
            ])
            image_name_tag = self.image_name + ":" + self.image_tag
            container.commit(image_name_tag)

            self.log(f"Image tagged as: [green]{image_name_tag}[/green]")

    def prune_cache_images(self):
        prune_cache_images(self.config.Buildah.Path, self.cache_prefix)
