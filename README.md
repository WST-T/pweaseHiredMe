# pweaseHiredMe 🤖💼
![Python Version](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-blue?logo=discord)
Your friendly neighborhood interview scheduler! Never miss an interview again with daily reminders and weekly progress tracking. 🚀

```python
           _____
         /      \
        |  ◕ ◕  |    "Let's ace those interviews!"
        |   ∆   |
         \______/
           |  |
          /    \
```

## Features ✨
    📅 Schedule interviews with descriptions

    ⏰ Daily reminders at 8AM Paris time

    🏆 Weekly leaderboards every Sunday

    ✏️ Update/delete your interviews

    🧹 Automatic cleanup of past events

    📊 SQLite database for persistent storage

## Quick Commands 🎮
```bash
!schedule 2024-02-20 Technical "System Design Round"
!my_interviews
!update_interview 3 date=2024-02-25
!delete_interview 5
!help
!total
```

## Setup Guide 🛠️
1. You need to clone the repo ma dude -> 
```bash
git clone https://github.com/yourusername/interview-buddy-bot.git
cd interview-buddy-bot
```

2. Set up virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure Environment
```bash
echo "BOT_TOKEN=your_bot_token_here" > .env
echo "CHANNEL_ID=your_channel_id_here" >> .env
```

5. Run the bot!
```bash
python main.py
```

## Configuration 🔧
- BOT_TOKEN	-> Your Discord bot token
- CHANNEL_ID ->	Channel ID for reminders/rankings

## Contributing 🤝
PRs are welcome!

    1 - Fork the project

    2 - Create your feature branch

    3 - Commit your changes

    4 - Push to the branch

    5 - Open a PR
    
## License 📄
This project is licensed under the MIT License - see LICENSE file for details.

Made with 💖 by WST-T "文森特"
