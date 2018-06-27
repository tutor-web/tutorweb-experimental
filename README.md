# Prerequisites
First, configure your system to include the Yarn repository: https://yarnpkg.com/lang/en/docs/install/

...then the nodejs repository:

```
curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
echo "deb https://deb.nodesource.com/node_6.x xenial main" > /etc/apt/sources.list.d/nodesource.list
apt-get update
```

Server-side dependencies:

```
apt install \
    python3 python3-venv python3-dev \
    libreadline-dev \
    r-base-core r-base-dev \
    postgresql
```

Client-side dependencies:

```
apt install \
    make nodejs nodejs-legacy yarn nginx
```

## Debugging

### Fake SMTP server for activation e-mails

You can start a fake SMTP server to receive e-mails with:

    sudo make fakesmtp
