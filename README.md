

## 🎯 Overview

> **Development Note**: This solution was developed with minimal LLM assistance, primarily for documentation formatting and code structure guidance. The core business logic, API integration, and technical implementation were completed independently.

The solution demonstrates the ability to:
- Work with REST APIs
- Understand permission models
- Communicate technical solutions to business stakeholders
- Programmatically manage Confluence Cloud resources
- Implement sophisticated workspace management
- Handle complex permission scenarios

## 🏗️ Architecture

The solution is built with Python and includes:

- **ConfluenceClient**: A comprehensive REST API client for Confluence Cloud
- **ConfluenceSetup**: Main orchestrator class that handles the complete setup process
- **Modular Design**: Separate methods for users, groups, spaces, and content management
- **Error Handling**: Robust error handling with detailed logging
- **Permission Management**: Proper permission configuration for different access levels

## 📋 Features Implemented

### ✅ User Management
- Creates 1 administrator user (`admin-user`)
- Creates 4 standard users (`user-1`, `user-2`, `user-3`, `user-4`)
- Proper role assignment and permissions

### ✅ Group Management
- Creates a group called `standard-users`
- Adds all 4 standard users to the group
- Excludes administrator from the group

### ✅ Space Management
- **Administrator Space**: Restricted to administrators only
- **Restricted Workspace**: Highly restricted workspace for sensitive information
- **Collaborative Workspace**: Open collaborative workspace for team projects
- **Team Space**: Group members can view and edit
- **Public Space**: All users can view, only administrators can edit

### ✅ Content Management
- Creates pages in different spaces with appropriate permissions
- Creates blog posts with proper access controls
- Implements content-level permission restrictions

## 🚀 Quick Start

### Prerequisites

1. **Confluence Cloud Account**: Create a free account at [Atlassian Cloud](https://www.atlassian.com/)
2. **Python 3.7+**: Ensure Python is installed on your system
3. **API Token**: Generate an API token from your Atlassian account
4. **⚠️ Manual User Creation**: Users must be created manually (see User Creation Guide below)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd confluence-task
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp env_example.txt .env
   ```

4. **Update `.env` file** with your Confluence Cloud credentials:
   ```env
   CONFLUENCE_URL=https://your-domain.atlassian.net
   CONFLUENCE_EMAIL=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token-here
   ```

### ⚠️ Important: User Creation Required

**Confluence Cloud does not support direct user creation via REST API.** Users must be created manually through the Atlassian admin console.

**Before running the setup script:**
1. Read the [User Creation Guide](user_creation_guide.md)
2. Create all 5 users manually in your Confluence admin console
3. Ensure one user has administrator privileges
4. Then run the setup script

### Running the Setup

Execute the main script to run the complete setup:

```bash
python main.py
```

The script will:
1. **Verify users exist** (created manually)
2. Set up groups and add users
3. Create spaces with proper permissions
4. Generate sample content (pages and blog posts)
5. Configure content-level permissions

## 🔧 Configuration


### API Token Setup

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a descriptive name (e.g., "Confluence Setup Script")
4. Copy the generated token to your `.env` file

## 📁 Project Structure

```
confluence-task/
├── main.py                 # Main setup script
├── confluence_client.py    # Confluence REST API client
├── requirements.txt        # Python dependencies
├── env_example.txt        # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔐 Permission Model

The solution implements a comprehensive permission model:

### User Roles
- **Administrator**: Full access to all resources
- **Standard Users**: Limited access based on group membership

### Space Permissions
- **Administrator Space**: Admin-only access
- **Team Space**: Group-based access (standard-users group)
- **Public Space**: Read access for all, write access for admins

### Content Permissions
- **Admin Content**: Restricted to administrators
- **Team Content**: Group members can view and edit
- **Public Content**: All users can read, admins can write

## 🛠️ API Endpoints Used

The solution utilizes the following Confluence REST API endpoints:

- `POST /rest/api/user` - Create users
- `POST /rest/api/group` - Create groups
- `POST /rest/api/group/{groupName}/member` - Add users to groups
- `POST /rest/api/space` - Create spaces
- `POST /rest/api/space/{spaceKey}/permission` - Set space permissions
- `POST /rest/api/content` - Create pages and blog posts
- `POST /rest/api/content/{contentId}/permission` - Set content permissions

## 📊 Expected Output

After running the setup, you should see:

```
🚀 Starting Confluence Cloud setup...
==================================================
🔧 Setting up users...
  Creating user: admin-user
  ✅ User admin-user created successfully
  Creating user: user-1
  ✅ User user-1 created successfully
  ...

🔧 Setting up groups...
  Creating group: standard-users
  ✅ Group standard-users created successfully
  Adding user-1 to group standard-users
  ✅ User user-1 added to group successfully
  ...

🔧 Setting up spaces...
  Creating space: ADMIN
  ✅ Space ADMIN created successfully
  ✅ Permissions set for space ADMIN
  ...

🔧 Setting up content...
  Creating page: Admin Documentation in space ADMIN
  ✅ Page 'Admin Documentation' created successfully
  ✅ Permissions set for content 123456
  ...

🎉 Setup completed successfully!
==================================================
✅ Created 5 users
✅ Created 1 group: standard-users
✅ Created 3 spaces
✅ Created 5 content items

📋 Summary:
  - Users: ['admin-user', 'user-1', 'user-2', 'user-3', 'user-4']
  - Group: standard-users
  - Spaces: ['ADMIN', 'TEAM', 'PUBLIC']
  - Content: ['Admin Documentation', 'Team Guidelines', 'Welcome to Our Confluence Site', ...]
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your API token is correct
   - Ensure your email address matches your Atlassian account
   - Check that your Confluence URL is properly formatted

2. **Permission Errors**:
   - Ensure your account has admin privileges on the Confluence site
   - Verify the site allows programmatic access

3. **Rate Limiting**:
   - The script includes delays to respect API rate limits
   - If you encounter rate limit errors, increase the delay in the script

4. **User Creation Failures**:
   - Some users might already exist
   - Check your Confluence site's user management settings

### Debug Mode

For detailed debugging, you can modify the script to include more verbose logging or add print statements to track the execution flow.

## 🔒 Security Considerations

- **API Token**: Never commit your API token to version control
- **Environment Variables**: Use `.env` files for sensitive configuration
- **Test Environment**: Always use a dedicated test site, never production
- **Permissions**: Review and validate all permission settings

## 📈 Future Enhancements

Potential improvements for the solution:

1. **Configuration File**: JSON/YAML configuration for users, spaces, and content
2. **Batch Operations**: Optimize API calls for better performance
3. **Validation**: Add validation for created resources
4. **Rollback**: Implement cleanup functionality
5. **Logging**: Enhanced logging with different levels
6. **Testing**: Unit tests for all components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is created for educational purposes as part of a technical assessment.

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section
2. Review the Confluence REST API documentation
3. Verify your environment configuration
4. Check the script output for specific error messages

---

**Note**: This solution is designed for the Senior Technical Specialist take-home exercise and demonstrates proficiency in REST API integration, permission management, and technical solution design.
