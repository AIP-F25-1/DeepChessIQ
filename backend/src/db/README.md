# Database Migrations

## Running Migrations

You need to run these SQL migration files manually in your SQL Server database.

### Prerequisites
- SQL Server Management Studio (SSMS) or Azure Data Studio
- Access to your DeepChessIQ database
- Connection credentials from your `.env` file

### How to Run Migrations

#### Option 1: Using SQL Server Management Studio (SSMS)
1. Open SSMS and connect to your SQL Server
2. Select your DeepChessIQ database
3. Open the migration file: `File > Open > File...`
4. Navigate to `backend/src/db/migrations/002_core_tables.sql`
5. Click `Execute` or press `F5`

#### Option 2: Using Azure Data Studio
1. Open Azure Data Studio and connect to your server
2. Select your database
3. Open the migration file
4. Click `Run` or press `F5`

#### Option 3: Using sqlcmd (Command Line)
```bash
sqlcmd -S your_server -d your_database -U your_username -P your_password -i migrations/002_core_tables.sql
```

### Migration Files

#### 002_core_tables.sql
Creates all core tables for the application:
- `user_profiles` - Extended user information
- `chess_ratings` - Rating history tracking
- `games` - Game records
- `game_settings` - User preferences
- `user_statistics` - Computed statistics
- `invitations` - Coach invitation system
- `coach_students` - Coach-student relationships

This migration will:
- Drop existing tables if they exist (be careful!)
- Create all tables with proper indexes
- Set up foreign keys and constraints
- Create default entries for existing users

### Important Notes

⚠️ **Warning**: The migration script will drop existing tables with the same names. Make sure you have backups if you have important data.

### Verification

After running the migration, verify the tables were created:

```sql
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
```

You should see:
- users (existing)
- user_profiles
- chess_ratings
- games
- game_settings
- user_statistics
- invitations
- coach_students

### Next Steps

After running the migrations, you can:
1. Start the backend server: `npm run dev`
2. Test the API endpoints
3. Integrate with the frontend

