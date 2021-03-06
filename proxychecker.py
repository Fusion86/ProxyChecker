import time
import click
import requests
import colorama
import concurrent.futures
from typing import Optional
from colorama import Fore, Style
from requests.exceptions import ProxyError


class Proxy:
    def __init__(
        self, url: str, port: str, username: Optional[str], password: Optional[str]
    ):
        self.url = url
        self.port = port
        self.username = username
        self.password = password


# Thread safe print, yes this works.
def safe_print(line):
    print(line + "\n", end="")


def test_proxy(proxy: Proxy, test_url: str, timeout_ms: int) -> bool:
    try:
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.username}:{proxy.password}@{proxy.url}:{proxy.port}"
        else:
            proxy_url = f"{proxy.url}:{proxy.port}"

        http_proxy = "http://" + proxy_url
        https_proxy = "http://" + proxy_url

        # Shitty way to get the server response time, but it's decent enough I suppose.
        start = time.perf_counter()
        r = requests.get(
            test_url,
            proxies={"http": http_proxy, "https": https_proxy},
            timeout=timeout_ms / 1000.0,
        )
        request_time = time.perf_counter() - start
    except ProxyError as ex:
        safe_print(f"{Fore.RED}PROXY ERROR{Style.RESET_ALL} - {proxy_url}")
    except IOError as ex:
        safe_print(f"{Fore.RED}UNKNOWN ERROR{Style.RESET_ALL} - {proxy_url}")
    else:
        if "ip.cerbus.nl" in test_url:
            status_str = f" ({r.text.strip()})"
        else:
            status_str = ""

        safe_print(
            f"{Fore.GREEN}WORKING {round(request_time*1000, 2)}ms{status_str}{Style.RESET_ALL} - {proxy_url}"
        )
        return True
    return False


# I guess we could use file arguments -> https://click.palletsprojects.com/en/8.0.x/arguments/#file-arguments
# But thats more work, and this works well enough.
@click.command()
@click.argument("proxylist")
@click.option(
    "--url", help="url to test", default="https://ip.cerbus.nl", show_default=True
)
@click.option(
    "--timeout",
    help="timeout in milliseconds",
    default=2000,
    type=int,
    show_default=True,
)
@click.option(
    "--workers",
    help="how many workers to use",
    default=20,
    type=int,
    show_default=True,
)
@click.option("--export", help="export working proxies to this file", type=str)
def cli(proxylist: str, url: str, timeout: int, workers: int, export: Optional[str]):
    """Test proxies inside a proxy list."""

    proxies = []
    working_proxies = []

    with open(proxylist, "r") as f:
        # Read initial line
        line = f.readline().strip()

        while line:
            parts = line.split(":")

            if len(parts) == 2:
                proxy = Proxy(parts[0], parts[1], None, None)
                proxies.append(proxy)
            elif len(parts) == 4:
                proxy = Proxy(parts[0], parts[1], parts[2], parts[3])
                proxies.append(proxy)
            else:
                print(f"Ignoring line '{line}'")

            # Read next line
            line = f.readline().strip()

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(test_proxy, proxy, url, timeout) for proxy in proxies
        ]

        # See https://stackoverflow.com/a/63495323/2125072
        done, not_done = concurrent.futures.wait(futures, timeout=0)
        try:
            while not_done:
                # next line 'sleeps' this main thread, letting the thread pool run
                freshly_done, not_done = concurrent.futures.wait(not_done, timeout=1)
                done |= freshly_done
        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}Stopping...{Style.RESET_ALL}")
            for future in not_done:
                _ = future.cancel()
            _ = concurrent.futures.wait(not_done, timeout=None)

        for i, proxy in enumerate(proxies):
            # If test_proxy returned True
            try:
                if futures[i].result():
                    working_proxies.append(proxy)
            except:
                # Probably cancelled or something, idc
                pass

    if export != None and export != "":
        with open(export, "w") as f:
            for proxy in working_proxies:
                if proxy.username and proxy.password:
                    line = f"{proxy.url}:{proxy.port}:{proxy.username}:{proxy.password}"
                else:
                    line = f"{proxy.url}:{proxy.port}"
                f.write(line + "\n")


if __name__ == "__main__":
    colorama.init

    try:
        cli()
    except SystemExit:
        pass
