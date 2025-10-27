# 🧭 Confluence Cloud Setup — Take-Home Solution

> Automated setup of Confluence Cloud users, groups, spaces, and permissions.

---

## 🎯 Overview

> **Development Note**: GitHub Copilot was used only for documentation formatting and template suggestions.
> All implementation logic, API integration, and permission design were written manually.

**Completion Time:** ~3 hours

* Environment & Planning — 30 min
* Implementation — 1.5 hrs
* Testing & Debugging — 30 min
* Documentation — 30 min

This solution demonstrates the ability to:

* Work with REST APIs and authentication
* Manage Confluence users, groups, and spaces programmatically
* Understand and implement permission models
* Communicate technical logic clearly to business and technical stakeholders

---

## 🏗️ Architecture

**Core Components:**

* **`ConfluenceClient`** → REST API wrapper for Confluence Cloud
  Handles groups, spaces, and content operations.
* **`ConfluenceSetup`** → Main orchestrator
  Implements the full setup flow end-to-end.
* **Environment-Driven Configuration** → Uses `.env` and a `user_account_mapping.json`
* **Error Handling & Logging** → Graceful continuation, clear messages
* **Idempotent Design** → Safe to re-run without side effects

---

## 📋 Features

### 👤 User Management

* Handles 1 admin and 4 standard users
* Reads user → `accountId` mappings from JSON
* Assigns correct roles and permissions

### 👥 Group Management

* Creates `standard-users` group (if missing)
* Adds all standard users to the group
* Excludes the admin user

### 🗂️ Space Management

Creates two spaces as required:

* **COLLAB (Collaborative Workspace)** — for open teamwork
* **RESTRICT (Restricted Workspace)** — for controlled access

> *Note:* Space-level permissions setup is documented as a future enhancement.

### 📄 Content Management

* Creates a sample page: “**Project Kickoff**”
* Adds structured sections and an embedded image
* Applies **page-level read restriction** to:

  * Admin user (to retain access)
  * One selected standard user

---

## 🚀 Quick Start

### Prerequisites

1. **Confluence Cloud Account** — [Create one here](https://www.atlassian.com/)
2. **Python 3.9+**
3. **Atlassian API Token** — [Generate here](https://id.atlassian.com/manage/api-tokens)
4. **Manually Create Users** — Confluence Cloud doesn’t allow user creation via API

   * Follow `user_creation_guide.md`
   * Create: 1 admin, 4 standard users

---

### Installation

```bash
git clone <repository-url>
cd confluence-cloud-setup
pip install -r requirements.txt
cp env_example.txt .env
```

Update `.env`:

```bash
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

---

### User Mapping File

Create `user_account_mapping.json`:

```json
{
  "admin@example.com": "admin-account-id",
  "user1@example.com": "user1-account-id",
  "user2@example.com": "user2-account-id",
  "user3@example.com": "user3-account-id",
  "user4@example.com": "user4-account-id"
}
```

---

### Run the Setup

```bash
python3 main.py
```

The script will:

1. Load configuration & verify users
2. Create `standard-users` group
3. Add users to the group
4. Create spaces `COLLAB` and `RESTRICT`
5. Create and restrict the sample page

---

## 📁 Project Structure

```
confluence-cloud-setup/
├── main.py                  # Main setup script
├── confluence_client.py     # REST API client
├── requirements.txt
├── env_example.txt
├── user_account_mapping.json.example
└── README.md
```

---

## 🔐 Permission Model

| Layer                 | Description                                          |
| --------------------- | ---------------------------------------------------- |
| **Users**             | 1 Admin + 4 Standard Users                           |
| **Group**             | `standard-users` includes only standard users        |
| **Spaces**            | `COLLAB` (team access) / `RESTRICT` (limited access) |
| **Page Restrictions** | Read access only to Admin + 1 selected user          |

---

## 🛠️ API Endpoints Used

| Action            | Endpoint                                                       |
| ----------------- | -------------------------------------------------------------- |
| Create group      | `POST /rest/api/group`                                         |
| Add user to group | `POST /rest/api/group/userByGroupId`                           |
| Create space      | `POST /rest/api/space`                                         |
| Get space         | `GET /rest/api/space/{spaceKey}`                               |
| Create page       | `POST /rest/api/content`                                       |
| Restrict content  | `PUT /rest/api/content/{id}/restriction/byOperation/{op}/user` |

---

## 📊 Example Output

```
🚀 Starting Confluence Setup
==================================================
✅ Users loaded: 5
✅ Group 'standard-users' created or exists
✅ Added standard users to group
✅ Spaces created: COLLAB, RESTRICT
✅ Page created: 'Project Kickoff: Collaboration Page'
🔒 Page restricted to: admin@example.com, user1@example.com
🎉 Setup completed successfully!
```

---

## 🧩 Troubleshooting

| Issue                    | Fix                                                 |
| ------------------------ | --------------------------------------------------- |
| `Missing CONFLUENCE_URL` | Check your `.env` file                              |
| `403 Forbidden`          | Ensure admin privileges                             |
| `Mapping missing`        | Verify `user_account_mapping.json`                  |
| `Image not showing`      | Use Confluence attachments instead of external link |
| `Rate limit`             | Add small delays or re-run                          |

---

## 🔒 Security Guidelines

* Never commit `.env` or tokens
* Use a dedicated **test** Confluence site
* Run with an **admin account** that can create spaces/groups
* Review permissions before running in production

---

## ⚙️ Known Limitations & Future Enhancements

| Area              | Planned Improvement                              |
| ----------------- | ------------------------------------------------ |
| Space Permissions | Implement API-based space-level permission setup |
| Error Handling    | Add retry logic and validation for each step     |
| Config Management | Move from `.env` + JSON → single YAML config     |
| Testing           | Add mocks + integration test suite               |
| Logging           | Replace `print()` with structured logging        |

---

## 🤖 AI Assistance Attribution

| Tool               | Used For                              | Manual Refinements                                              |
| ------------------ | ------------------------------------- | --------------------------------------------------------------- |
| **GitHub Copilot** | Docstring and format suggestions      | Adjusted for clarity and consistency                            |
| **ChatGPT**        | Template guidance and troubleshooting | API integration, logic, and permission design were fully manual |

---

## 📜 License

This project was developed for the **Senior Technical Specialist Take-Home Exercise**
to demonstrate REST API integration, permission modeling, and automation proficiency.
