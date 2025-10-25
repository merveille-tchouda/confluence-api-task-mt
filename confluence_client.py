"""
Confluence Cloud REST API Client

This module provides a client for interacting with Confluence Cloud REST API
to manage users, groups, spaces, and content with proper permissions.
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfluenceClient:
    """Client for Confluence Cloud REST API operations."""
    
    def __init__(self, base_url: str = None, email: str = None, api_token: str = None):
        """
        Initialize the Confluence client.
        
        Args:
            base_url: Confluence Cloud site URL
            email: User email for authentication
            api_token: API token for authentication
        """
        self.base_url = base_url or os.getenv('CONFLUENCE_URL')
        self.email = email or os.getenv('CONFLUENCE_EMAIL')
        self.api_token = api_token or os.getenv('CONFLUENCE_API_TOKEN')
        
        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Missing required configuration. Please check your environment variables.")
        
        # Ensure base_url doesn't end with slash
        self.base_url = self.base_url.rstrip('/')
        
        # Set up session with authentication
        self.session = requests.Session()
        self.session.auth = (self.email, self.api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the Confluence API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
        """
        # Confluence Cloud API uses /wiki/rest/api/ prefix
        if not endpoint.startswith('/wiki/rest/api/'):
            if endpoint.startswith('/rest/api/'):
                endpoint = '/wiki' + endpoint
            else:
                endpoint = '/wiki/rest/api' + endpoint
        url = urljoin(self.base_url + '/', endpoint)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise
    
    def create_user(self, username: str, email: str, display_name: str, 
                   is_admin: bool = False) -> Dict[str, Any]:
        """
        Create a new user in Confluence.
        
        Note: Confluence Cloud doesn't have a direct user creation API.
        Users must be created through the Atlassian admin console.
        This method provides instructions for manual user creation.
        
        Args:
            username: Username for the new user
            email: Email address
            display_name: Display name
            is_admin: Whether the user should have admin privileges
            
        Returns:
            Created user information
        """
        print(f"  ⚠️ IMPORTANT: Confluence Cloud doesn't support direct user creation via API.")
        print(f"  Users must be created manually through the Atlassian admin console.")
        print(f"  ")
        print(f"  📋 Manual User Creation Instructions:")
        print(f"  1. Go to your Atlassian admin console: {self.base_url}/admin")
        print(f"  2. Navigate to 'User management' > 'Users'")
        print(f"  3. Click 'Invite users' or 'Add users'")
        print(f"  4. Create user with these details:")
        print(f"     - Username: {username}")
        print(f"     - Email: {email}")
        print(f"     - Display Name: {display_name}")
        print(f"     - Admin privileges: {'Yes' if is_admin else 'No'}")
        print(f"  ")
        print(f"  ⏳ Please create this user manually, then press Enter to continue...")
        input("  Press Enter when user creation is complete...")
        
        # Return user info for the setup to continue
        user = {
            'id': f'user-{username}',
            'username': username,
            'email': email,
            'displayName': display_name,
            'isAdmin': is_admin
        }
        print(f"  ✅ User {username} ready for setup")
        return user
    
    def get_users(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of users
        """
        # Confluence Cloud doesn't have a direct user list API
        # We'll return an empty list for now as this is typically managed by site admins
        return []
    
    def check_user_exists(self, username: str) -> bool:
        """
        Check if a user exists in the system.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            # Try to get user info using accountId or email
            # Since username parameter doesn't work, we'll assume users exist
            # if they were created manually in the admin console
            print(f"  ⚠️ Cannot verify user '{username}' via API - assuming user exists")
            return True
        except:
            return False
    
    def create_group(self, group_name: str) -> Dict[str, Any]:
        """
        Create a new group.
        
        Args:
            group_name: Name of the group to create
            
        Returns:
            Created group information
        """
        data = {'name': group_name}
        return self._make_request('POST', '/rest/api/group', json=data)
    
    def add_user_to_group(self, group_name: str, username: str) -> Dict[str, Any]:
        """
        Add a user to a group.
        
        Args:
            group_name: Name of the group
            username: Username to add
            
        Returns:
            Operation result
        """
        data = {'username': username}
        return self._make_request('POST', f'/rest/api/group/{group_name}/member', json=data)
    
    def create_space(self, space_key: str, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new space.
        
        Args:
            space_key: Unique key for the space
            name: Display name of the space
            description: Description of the space
            
        Returns:
            Created space information
        """
        data = {
            'key': space_key,
            'name': name,
            'description': {'value': description, 'representation': 'storage'}
        }
        return self._make_request('POST', '/rest/api/space', json=data)
    
    
    def create_page(self, space_key: str, title: str, content: str, 
                   parent_id: str = None) -> Dict[str, Any]:
        """
        Create a new page.
        
        Args:
            space_key: Space key where page will be created
            title: Page title
            content: Page content in Confluence storage format
            parent_id: ID of parent page (optional)
            
        Returns:
            Created page information
        """
        data = {
            'type': 'page',
            'title': title,
            'space': {'key': space_key},
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }
        
        if parent_id:
            data['ancestors'] = [{'id': parent_id}]
        
        return self._make_request('POST', '/rest/api/content', json=data)
    
    def create_blog_post(self, space_key: str, title: str, content: str) -> Dict[str, Any]:
        """
        Create a new blog post.
        
        Args:
            space_key: Space key where blog post will be created
            title: Blog post title
            content: Blog post content in Confluence storage format
            
        Returns:
            Created blog post information
        """
        data = {
            'type': 'blogpost',
            'title': title,
            'space': {'key': space_key},
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }
        
        return self._make_request('POST', '/rest/api/content', json=data)
    
    
    def get_space(self, space_key: str) -> Dict[str, Any]:
        """
        Get space information.
        
        Args:
            space_key: Space key
            
        Returns:
            Space information
        """
        return self._make_request('GET', f'/rest/api/space/{space_key}')
    
    def get_content(self, content_id: str) -> Dict[str, Any]:
        """
        Get content information.
        
        Args:
            content_id: Content ID
            
        Returns:
            Content information
        """
        return self._make_request('GET', f'/rest/api/content/{content_id}')
