# DDoS Protection System (Layer 7 & Layer 4)

A standalone DDoS protection engine built for Python/FastAPI that features a powerful **Telegram Bot Control Panel** for remote firewall management.

## Features
- **Application Layer (L7)**: Rejects blocked IPs instantly via FastAPI middleware.
- **Network Layer (L4)**: Interfaces directly with the Operating System (`route` on Mac, `iptables` on Linux) to drop massive volumetric connections natively before they hit your API.
- **Telegram Control Panel**: 
  - Block / Unblock IPs.
  - Monitor live server status (CPU, RAM, Disk).
  - Toggle the auto-block rate limiter ON or OFF directly from Telegram.

## Setup
1. Clone the repository and `cd` into it.
2. Install dependencies: `pip install -r requirements.txt`
3. Fill out your `.env` file with your Telegram Bot Token.
4. Run the API (requires `sudo` for OS firewall modifications): 
   ```bash
   sudo python -m app.main
   ```
