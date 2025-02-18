from aiohttp import ClientResponseError, ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from eth_account import Account
from eth_account.messages import encode_defunct
from fake_useragent import FakeUserAgent
from datetime import datetime, timezone
from colorama import Fore, Style, init
import asyncio
import json
import random
import os
import pytz
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

init(autoreset=True)
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
        self.use_proxy = False  # Variabel untuk menyimpan pilihan proxy
        self.progress_bar = None

    def show_banner(self):
        """Menampilkan banner saat script dijalankan."""
        banner = f"""
{Fore.YELLOW + Style.BRIGHT}
╔══════════════════════════════════════════════╗
║      🚀 MultipleLite - Auto Login Bot        ║
║    Automate your login process faster!       ║
║  Developed by: https://t.me/sentineldiscus   ║
╚══════════════════════════════════════════════╝
{Style.RESET_ALL}"""
        print(banner)

    def log(self, message):
        print(f"{Fore.CYAN}[{datetime.now().astimezone(wib).strftime('%x %X %Z')}] {Style.RESET_ALL}{message}", flush=True)

    def print_proxy_options(self):
        """Menampilkan opsi pemilihan proxy (hanya sekali di awal)."""
        while True:
            try:
                print(f"\n{Fore.CYAN}Pilih metode proxy:{Style.RESET_ALL}")
                print("1. Gunakan Proxy Gratis")
                print("2. Gunakan Proxy Pribadi")
                print("3. Jalankan Tanpa Proxy")
                choice = int(input(f"{Fore.YELLOW}Pilih [1/2/3] -> {Style.RESET_ALL}").strip())

                if choice in [1, 2, 3]:
                    return choice
                else:
                    print(f"{Fore.RED}Masukkan angka 1, 2, atau 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Input tidak valid, masukkan angka 1, 2, atau 3.{Style.RESET_ALL}")

    async def load_proxies(self, choice):
        """Memuat daftar proxy berdasarkan pilihan user."""
        if choice == 3:
            self.use_proxy = False
            return  # Tidak menggunakan proxy

        self.use_proxy = True
        filename = "proxy.txt" if choice == 2 else "proxyshare.txt"

        try:
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
                    self.log(f"{Fore.RED}File {filename} tidak ditemukan!{Style.RESET_ALL}")

            self.log(f"{Fore.GREEN}Loaded {len(self.proxies)} proxies.{Style.RESET_ALL}")

        except Exception as e:
            self.log(f"{Fore.RED}Gagal memuat proxy: {e}{Style.RESET_ALL}")

    def get_next_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def generate_address(self, private_key):
        try:
            return Account.from_key(private_key).address
        except:
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
        except:
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
            self.log(f"{Fore.RED}Login gagal untuk {address}: {e}{Style.RESET_ALL}")
            return None

    async def process_account(self, private_key):
        proxy = self.get_next_proxy() if self.use_proxy else None
        address = self.generate_address(private_key)

        if not address:
            self.log(f"{Fore.RED}Invalid private key. Skipping...{Style.RESET_ALL}")
            return

        message = self.generate_message(address)
        signature = self.generate_signature(private_key, message)

        if not signature:
            self.log(f"{Fore.RED}Failed to generate signature. Skipping...{Style.RESET_ALL}")
            return

        token = await self.user_login(address, message, signature, proxy)
        if token:
            self.log(f"{Fore.GREEN}Login berhasil untuk {address}{Style.RESET_ALL}")
        else:
            self.log(f"{Fore.RED}Login gagal untuk {address}{Style.RESET_ALL}")

        self.progress_bar.update(1)

    async def run(self):
        self.show_banner()  # **Menampilkan banner di awal**
        choice = self.print_proxy_options()
        await self.load_proxies(choice)

        while True:
            with open("privateKeys.txt", "r") as f:
                accounts = [line.strip() for line in f if line.strip()]

            if not accounts:
                self.log(f"{Fore.RED}Tidak ada akun ditemukan!{Style.RESET_ALL}")
                return

            self.progress_bar = tqdm(total=len(accounts), desc="Memproses akun", ncols=100)

            with ThreadPoolExecutor(max_workers=10) as executor:
                loop = asyncio.get_event_loop()
                tasks = [loop.run_in_executor(executor, asyncio.run, self.process_account(acc)) for acc in accounts]
                await asyncio.gather(*tasks)

            self.progress_bar.close()
            self.log(f"{Fore.CYAN}Menunggu 10 menit sebelum loop berikutnya...{Style.RESET_ALL}")
            await asyncio.sleep(random.randint(600, 610))

if __name__ == "__main__":
    try:
        bot = MultipleLite()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print(f"{Fore.RED}Proses dihentikan oleh pengguna.{Style.RESET_ALL}")
