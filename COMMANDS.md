# Interview Bot Command List 🤖

## User Commands 👤

| Command | Description | Example |
|---------|-------------|---------|
| `!schedule <date> [time] <type> <description>` | Schedule a new interview | `!schedule 2024-02-15 14:30 Technical "Backend Engineer interview"` |
| `!my_interviews` | List your scheduled interviews | `!my_interviews` |
| `!update_interview <ID> <key=value>` | Modify your interview details | `!update_interview 5 date=2024-02-16 time=15:30 type=Technical desc="Rescheduled to 3:30PM"` |
| `!delete_interview <ID>` | Remove one of your interviews | `!delete_interview 5` |
| `!total` | Show your all-time interview count | `!total` |

## Admin Commands 👑

| Command | Description | Permission Needed |
|---------|-------------|-------------------|
| `!all_interviews` | View all scheduled interviews | Administrator |

## Automatic Features ⏰

**Daily Reminders**  
📅 Posted every day at 8AM Paris time  
`• John: at 14:30 Technical - Frontend review`

**Weekly Rankings**  
🏆 Posted every Sunday at 8PM Paris time  
`1. Bob: 5 interviews`

## Command Details 📚

### Schedule Command
```
!schedule 2024-03-01 13:45 HR "Cultural fit interview"
```

- Date Format: YYYY-MM-DD (e.g., 2024-02-28)
- Time Format: HH:MM in 24-hour format (e.g., 14:30)
- Time is optional. If not provided, it will show as "No time specified"
- Description: Use quotes for multi-word descriptions

-----------------------------------------------------------------------
### Update Command

```
!update_interview 3 date=2024-02-20 time=14:00 desc="Changed to video call"
```

Valid Keys:
- `date=` - New interview date (YYYY-MM-DD)
- `time=` - New interview time (HH:MM)
- `type=` - New interview type
- `desc=` - New description

-----------------------------------------------------------------------
### Delete Command

```
!delete_interview 7
```
❗ Note: Deleted interviews cannot be recovered

-----------------------------------------------------------------------
### Help Command

```
!help
```

-----------------------------------------------------------------------
### Total Command

```
!total
```
🐣 This command will retrieve your all-time amount of scheduled interviews

## Pro Tips 💡

- Find your interview IDs using !my_interviews
- Time format is 24-hour (military time)
- All times are in Paris Timezone (CET/CEST)
- Old interviews auto-delete 1 day after their date
- Use quotes " " for descriptions with spaces

📁 Database File: interviews.db (SQLite)  
⏲️ Timezone: Europe/Paris  
🔧 Need Help? Contact your server admin!