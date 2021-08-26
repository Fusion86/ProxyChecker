# ProxyChecker

Basic proxy checker.

## Usage

```sh
# Install requirements
pip install -r requirements.txt

# Create some proxylist.txt
echo 192.168.2.200:8118 > proxylist.txt

# Call proxychecker.py
python proxychecker.py proxylist.txt

# See --help for more
python proxychecker.py --help
# Usage: proxychecker.py [OPTIONS] PROXYLIST

#   Test proxies inside a proxy list.

# Options:
#   --url TEXT         url to test  [default: https://ip.cerbus.nl]
#   --timeout INTEGER  timeout in milliseconds  [default: 2000]
#   --export TEXT      export working proxies to this file
#   --help             Show this message and exit.
```
