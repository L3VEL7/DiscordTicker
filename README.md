# PDT Price Tracking Bot

A Discord bot that tracks and displays the PDT token price with real-time updates.

## Features

- 🔄 Real-time price updates every 5 minutes
- 📊 Displays current price in bot's nickname
- 📈 Shows price trend with up/down indicators
- 🎨 Role color changes based on price movement (green/red)
- ⏱️ Shows 24-hour price change percentage in status

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Discord Server ID

### Step 1: Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Enable these privileged intents:
   - Server Members Intent
   - Message Content Intent
   - Presence Intent
6. Copy the bot token (you'll need this later)

### Step 2: Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PDT-Bot.git
cd PDT-Bot
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/Mac:
```bash
source .venv/bin/activate
```

4. Install requirements:
```bash
pip install -r requirements.txt
```

### Step 3: Configuration

1. Create a `.env` file in the project root:
```env
DISCORD_TOKEN=your_discord_bot_token
GUILD_ID=your_discord_server_id
OPENAI_API_KEY=your_openai_api_key  # Optional, only needed for agency features
```

2. Replace the placeholders with your actual values:
- `your_discord_bot_token`: The token from Discord Developer Portal
- `your_discord_server_id`: Your Discord server (guild) ID
- `your_openai_api_key`: Your OpenAI API key (optional)

### Step 4: Invite Bot to Server

1. Go back to Discord Developer Portal
2. Select your application
3. Go to OAuth2 -> URL Generator
4. Select these scopes:
   - `bot`
   - `applications.commands`
5. Select these bot permissions:
   - View Channels
   - Change Nickname
   - Manage Roles
   - Send Messages
6. Copy and open the generated URL
7. Select your server and authorize the bot

### Step 5: Running the Bot

1. Make sure you're in the project directory with the virtual environment activated
2. Run the bot:
```bash
python run_bot.py
```

The bot should now:
- Join your server
- Update its nickname with the current PDT price
- Change role color based on price movement
- Show 24h change in its status

## Debug Mode

To run the bot in debug mode with more detailed logging:

```bash
# Set DEBUG environment variable
set DEBUG=1  # Windows
export DEBUG=1  # Linux/Mac
```

## Deploy to Railway

You can also deploy the bot to [Railway](https://railway.app) for 24/7 uptime:

1. Fork this repository to your GitHub account

2. Create a Railway account:
   - Go to [Railway.app](https://railway.app)
   - Sign up with your GitHub account

3. Create a new project:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository

4. Add environment variables:
   - Go to your project's "Variables" tab
   - Add the following variables:
     ```
     DISCORD_TOKEN=your_discord_bot_token
     GUILD_ID=your_discord_server_id
     DEBUG=0  # Set to 1 for debug logging
     ```

5. Your bot will automatically deploy and start running
   - Railway will handle all the dependencies and deployment
   - The bot will run 24/7 with automatic updates

## Troubleshooting

- **Bot not updating role color**: Make sure the bot's role is high enough in the server's role hierarchy
- **Missing Permissions**: Check that the bot has all required permissions
- **Connection Issues**: Verify your Discord token and server ID are correct

## License

This project is licensed under the MIT License - see the LICENSE file for details. 