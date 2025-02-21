from aiohttp import ClientResponseError, ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from eth_account import Account
from eth_account.messages import encode_defunct
from fake_useragent import FakeUserAgent
from datetime import datetime, timezone
import asyncio
import json
import random
import os
import pytz
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm.asyncio import tqdm_asyncio
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text

# Setup rich console
console = Console()

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)
logger = logging.getLogger("MultipleLite")

# Configure timezone
wib = pytz.timezone('Asia/Jakarta')

class MultipleLite:
    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.use_proxy = False
        self.stats = {
            "success": 0,
            "failed": 0,
            "total": 0
        }
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.progress = None

    def show_banner(self):
        """Display fancy banner when script runs."""
        banner_text = Text()
        banner_text.append("🚀 MultipleLite - Auto Login Bot\n", style="bold yellow")
        banner_text.append("    Automate your login process faster!\n", style="cyan")
        banner_text.append("  Developed by: https://t.me/sentineldiscus", style="blue")
        
        console.print(Panel(
            banner_text,
            border_style="yellow",
            expand=False,
            padding=(1, 2)
        ))

    def log(self, message, level="info", style=None):
        """Enhanced logging with rich styling"""
        timestamp = datetime.now().astimezone(wib).strftime('%x %X %Z')
        
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "success":
            # Success doesn't exist in logger, so we use console directly
            console.print(f"[{timestamp}] ✅ {message}", style=style or "green")
        else:
            logger.info(message)

    def print_proxy_options(self):
        """Display proxy selection options with rich formatting"""
        console.print("\n[bold cyan]Pilih metode proxy:[/]")
        
        options_table = Table(show_header=False, box=None)
        options_table.add_column("Option", style="yellow")
        options_table.add_column("Description")
        
        options_table.add_row("1", "Gunakan Proxy Gratis")
        options_table.add_row("2", "Gunakan Proxy Pribadi")
        options_table.add_row("3", "Jalankan Tanpa Proxy")
        
        console.print(options_table)
        
        while True:
            try:
                choice = int(console.input("[yellow]Pilih [1/2/3] -> [/]").strip())
                if choice in [1, 2, 3]:
                    return choice
                else:
                    console.print("[red]Masukkan angka 1, 2, atau 3.[/]")
            except ValueError:
                console.print("[red]Input tidak valid, masukkan angka 1, 2, atau 3.[/]")

    async def load_proxies(self, choice):
        """Load proxy list based on user choice with progress indicator"""
        if choice == 3:
            self.use_proxy = False
            return  # No proxy needed

        self.use_proxy = True
        filename = "proxy.txt" if choice == 2 else "proxyshare.txt"

        try:
            with console.status("[bold green]Loading proxies...", spinner="dots"):
                if choice == 1:
                    url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"
                    async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                        async with session.get(url) as response:
                            response.raise_for_status()
                            content = await response.text()
                            self.proxies = content.splitlines()
                            with open(filename, "w") as f:
                                f.write(content)
                else:
                    if os.path.exists(filename):
                        with open(filename, "r") as f:
                            self.proxies = [line.strip() for line in f if line.strip()]
                    else:
                        self.log(f"File {filename} tidak ditemukan!", level="error")

            self.log(f"Loaded {len(self.proxies)} proxies.", level="success")

        except Exception as e:
            self.log(f"Gagal memuat proxy: {e}", level="error")

    def get_next_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def generate_address(self, private_key):
        try:
            return Account.from_key(private_key).address
        except Exception as e:
            self.log(f"Address generation error: {str(e)}", level="error")
            return None

    def generate_message(self, address):
        timestamp = datetime.now(timezone.utc)
        nonce = int(timestamp.timestamp() * 1000)
        return f"www.multiple.cc wants you to sign in with your Ethereum account: {address}\nNonce: {nonce}"

    def generate_signature(self, private_key, message):
        try:
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=private_key)
            return signed_message.signature.hex()
        except Exception as e:
            self.log(f"Signature generation error: {str(e)}", level="error")
            return None

    async def user_login(self, address, message, signature, proxy=None):
        url = "https://api.app.multiple.cc/WalletLogin"
        data = json.dumps({"walletAddr": address, "message": message, "signature": signature})
        headers = {**self.headers, "Content-Type": "application/json"}

        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                async with session.post(url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result.get("data", {}).get("token")
        except Exception as e:
            self.log(f"Login gagal untuk {address}: {e}", level="error")
            return None

    async def process_account(self, private_key, task_id=None):
        result = {
            "address": "Invalid",
            "status": "Failed",
            "reason": "Unknown error",
            "timestamp": datetime.now().astimezone(wib).strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        
        proxy = self.get_next_proxy() if self.use_proxy else None
        address = self.generate_address(private_key)

        if task_id and self.progress:
            self.progress.update(task_id, description=f"Processing {address[:8]}...")

        if not address:
            result["reason"] = "Invalid private key"
            self.stats["failed"] += 1
            if task_id and self.progress:
                self.progress.update(task_id, description=f"[red]Failed[/] {address[:8]}")
            return result

        result["address"] = address
        message = self.generate_message(address)
        signature = self.generate_signature(private_key, message)

        if not signature:
            result["reason"] = "Failed to generate signature"
            self.stats["failed"] += 1
            if task_id and self.progress:
                self.progress.update(task_id, description=f"[red]Failed[/] {address[:8]}")
            return result

        token = await self.user_login(address, message, signature, proxy)
        if token:
            result["status"] = "Success"
            result["reason"] = "Login successful"
            self.stats["success"] += 1
            if task_id and self.progress:
                self.progress.update(task_id, description=f"[green]Success[/] {address[:8]}")
        else:
            result["reason"] = "Login failed"
            self.stats["failed"] += 1
            if task_id and self.progress:
                self.progress.update(task_id, description=f"[red]Failed[/] {address[:8]}")

        return result

    def display_stats(self, results):
        """Display statistics and results in a rich table"""
        stats_table = Table(title="Login Statistics", show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="yellow")
        
        stats_table.add_row("Total Accounts", str(self.stats["total"]))
        stats_table.add_row("Successful Logins", str(self.stats["success"]))
        stats_table.add_row("Failed Logins", str(self.stats["failed"]))
        success_rate = (self.stats["success"] / self.stats["total"]) * 100 if self.stats["total"] > 0 else 0
        stats_table.add_row("Success Rate", f"{success_rate:.2f}%")
        
        console.print(stats_table)
        
        # Display recent results
        results_table = Table(title="Recent Login Results", show_header=True, header_style="bold blue")
        results_table.add_column("Address", style="cyan")
        results_table.add_column("Status", style="bold")
        results_table.add_column("Reason")
        results_table.add_column("Timestamp", style="dim")
        
        # Only show the last 10 results
        for result in results[-10:]:
            status_style = "green" if result["status"] == "Success" else "red"
            results_table.add_row(
                result["address"][:16] + "..." if len(result["address"]) > 16 else result["address"],
                f"[{status_style}]{result['status']}[/{status_style}]",
                result["reason"],
                result["timestamp"]
            )
        
        console.print(results_table)

    async def run(self):
        self.show_banner()
        choice = self.print_proxy_options()
        await self.load_proxies(choice)
        
        results = []

        while True:
            try:
                with open("privateKeys.txt", "r") as f:
                    accounts = [line.strip() for line in f if line.strip()]

                if not accounts:
                    self.log("Tidak ada akun ditemukan!", level="error")
                    return

                self.stats["total"] = len(accounts)
                loop_results = []
                
                # Create a custom progress display
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    self.progress = progress
                    overall_task = progress.add_task("[yellow]Overall Progress", total=len(accounts))
                    
                    # Create tasks for each account
                    tasks = []
                    for i, account in enumerate(accounts):
                        task_id = progress.add_task(f"Waiting... {i+1}/{len(accounts)}", total=1)
                        tasks.append(self.process_account(account, task_id))
                        
                    # Process accounts with asyncio.gather
                    completed_tasks = await asyncio.gather(*tasks)
                    loop_results.extend(completed_tasks)
                    
                    progress.update(overall_task, completed=len(accounts))
                
                # Update results with the latest batch
                results.extend(loop_results)
                
                # Display statistics
                self.display_stats(results)
                
                # Wait before next loop
                wait_time = random.randint(600, 610)
                self.log(f"Menunggu {wait_time} detik sebelum loop berikutnya...", style="cyan")
                
                # Show countdown timer
                with Progress(
                    TextColumn("[bold cyan]Waiting for next cycle:"),
                    BarColumn(),
                    TextColumn("[bold cyan]{task.percentage:.0f}%"),
                    console=console
                ) as progress:
                    wait_task = progress.add_task("Waiting", total=wait_time)
                    for _ in range(wait_time):
                        await asyncio.sleep(1)
                        progress.update(wait_task, advance=1)
                
            except Exception as e:
                self.log(f"Error in main loop: {str(e)}", level="error")
                await asyncio.sleep(10)  # Short delay before retry after error

if __name__ == "__main__":
    try:
        bot = MultipleLite()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        console.print("\n[bold red]Proses dihentikan oleh pengguna.[/]")
    except Exception as e:
        console = Console(stderr=True)
        console.print_exception(show_locals=True)
    
