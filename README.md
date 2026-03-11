# angie-setup

A utility for creating a customized, rootless [Angie](https://angie.software/en/) (Nginx fork) container image.
It performs a multi-stage build to compile Angie from source, enabling high-performance features like HTTP/3 (QUIC), TCP
Streaming, and native ACME support while removing unused legacy modules.

**Base Image:** [openSUSE Leap 16.0](https://registry.opensuse.org/cgi-bin/cooverview)  
**Angie Version:** 1.11.1 (Compiled from source)

## Pre-requisites

**OS:** Linux-based.

<table>
    <caption>Required Tools</caption>
    <thead>
        <tr>
            <th>Package</th>
            <th>Version</th>
            <th>Notes</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Python</td>
            <td>3.13+</td>
            <td>
                <p>Core language the CLI tool is written in.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://python-poetry.org/docs/">Poetry</a></td>
            <td>2.2.1+</td>
            <td>
                <p>Project dependency manager.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://buildah.io/">Buildah</a></td>
            <td>1.41.5+</td>
            <td>
                <p>Used to programmatically create OCI-compliant container images without a daemon.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://taskfile.dev/">Taskfile</a></td>
            <td>3.46.3+</td>
            <td>
                <p>Optional. You can use the provided <a href="taskw">shell script wrapper</a> (<code>./taskw</code>) which scopes the binary to the project.</p>
            </td>
        </tr>
    </tbody>
</table>

## Usage

List available tasks:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY --list
```

Setup python virtual environment and install dependencies:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY deps
```

View CLI tool options and build help:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- --help
```

### Example

Build angie core binary from source:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- containers core build
```

Build angie runtime:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- containers runtime build
```

Run built container using `podman`:

- Create `angie.conf` in script directory:
    ```
    #user  nobody;
    worker_processes  auto;
    daemon off;
    error_log /dev/stderr info;
    
    #error_log  logs/error.log;
    #error_log  logs/error.log  notice;
    #error_log  logs/error.log  info;
    
    #pid        logs/angie.pid;
    
    
    events {
        worker_connections  1024;
    }
    
    
    http {
        include       mime.types;
        default_type  application/octet-stream;
    
        access_log /dev/stdout;
        #log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
        #                  '$status $body_bytes_sent "$http_referer" '
        #                  '"$http_user_agent" "$http_x_forwarded_for"';
    
        #access_log  logs/access.log  main;
    
        sendfile        on;
        #tcp_nopush     on;
    
        #keepalive_timeout  0;
        keepalive_timeout  65;
    
        #gzip  on;
    
        server {
            listen       80;
            server_name  localhost;
    
            #access_log  logs/host.access.log  main;
    
            location / {
                root   html;
                index  index.html index.htm;
            }
    
            #error_page  404              /404.html;
    
            # redirect server error pages to the static page /50x.html
            #
            error_page   500 502 503 504  /50x.html;
            location = /50x.html {
                root   html;
            }
    
            # proxy the PHP scripts to Apache listening on 127.0.0.1:80
            #
            #location ~ \.php$ {
            #    proxy_pass   http://127.0.0.1;
            #}
    
            # pass the PHP scripts to FastCGI server listening on 127.0.0.1:9000
            #
            #location ~ \.php$ {
            #    root           html;
            #    fastcgi_pass   127.0.0.1:9000;
            #    fastcgi_index  index.php;
            #    fastcgi_param  SCRIPT_FILENAME  /scripts$fastcgi_script_name;
            #    include        fastcgi_params;
            #}
    
            # deny access to .htaccess files, if Apache's document root
            # concurs with Angie's one
            #
            #location ~ /\.ht {
            #    deny  all;
            #}
        }
    
    
        # another virtual host using mix of IP-, name-, and port-based configuration
        #
        #server {
        #    listen       8000;
        #    listen       somename:8080;
        #    server_name  somename  alias  another.alias;
    
        #    location / {
        #        root   html;
        #        index  index.html index.htm;
        #    }
        #}
    
    
        # HTTPS server
        #
        #server {
        #    listen       443 ssl;
        #    server_name  localhost;
    
        #    ssl_certificate      cert.pem;
        #    ssl_certificate_key  cert.key;
    
        #    ssl_session_cache    shared:SSL:1m;
        #    ssl_session_timeout  5m;
    
        #    ssl_ciphers  HIGH:!aNULL:!MD5;
        #    ssl_prefer_server_ciphers  on;
    
        #    location / {
        #        root   html;
        #        index  index.html index.htm;
        #    }
        #}
    
    }
    ```

- Run container:
  ```shell

  #!/bin/bash
  
  CONTAINER="angie1.11.1"
  NETWORK="tumbleweed"
  NETWORK_ALIAS="angie"
  CONTAINER_UID=1004
  CONTAINER_GID=1004
  
  # Standard Web Ports
  
  PORT_HTTP=8080
  PORT_HTTPS=8443
  
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  CONFIG_FILE=$SCRIPT_DIR/angie.conf # Custom configuration file
  
  VOLUME_LOGS="angie-logs"
  IMAGE="localhost/angie:1.11.1" # Matches your runtime build tag
  
  podman run -d \
  --sysctl net.ipv4.ip_unprivileged_port_start=80 \
  --name $CONTAINER \
  --network $NETWORK \
  --network-alias $NETWORK_ALIAS \
  --user $CONTAINER_UID:$CONTAINER_GID \
  -p $PORT_HTTP:80 \
  -p $PORT_HTTPS:443 \
  -p $PORT_PULSAR:6650 \
  -v $CONFIG_FILE:/usr/local/angie/conf/angie.conf:ro,Z \
  $IMAGE
  
  ```

## Application Container Image Features

### Image capabilities

This image is compiled with specific flags to support modern edge-proxy requirements while reducing attack surface.

<table> <thead> <th>Feature</th> <th>Enabled</th> <th>Description</th> </thead> <tbody> <tr> <td><strong>HTTP/3 (QUIC)</strong></td> <td>✅</td> <td>Native support for HTTP/3 over UDP (--with-http_v3_module) using OpenSSL QUIC APIs.</td> </tr> <tr> <td><strong>L4 Streaming</strong></td> <td>✅</td> <td>TCP/UDP proxying (--with-stream) enabled for handling databases (Postgres) and messaging (Pulsar).</td> </tr> <tr> <td><strong>ACME</strong></td> <td>✅</td> <td>Native Let's Encrypt integration (--with-http_acme_module) for automatic certificate management.</td> </tr> <tr> <td><strong>Observability</strong></td> <td>✅</td> <td>Stub Status module enabled (--with-http_stub_status_module) for Prometheus metrics scraping.</td> </tr> <tr> <td><strong>RealIP</strong></td> <td>✅</td> <td>Extracts client IP from X-Forwarded-For or PROXY protocol headers (--with-http_realip_module).</td> </tr> </tbody> </table>

### Ports

<table> <thead> <th>Port</th> <th>Protocol</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>80</code></td> <td>HTTP</td> <td>Standard web traffic (requires <code>--sysctl</code> to bind as non-root).</td> </tr> <tr> <td><code>443</code></td> <td>HTTPS/QUIC</td> <td>Secure web traffic.</td> </tr>  </tbody> </table>

### Volumes

<table> <thead> <th>Path</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>/usr/local/angie/conf/angie.conf</code></td> <td><strong>Configuration.</strong> Mount your custom config file here (Read-only recommended).</td> </tr> <tr> <td><code>/usr/local/angie/logs</code></td> <td><strong>Logs.</strong> Default directory for log files (if not logging to stdout/stderr).</td> </tr> </tbody> </table>


