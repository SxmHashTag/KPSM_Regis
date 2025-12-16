from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from forensics.journal_models import DailyJournal, JournalComment


class Command(BaseCommand):
    help = 'Creates dummy journal entries for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=25,
            help='Number of journal entries to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create test users
        users = []
        user_names = [
            ('admin', 'Admin User'),
            ('jsmith', 'John Smith'),
            ('mjones', 'Maria Jones'),
            ('rwilliams', 'Robert Williams'),
            ('sbrown', 'Sarah Brown'),
        ]
        
        for username, full_name in user_names:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': full_name.split()[0],
                    'last_name': full_name.split()[1] if len(full_name.split()) > 1 else '',
                    'is_staff': username == 'admin',
                    'is_superuser': username == 'admin',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            users.append(user)
        
        # Journal entry templates
        titles = [
            "Daily Forensic Analysis - {date}",
            "Case Review and Evidence Processing - {date}",
            "Mobile Device Extraction and Analysis - {date}",
            "Digital Evidence Documentation - {date}",
            "Team Collaboration and Case Updates - {date}",
            "Advanced Forensic Techniques Applied - {date}",
            "Chain of Custody and Evidence Management - {date}",
            "Cybercrime Investigation Progress - {date}",
            "Data Recovery and Analysis Session - {date}",
            "Weekly Case Summary and Planning - {date}",
        ]
        
        content_templates = [
            """🔍 Case 25-{case_num}: Mobile Forensics Analysis
   • Extracted {msg_count} messages and {photo_count} photos from seized device
   • Found critical evidence in WhatsApp and Signal conversations
   • Recovered deleted images showing suspect at crime scene
   • Generated forensic report for prosecutor review
   ⏱️ Time: {hours} hours

📊 Case 25-{case_num2}: Computer Forensics
   • Analyzed hard drive from suspect's laptop
   • Discovered encrypted files with financial records
   • Successfully decrypted {file_count} documents using forensic tools
   • Documented findings in evidence log
   ⏱️ Time: {hours2} hours

👥 Team Meeting
   • Discussed upcoming training on new extraction tools
   • Reviewed active cases and resource allocation
   • Coordinated with prosecutors on pending trials
   ⏱️ Time: 1 hour

📝 Administrative Tasks
   • Updated evidence tracking system
   • Completed chain of custody documentation
   ⏱️ Time: 30 minutes""",
            
            """📱 Mobile Device Examination - Case 25-{case_num}
   • Performed logical and physical extraction on iPhone {model}
   • Recovered {msg_count} SMS messages, {call_count} call logs
   • Extracted GPS location data showing movement patterns
   • Found deleted photos relevant to investigation
   • Used Cellebrite UFED for extraction
   ⏱️ Time: {hours} hours

💻 Computer Analysis - Case 25-{case_num2}
   • Imaged {drive_size}TB hard drive from seized desktop
   • Verified hash values (MD5, SHA-256) for integrity
   • Began keyword searches for relevant terms
   • Identified {file_count} files of interest
   ⏱️ Time: {hours2} hours

📋 Documentation
   • Prepared preliminary findings report
   • Updated case management system
   ⏱️ Time: 45 minutes""",
            
            """🔐 Encrypted Data Analysis - Case 25-{case_num}
   • Attempted decryption of seized laptop drive
   • Successfully bypassed password protection using forensic methods
   • Found {file_count} relevant documents and spreadsheets
   • Discovered communication records with co-conspirators
   ⏱️ Time: {hours} hours

🌐 Network Traffic Analysis - Case 25-{case_num2}
   • Analyzed captured network packets from suspect's router
   • Identified suspicious connections to offshore servers
   • Documented IP addresses and timestamps
   • Prepared visual timeline of network activity
   ⏱️ Time: {hours2} hours

📞 Prosecutor Consultation
   • Briefed prosecutor on findings in Case 25-{case_num}
   • Discussed technical aspects for court presentation
   • Answered questions about evidence reliability
   ⏱️ Time: 1.5 hours""",
            
            """💾 Data Recovery - Case 25-{case_num}
   • Attempted recovery from damaged storage device
   • Successfully retrieved {file_count} files using specialized tools
   • Found deleted emails with critical evidence
   • Documented recovery process for court testimony
   ⏱️ Time: {hours} hours

🔍 Social Media Analysis - Case 25-{case_num2}
   • Examined Facebook and Instagram accounts
   • Downloaded {msg_count} messages and {photo_count} photos
   • Identified associates and communication patterns
   • Created relationship diagram for investigation
   ⏱️ Time: {hours2} hours

📚 Training
   • Attended webinar on new iOS extraction techniques
   • Practiced with updated forensic software
   ⏱️ Time: 2 hours

🗂️ Evidence Organization
   • Catalogued new evidence items
   • Updated storage location database
   ⏱️ Time: 45 minutes""",
            
            """⚖️ Court Preparation - Case 25-{case_num}
   • Prepared expert witness testimony materials
   • Created visual aids and presentations
   • Reviewed evidence findings with legal team
   • Practiced testimony for upcoming trial
   ⏱️ Time: {hours} hours

🔬 Advanced Analysis - Case 25-{case_num2}
   • Performed RAM analysis on seized computer
   • Extracted running processes and network connections
   • Found evidence of malware and unauthorized access
   • Documented attack vectors and compromised data
   ⏱️ Time: {hours2} hours

👨‍🏫 Mentoring
   • Trained junior analyst on evidence handling procedures
   • Demonstrated proper chain of custody documentation
   ⏱️ Time: 1 hour

📝 Report Writing
   • Completed detailed forensic report for Case 25-{case_num}
   • {report_pages} page technical analysis
   ⏱️ Time: 2 hours"""
        ]
        
        tags_options = [
            ['analysis', 'mobile-forensics', 'investigation'],
            ['report', 'documentation', 'analysis'],
            ['investigation', 'computer-forensics', 'encryption'],
            ['meeting', 'collaboration', 'planning'],
            ['training', 'professional-development'],
            ['court-preparation', 'testimony'],
            ['data-recovery', 'advanced-analysis'],
            ['network-analysis', 'cybercrime'],
            ['social-media', 'investigation'],
            ['evidence-management', 'admin'],
        ]
        
        comment_templates = [
            "Great work on this case! The evidence you found is crucial.",
            "Can you share more details about the extraction method used?",
            "This will be very helpful for the prosecution. Well documented!",
            "Let's discuss the timeline for case {case_num} in tomorrow's meeting.",
            "Excellent analysis. The prosecutor will definitely need this for trial.",
            "Have you considered cross-referencing this with Case {case_num2}?",
            "The recovery rate on that damaged drive is impressive!",
            "Thanks for the detailed notes. This helps our team coordination.",
            "Please make sure to update the evidence tracking system.",
            "Nice work! The visual timeline will be perfect for the jury.",
        ]
        
        # Create journal entries
        created_count = 0
        start_date = timezone.now().date() - timedelta(days=60)
        
        for i in range(count):
            # Select random user
            user = random.choice(users)
            
            # Create date (spreading entries over past 60 days, avoiding weekends)
            days_offset = random.randint(0, 60)
            entry_date = start_date + timedelta(days=days_offset)
            
            # Skip weekends
            while entry_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                days_offset += 1
                entry_date = start_date + timedelta(days=days_offset)
                if days_offset > 60:
                    break
            
            # Check if entry already exists for this user and date
            if DailyJournal.objects.filter(user=user, date=entry_date).exists():
                continue
            
            # Generate content
            title = random.choice(titles).format(date=entry_date.strftime("%B %d, %Y"))
            
            content_template = random.choice(content_templates)
            content = content_template.format(
                case_num=random.randint(1, 20),
                case_num2=random.randint(21, 40),
                msg_count=random.randint(500, 5000),
                photo_count=random.randint(50, 800),
                hours=random.randint(2, 5),
                hours2=random.randint(1, 4),
                file_count=random.randint(10, 500),
                call_count=random.randint(50, 300),
                model=random.randint(11, 15),
                drive_size=random.choice([1, 2, 4]),
                report_pages=random.randint(15, 45),
            )
            
            tags = random.choice(tags_options)
            is_pinned = random.random() < 0.15  # 15% chance of being pinned
            
            # Create journal entry
            journal = DailyJournal.objects.create(
                user=user,
                date=entry_date,
                title=title,
                content=content,
                tags=tags,
                is_pinned=is_pinned,
            )
            
            # Add 0-3 comments to some entries
            if random.random() < 0.6:  # 60% chance of having comments
                num_comments = random.randint(1, 3)
                for _ in range(num_comments):
                    commenter = random.choice([u for u in users if u != user])
                    comment_text = random.choice(comment_templates).format(
                        case_num=random.randint(1, 30),
                        case_num2=random.randint(1, 30),
                    )
                    
                    JournalComment.objects.create(
                        journal=journal,
                        user=commenter,
                        comment=comment_text,
                    )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created journal entry #{created_count}: {title[:50]}...'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {created_count} journal entries with comments!'))
        self.stdout.write(self.style.SUCCESS(f'📊 Entries span from {start_date} to {timezone.now().date()}'))
        self.stdout.write(self.style.SUCCESS(f'👥 Created with {len(users)} different users'))
