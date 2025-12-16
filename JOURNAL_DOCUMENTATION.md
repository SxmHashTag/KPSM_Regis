# Daily Work Journal Documentation

## Overview
The Daily Work Journal feature allows team members to document their daily tasks and activities. All users can view everyone's journal entries, but users can only edit and delete their own entries.

## Features

### 1. **Journal Entries**
- Each user can create one journal entry per day
- Entries include:
  - **Date**: The workday date
  - **Title**: Brief summary of the day
  - **Content**: Detailed description of tasks completed
  - **Tags**: Categorize entries (e.g., analysis, investigation, report)
  - **Pin**: Mark important entries to highlight them

### 2. **Permissions**
- **View**: All authenticated users can view all journal entries
- **Create**: All users can create their own journal entries
- **Edit**: Users can only edit their own journal entries
- **Delete**: Users can only delete their own journal entries
- **Comment**: All users can comment on any journal entry

### 3. **Comments**
- Users can add comments to any journal entry
- Comments support collaboration and feedback
- Users can delete their own comments

### 4. **Filtering & Search**
- Filter by user, date, or tag
- Search in title and content
- View all journals or just your own

## Access Points

### Navigation
- **Main Menu**: Click "Journals" in the top navigation bar
- **URL**: `/journals/`

### Key Pages
- **All Journals**: `/journals/` - View all team journal entries
- **My Journals**: `/journals/my/` - View only your journal entries
- **Create Entry**: `/journals/create/` - Create a new journal entry
- **View Entry**: `/journals/<id>/` - View a specific entry
- **Edit Entry**: `/journals/<id>/edit/` - Edit your entry
- **Delete Entry**: `/journals/<id>/delete/` - Delete your entry

## How to Use

### Creating a Journal Entry
1. Click "Journals" in the navigation menu
2. Click "New Entry" button
3. Fill in:
   - **Date**: Defaults to today, but can select any date
   - **Title**: e.g., "Daily Tasks - November 30, 2025"
   - **Content**: Detailed description of your work
   - **Tags**: Optional comma-separated tags (analysis, investigation, etc.)
   - **Pin**: Check if this is an important entry
4. Click "Create Entry"

### Viewing Journals
1. Click "Journals" in the navigation menu
2. Browse all team entries
3. Use filters to narrow results:
   - Filter by specific user
   - Filter by date
   - Filter by tag
   - Search in title/content
4. Click on any entry to view full details

### Editing Your Entry
1. Navigate to your journal entry
2. Click "Edit" button (only appears for your own entries)
3. Make changes
4. Click "Update Entry"

### Adding Comments
1. View any journal entry
2. Scroll to the comments section
3. Type your comment
4. Click "Post Comment"

### Deleting Your Entry
1. Navigate to your journal entry
2. Click "Delete" button (only appears for your own entries)
3. Confirm deletion

## Best Practices

### Writing Effective Journal Entries

1. **Be Specific**
   - Include case numbers or evidence IDs
   - Example: "Analyzed forensic evidence from Case 25-0001"

2. **Include Key Details**
   - Tasks completed
   - Time spent on major activities
   - Challenges encountered
   - Important discoveries

3. **Use Tags Effectively**
   - analysis
   - investigation
   - documentation
   - meeting
   - training
   - admin
   - report

4. **Example Entry**
   ```
   Title: Case Analysis and Evidence Processing - Nov 30, 2025
   
   Content:
   - Case 25-0001: Completed mobile device extraction
     * Extracted 2,500 messages and 340 photos
     * Found relevant evidence in WhatsApp conversations
     * Time: 3 hours
   
   - Case 25-0003: Initial evidence review
     * Catalogued 5 storage devices
     * Verified chain of custody documentation
     * Time: 1.5 hours
   
   - Team meeting: Discussed upcoming training schedule
     * Time: 45 minutes
   
   - Administrative: Updated evidence tracking system
     * Time: 30 minutes
   
   Tags: analysis, investigation, mobile-forensics
   ```

5. **Pin Important Entries**
   - Major case breakthroughs
   - Important meetings or decisions
   - Milestone completions

## Admin Features

Administrators can:
- View all journal entries and comments
- Edit or delete any journal entry
- Manage entries through Django Admin at `/admin/`
- Export journal data for reporting

## Data Structure

### Journal Entry Fields
- **ID**: Unique identifier (UUID)
- **User**: Author of the entry
- **Date**: Workday date
- **Title**: Brief summary (max 255 characters)
- **Content**: Detailed description (unlimited text)
- **Tags**: JSON array of tags
- **Is Pinned**: Boolean flag for important entries
- **Created At**: Timestamp of creation
- **Updated At**: Timestamp of last update

### Comment Fields
- **ID**: Unique identifier (UUID)
- **Journal**: Link to parent journal entry
- **User**: Comment author
- **Comment**: Comment text
- **Created At**: Timestamp of creation
- **Updated At**: Timestamp of last update

## Tips

1. **Daily Habit**: Create your journal entry at the end of each workday
2. **Consistency**: Use consistent tag names for better filtering
3. **Detail**: Include enough detail for future reference
4. **Collaboration**: Use comments to ask questions or provide feedback
5. **Review**: Periodically review your journal entries to track progress

## Integration with Cases

While journal entries are separate from case records, you can:
- Reference case numbers in your entries
- Use tags that match case types
- Track your involvement in multiple cases
- Document decisions and findings

## Privacy & Security

- All journal entries are visible to all authenticated users
- Only entry authors can edit or delete their entries
- Comments are tied to user accounts
- All actions are timestamped and auditable
- Data is stored securely in the database

## Troubleshooting

### "You already have a journal entry for this date"
- You can only have one entry per day
- Edit your existing entry instead of creating a new one

### Can't Edit or Delete an Entry
- You can only modify your own entries
- Check that you're logged in as the correct user

### Comments Not Appearing
- Refresh the page
- Ensure you clicked "Post Comment"
- Check that you're logged in

## Future Enhancements

Potential improvements:
- Export individual entries as PDF
- Markdown support for formatting
- Attach files or images to entries
- Email notifications for new comments
- Weekly/monthly summary reports
- Integration with case timelines
