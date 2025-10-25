"""
Confluence Cloud Setup Script

This script implements the Senior Technical Specialist take-home exercise
for setting up a Confluence Cloud site with users, groups, spaces, and content.
"""

import os
import time
from typing import Dict, List, Any
from confluence_client import ConfluenceClient


class ConfluenceSetup:
    """Main class for setting up Confluence Cloud site."""
    
    def __init__(self):
        """Initialize the Confluence setup with API client."""
        self.client = ConfluenceClient()
        self.users = {}
        self.group_name = "standard-users"
        self.spaces = {}
        self.content = {}
    
    def setup_users(self) -> None:
        """
        Create users as specified in the requirements:
        - 1 administrator user
        - 4 standard users
        
        Note: Users must be created manually through Atlassian admin console
        as Confluence Cloud doesn't support direct user creation via API.
        """
        print("🔧 Setting up users...")
        print("⚠️  IMPORTANT: Confluence Cloud requires manual user creation.")
        print("   Users must be created through the Atlassian admin console.")
        print()
        
        # User configurations
        user_configs = [
            {
                'username': 'merveille',
                'email': 'mmnjong@gmail.com',
                'display_name': 'Administrator User',
                'is_admin': True
            },
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'display_name': 'Standard User 1',
                'is_admin': False
            },
            {
                'username': 'user2',
                'email': 'user2@example.com',
                'display_name': 'Standard User 2',
                'is_admin': False
            },
            {
                'username': 'user3',
                'email': 'user3@example.com',
                'display_name': 'Standard User 3',
                'is_admin': False
            },
            {
                'username': 'User 4',
                'email': 'user4@example.com',
                'display_name': 'Standard User 4',
                'is_admin': False
            }
        ]
        
        print("📋 User Creation Instructions:")
        print("=" * 50)
        print("1. Go to your Atlassian admin console")
        print("2. Navigate to 'User management' > 'Users'")
        print("3. Click 'Invite users' or 'Add users'")
        print("4. Create the following users:")
        print()
        
        for i, config in enumerate(user_configs, 1):
            print(f"User {i}: {config['display_name']}")
            print(f"  - Username: {config['username']}")
            print(f"  - Email: {config['email']}")
            print(f"  - Admin privileges: {'Yes' if config['is_admin'] else 'No'}")
            print()
        
        print("⏳ Please create all users manually, then press Enter to continue...")
        input("Press Enter when all users are created...")
        
        # Verify users exist and add them to our tracking
        for config in user_configs:
            try:
                print(f"  Verifying user: {config['username']}")
                if self.client.check_user_exists(config['username']):
                    user = {
                        'id': f'user-{config["username"]}',
                        'username': config['username'],
                        'email': config['email'],
                        'displayName': config['display_name'],
                        'isAdmin': config['is_admin']
                    }
                    self.users[config['username']] = user
                    print(f"  ✅ User {config['username']} verified and ready")
                else:
                    print(f"  ❌ User {config['username']} not found. Please create this user first.")
                    # Continue with other users even if one fails
                
            except Exception as e:
                print(f"  ❌ Failed to verify user {config['username']}: {e}")
        
        print(f"✅ User setup completed. {len(self.users)} users ready for setup.")
    
    def setup_groups(self) -> None:
        """
        Create group and add standard users to it.
        Administrator is not added to the group.
        """
        print("🔧 Setting up groups...")
        
        try:
            # Create the group
            print(f"  Creating group: {self.group_name}")
            try:
                group = self.client.create_group(self.group_name)
                print(f"  ✅ Group {self.group_name} created successfully")
            except Exception as group_error:
                if "already exists" in str(group_error) or "Group already exists" in str(group_error):
                    print(f"  ⚠️ Group {self.group_name} already exists - using existing group")
                else:
                    raise group_error
            
            # Add standard users to the group (exclude admin)
            standard_users = [username for username in self.users.keys() if username != 'PepikM']
            
            if not standard_users:
                print("  ⚠️ No standard users available to add to group.")
                print("  Please ensure users are created and verified first.")
                return
            
            for username in standard_users:
                try:
                    print(f"  Adding {username} to group {self.group_name}")
                    self.client.add_user_to_group(self.group_name, username)
                    print(f"  ✅ User {username} added to group successfully")
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"  ❌ Failed to add {username} to group: {e}")
            
            print(f"✅ Group setup completed. Added {len(standard_users)} users to group.")
            
        except Exception as e:
            print(f"❌ Failed to setup groups: {e}")
    
    def setup_spaces(self) -> None:
        """
        Create spaces with proper permissions.
        - Admin Space: Only administrators can view and edit
        - Team Space: Group members can view and edit
        - Public Space: All users can view, only administrators can edit
        """
        print("🔧 Setting up spaces...")
        
        space_configs = [
            {
                'key': 'ADMIN',
                'name': 'Administrator Space',
                'description': 'Space restricted to administrators only'
            },
            {
                'key': 'RESTRICTED',
                'name': 'Restricted Workspace',
                'description': 'Highly restricted workspace for sensitive information'
            },
            {
                'key': 'COLLAB',
                'name': 'Collaborative Workspace',
                'description': 'Open collaborative workspace for team projects'
            },
            {
                'key': 'TEAM',
                'name': 'Team Space',
                'description': 'Space for team collaboration'
            },
            {
                'key': 'PUBLIC',
                'name': 'Public Space',
                'description': 'Public space with read access for all users'
            }
        ]
        
        for config in space_configs:
            try:
                print(f"  Creating space: {config['key']}")
                space = self.client.create_space(
                    space_key=config['key'],
                    name=config['name'],
                    description=config['description']
                )
                self.spaces[config['key']] = space
                print(f"  ✅ Space {config['key']} created successfully")
                
                # Note: Space permissions must be set manually in Confluence admin console
                print(f"  ⚠️ Note: Set space permissions manually for {config['key']} in Confluence admin console")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                if "already exists" in str(e) or "Space keys must be unique" in str(e):
                    print(f"  ⚠️ Space {config['key']} already exists - using existing space")
                    # Try to get existing space
                    try:
                        space = self.client.get_space(config['key'])
                        self.spaces[config['key']] = space
                        print(f"  ✅ Using existing space {config['key']}")
                        # Note: Space permissions must be set manually in Confluence admin console
                        print(f"  ⚠️ Note: Set space permissions manually for {config['key']} in Confluence admin console")
                    except:
                        print(f"  ❌ Could not access existing space {config['key']}")
                else:
                    print(f"  ❌ Failed to create space {config['key']}: {e}")
        
        print(f"✅ Space setup completed. Created {len(self.spaces)} spaces.")
    
    
    def setup_content(self) -> None:
        """
        Create pages and blog posts with proper permissions.
        """
        print("🔧 Setting up content...")
        
        # Create pages in different spaces
        page_configs = [
            {
                'space_key': 'ADMIN',
                'title': 'Admin Documentation',
                'content': '''
                <h1>Administrator Documentation</h1>
                <p>This page contains sensitive administrative information.</p>
                <h2>System Configuration</h2>
                <ul>
                    <li>Database settings</li>
                    <li>Security configurations</li>
                    <li>User management procedures</li>
                </ul>
                ''',
            },
            {
                'space_key': 'RESTRICTED',
                'title': 'Confidential Information',
                'content': '''
                <h1>Confidential Information</h1>
                <p>This workspace contains highly sensitive and confidential information.</p>
                <h2>Security Protocols</h2>
                <ul>
                    <li>Access is strictly limited to authorized personnel</li>
                    <li>All content is encrypted and protected</li>
                    <li>Regular security audits are conducted</li>
                </ul>
                <h2>Compliance Requirements</h2>
                <ul>
                    <li>GDPR compliance documentation</li>
                    <li>Security incident procedures</li>
                    <li>Data retention policies</li>
                </ul>
                ''',
            },
            {
                'space_key': 'COLLAB',
                'title': 'Collaborative Project Hub',
                'content': '''
                <h1>Collaborative Project Hub</h1>
                <p>Welcome to our open collaborative workspace! This space encourages innovation and teamwork.</p>
                <h2>Project Management</h2>
                <ul>
                    <li>Active project tracking</li>
                    <li>Team collaboration tools</li>
                    <li>Real-time updates and notifications</li>
                </ul>
                <h2>Innovation Lab</h2>
                <ul>
                    <li>Brainstorming sessions</li>
                    <li>Prototype development</li>
                    <li>Knowledge sharing</li>
                </ul>
                ''',
            },
            {
                'space_key': 'TEAM',
                'title': 'Team Guidelines',
                'content': '''
                <h1>Team Guidelines</h1>
                <p>Welcome to the team space! This document outlines our team's working guidelines.</p>
                <h2>Communication</h2>
                <ul>
                    <li>Use clear and concise language</li>
                    <li>Update documentation regularly</li>
                    <li>Collaborate effectively</li>
                </ul>
                <h2>Best Practices</h2>
                <ul>
                    <li>Code review process</li>
                    <li>Testing procedures</li>
                    <li>Documentation standards</li>
                </ul>
                ''',
            },
            {
                'space_key': 'PUBLIC',
                'title': 'Welcome to Our Confluence Site',
                'content': '''
                <h1>Welcome to Our Confluence Site</h1>
                <p>This is a public page accessible to all users.</p>
                <h2>Getting Started</h2>
                <p>Here you can find general information about our organization and resources.</p>
                <h2>Resources</h2>
                <ul>
                    <li>Company policies</li>
                    <li>General announcements</li>
                    <li>Contact information</li>
                </ul>
                ''',
            }
        ]
        
        # Create pages
        for config in page_configs:
            try:
                print(f"  Creating page: {config['title']} in space {config['space_key']}")
                page = self.client.create_page(
                    space_key=config['space_key'],
                    title=config['title'],
                    content=config['content']
                )
                self.content[config['title']] = page
                print(f"  ✅ Page '{config['title']}' created successfully")
                
                # Note: Content permissions must be set manually in Confluence
                print(f"  ⚠️ Note: Set content permissions manually for '{config['title']}' in Confluence")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                if "already exists" in str(e) or "same TITLE" in str(e):
                    print(f"  ⚠️ Page '{config['title']}' already exists - skipping")
                else:
                    print(f"  ❌ Failed to create page '{config['title']}': {e}")
        
        # Create blog posts
        blog_configs = [
            {
                'space_key': 'RESTRICTED',
                'title': 'Security Alert - System Maintenance',
                'content': '''
                <h1>Security Alert - System Maintenance</h1>
                <p>This is a confidential security update for authorized personnel only.</p>
                <h2>Security Updates</h2>
                <ul>
                    <li>Critical security patches applied</li>
                    <li>Access logs reviewed and analyzed</li>
                    <li>New security protocols implemented</li>
                </ul>
                <h2>Action Required</h2>
                <ul>
                    <li>All users must update their passwords</li>
                    <li>Two-factor authentication is now mandatory</li>
                    <li>Regular security training sessions scheduled</li>
                </ul>
                ''',
            },
            {
                'space_key': 'COLLAB',
                'title': 'Innovation Spotlight - New Ideas',
                'content': '''
                <h1>Innovation Spotlight - New Ideas</h1>
                <p>Sharing exciting new ideas and innovations from our collaborative workspace!</p>
                <h2>Featured Innovations</h2>
                <ul>
                    <li>AI-powered automation tools</li>
                    <li>Enhanced user experience designs</li>
                    <li>Sustainable technology solutions</li>
                </ul>
                <h2>Collaboration Opportunities</h2>
                <ul>
                    <li>Cross-team project initiatives</li>
                    <li>Knowledge sharing sessions</li>
                    <li>Innovation workshops</li>
                </ul>
                ''',
            },
            {
                'space_key': 'TEAM',
                'title': 'Team Update - Project Status',
                'content': '''
                <h1>Project Status Update</h1>
                <p>Here's the latest update on our current project status.</p>
                <h2>Completed Tasks</h2>
                <ul>
                    <li>User authentication setup</li>
                    <li>Database configuration</li>
                    <li>API integration</li>
                </ul>
                <h2>Next Steps</h2>
                <ul>
                    <li>Testing and validation</li>
                    <li>Documentation updates</li>
                    <li>Deployment preparation</li>
                </ul>
                ''',
            },
            {
                'space_key': 'PUBLIC',
                'title': 'Company News - Q1 Updates',
                'content': '''
                <h1>Q1 Company Updates</h1>
                <p>Welcome to our quarterly company updates!</p>
                <h2>Key Achievements</h2>
                <ul>
                    <li>Successful product launch</li>
                    <li>Team expansion</li>
                    <li>Customer satisfaction improvements</li>
                </ul>
                <h2>Looking Ahead</h2>
                <p>We're excited about the upcoming quarter and the new initiatives we'll be launching.</p>
                ''',
            }
        ]
        
        # Create blog posts
        for config in blog_configs:
            try:
                print(f"  Creating blog post: {config['title']} in space {config['space_key']}")
                blog_post = self.client.create_blog_post(
                    space_key=config['space_key'],
                    title=config['title'],
                    content=config['content']
                )
                self.content[config['title']] = blog_post
                print(f"  ✅ Blog post '{config['title']}' created successfully")
                
                # Note: Content permissions must be set manually in Confluence
                print(f"  ⚠️ Note: Set content permissions manually for '{config['title']}' in Confluence")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                if "already exists" in str(e) or "same TITLE" in str(e):
                    print(f"  ⚠️ Blog post '{config['title']}' already exists - skipping")
                else:
                    print(f"  ❌ Failed to create blog post '{config['title']}': {e}")
        
        print(f"✅ Content setup completed. Created {len(self.content)} content items.")
    
    
    def run_setup(self) -> None:
        """Run the complete Confluence setup process."""
        print("🚀 Starting Confluence Cloud setup...")
        print("=" * 50)
        
        try:
            # Execute setup steps in order
            self.setup_users()
            print()
            
            self.setup_groups()
            print()
            
            self.setup_spaces()
            print()
            
            self.setup_content()
            print()
            
            # Summary
            print("🎉 Setup completed successfully!")
            print("=" * 50)
            print(f"✅ Created {len(self.users)} users")
            print(f"✅ Created 1 group: {self.group_name}")
            print(f"✅ Created {len(self.spaces)} spaces")
            print(f"✅ Created {len(self.content)} content items")
            print()
            print("📋 Summary:")
            print(f"  - Users: {list(self.users.keys())}")
            print(f"  - Group: {self.group_name}")
            print(f"  - Spaces: {list(self.spaces.keys())}")
            print(f"  - Content: {list(self.content.keys())}")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise


def main():
    """Main function to run the Confluence setup."""
    try:
        setup = ConfluenceSetup()
        setup.run_setup()
    except Exception as e:
        print(f"❌ Application failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
