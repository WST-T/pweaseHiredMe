# Interview Bot Command List 🤖

## User Commands 👤

| Command | Description | Example |
|---------|-------------|---------|
| `!schedule <date> <type> <description>` | Schedule a new interview | `!schedule 2024-02-15 Technical "Backend Engineer interview"` |
| `!my_interviews` | List your scheduled interviews | `!my_interviews` |
| `!update_interview <ID> <key=value>` | Modify your interview details | `!update_interview 5 date=2024-02-16 type=Technical desc="Rescheduled to 2PM"` |
| `!delete_interview <ID>` | Remove one of your interviews | `!delete_interview 5` |

## Admin Commands 👑

| Command | Description | Permission Needed |
|---------|-------------|-------------------|
| `!all_interviews` | View all scheduled interviews | Administrator |

## Automatic Features ⏰

**Daily Reminders**  
📅 Posted every day at 8AM Paris time  
`• Alice: Technical - Frontend review`

**Weekly Rankings**  
🏆 Posted every Sunday at 8PM Paris time  
`1. Bob: 5 interviews`

## Command Details 📚

### Schedule Command
!schedule 2024-03-01 HR "Cultural fit interview"

    Date Format: YYYY-MM-DD (e.g., 2024-02-28)

    Description: Use quotes for multi-word descriptions
-----------------------------------------------------------------------
    Update Command - 
    !update_interview 3 date=2024-02-20 desc="Changed to video call"

    Valid Keys:

    date= - New interview date

    type= - New interview type

    desc= - New description
-----------------------------------------------------------------------
    Delete Command - 
    !delete_interview 7
    ❗ Note: Deleted interviews cannot be recovered
-----------------------------------------------------------------------
    Help Command - 
    !help
-----------------------------------------------------------------------
    Total Command -
    !total
    🐣 This command will retrieves your all time amount of schedule

## Pro Tips 💡

    - Find your interview IDs using !my_interviews

    - All times are in Paris Timezone (CET/CEST)

    - Old interviews auto-delete 1 day after their date

    - Use quotes " " for descriptions with spaces

📁 Database File: interviews.db (SQLite)
⏲️ Timezone: Europe/Paris
🔧 Need Help? Contact your server admin!
