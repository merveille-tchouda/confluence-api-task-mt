"""
Confluence Cloud Setup Script (final minimal)

- Expects .env and user_account_mapping.json in repo root.
- Creates group 'standard-users' (if missing), adds 4 standard users to it.
- Creates two spaces: COLLAB and RESTRICT (if missing) with robust lookup fallback.
- Creates a page in COLLAB with an embedded image.
- Applies space-level permissions:
    * COLLAB: one standard user -> space admin; other standard users -> write+read
    * RESTRICT: site admin -> space admin; all standard users -> read-only
- Applies a page-level read restriction to admin + one non-admin user.
"""

import os
import time
import json
from typing import Dict, Any, Optional, List

from confluence_client import ConfluenceClient


class ConfluenceSetup:
    def __init__(self):
        self.client = ConfluenceClient()
        self.users: Dict[str, Dict[str, Any]] = {}
        self.group_name = "standard-users"
        self.spaces: Dict[str, Dict[str, Any]] = {}
        self.content: Dict[str, Dict[str, Any]] = {}

        # user configs (used for mapping keys + instructions)
        self.user_configs = [
            {'username': 'merveille', 'email': 'mmnjong@gmail.com', 'display_name': 'Administrator User', 'is_admin': True},
            {'username': 'user1', 'email': 'user1@example.com', 'display_name': 'Standard User 1', 'is_admin': False},
            {'username': 'user2', 'email': 'user2@example.com', 'display_name': 'Standard User 2', 'is_admin': False},
            {'username': 'user3', 'email': 'user3@example.com', 'display_name': 'Standard User 3', 'is_admin': False},
            {'username': 'user4', 'email': 'user4@example.com', 'display_name': 'Standard User 4', 'is_admin': False},
        ]

    def _load_user_mapping(self) -> Optional[Dict[str, str]]:
        mapping_path = os.path.join(os.path.dirname(__file__), 'user_account_mapping.json')
        if not os.path.exists(mapping_path):
            return None
        try:
            with open(mapping_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"❌ Failed to load user_account_mapping.json: {e}")
        return None

    def setup_users(self) -> None:
        """
        Load accountId mapping for users and populate self.users.
        If mapping missing, instruct and prompt the operator to create it.
        """
        print("🔧 Setting up users (mapping-based)...")
        mapping = self._load_user_mapping()
        if mapping is None:
            print("⚠️ user_account_mapping.json not found. Please create it with email -> accountId mappings.")
            print("Example:")
            print(json.dumps({u['email']: "<accountId>" for u in self.user_configs}, indent=2))
            input("Press Enter after creating user_account_mapping.json (or Ctrl+C to abort)...")
            mapping = self._load_user_mapping()
            if mapping is None:
                raise SystemExit("user_account_mapping.json missing or invalid; aborting.")

        found = 0
        for cfg in self.user_configs:
            email = cfg['email']
            acct = mapping.get(email)
            if acct:
                self.users[cfg['username']] = {
                    'accountId': acct,
                    'email': email,
                    'displayName': cfg['display_name'],
                    'isAdmin': cfg['is_admin'],
                    'username': cfg['username']
                }
                print(f"  ✅ mapping found: {email} -> {acct}")
                found += 1
            else:
                print(f"  ⚠️ mapping missing for {email}")

        print(f"✅ Users loaded: {found}/{len(self.user_configs)} (will continue with loaded users)")

    def setup_groups(self) -> None:
        """
        Create group and add standard users by accountId.
        """
        print(f"🔧 Creating/ensuring group '{self.group_name}' exists...")
        try:
            grp_resp = self.client.create_group(self.group_name)
            if isinstance(grp_resp, dict) and grp_resp.get('status') == 409:
                print(f"  ⚠️ Group '{self.group_name}' already exists (server returned 409). Continuing.")
            else:
                print(f"  ✅ Group '{self.group_name}' created or acknowledged by API.")
        except Exception as e:
            print(f"  ⚠️ Could not create group (maybe exists): {e}")

        # Add standard (non-admin) users to the group
        standard_users = [u for u in self.users.values() if not u.get('isAdmin')]
        if not standard_users:
            print("  ⚠️ No standard users found to add to group.")
            return

        for user in standard_users:
            email = user['email']
            account_id = user['accountId']
            try:
                print(f"  ➕ Adding {email} (accountId={account_id}) to group {self.group_name} ...")
                self.client.add_user_to_group_by_name(self.group_name, account_id)
                print(f"  ✅ Added {email} to group.")
                time.sleep(0.5)
            except Exception as e:
                txt = str(e)
                if '409' in txt or 'already exists' in txt.lower():
                    print(f"  ⚠️ {email} already in group (or conflict).")
                else:
                    print(f"  ❌ Failed to add {email} to group: {e}")

        print("✅ Group setup done.")

    # small helper to add a single operation (ensures single "operation" payload)
    def _add_single_operation_permission(self, space_key: str, account_id: str, op: Dict[str, str], subject_type: str = "user") -> bool:
        """
        Add one operation permission for subject_type:identifier.
        Returns True on success, False if permission already existed (or error handled).
        """
        try:
            # client.add_space_permission expects a list; using single-item list ensures "operation" JSON is used.
            self.client.add_space_permission(space_key, subject_type, account_id, [op])
            print(f"    ✅ Granted {op.get('key')}({op.get('target')}) to {account_id} on {space_key}")
            return True
        except Exception as e:
            txt = str(e)
            # handle "Permission already exists" and other readable messages gracefully
            if 'Permission already exists' in txt or 'already exists' in txt:
                print(f"    ⚠️ Permission already exists for {account_id} ({op.get('key')}). Skipping.")
                return False
            # surface read-before-other hint separately upstream
            print(f"    ❌ Failed to grant {op.get('key')} to {account_id} on {space_key}: {e}")
            return False

    def setup_spaces(self) -> None:
        """
        Create COLLAB and RESTRICT spaces (idempotent) and apply permissions:

        - COLLAB:
            * one standard user -> space administrator
            * other 3 standard users -> read + write/create
            * site admin keeps default (no change)
        - RESTRICT:
            * site admin -> space administrator
            * all 4 standard users -> read-only
        """
        print("🔧 Creating spaces (COLLAB, RESTRICT)...")
        space_configs = [
            {'key': 'COLLAB', 'name': 'Collaborative Workspace', 'description': 'Open collaborative workspace for team projects'},
            {'key': 'RESTRICT', 'name': 'Restricted Workspace', 'description': 'Highly restricted workspace for sensitive information'}
        ]

        for cfg in space_configs:
            key = cfg['key']
            try:
                print(f"  ➕ Creating space {key} ...")
                space = self.client.create_space(space_key=key, name=cfg['name'], description=cfg['description'])
                self.spaces[key] = space
                print(f"  ✅ Space {key} created.")
            except Exception as e:
                msg = str(e)
                print(f"  ℹ️ Could not create space {key} (may exist or validation failed): {msg}")
                # Try to find an existing space by listing spaces (fallback)
                try:
                    print("    🔎 Searching existing spaces for a match...")
                    resp = self.client._make_request('GET', '/rest/api/space?limit=200')
                    results = resp.get('results') if isinstance(resp, dict) else None
                    found = None
                    if isinstance(results, list):
                        for s in results:
                            sk = (s.get('key') or '').upper()
                            if sk == key.upper():
                                found = s
                                break
                            if (s.get('name') or '').lower() == (cfg['name'] or '').lower():
                                found = s
                                break
                    if found:
                        self.spaces[key] = found
                        print(f"    ✅ Found existing space for {key} (using discovered space).")
                    else:
                        print(f"    ⚠️ No matching space found in list for key={key}; continuing.")
                except Exception as ex:
                    print(f"    ❌ Failed to list/search spaces: {ex}")
            time.sleep(0.5)

        # --- Apply permissions per spec ---
        standard_users = [u for u in self.users.values() if not u.get('isAdmin')]
        admin_user = next((u for u in self.users.values() if u.get('isAdmin')), None)

        if not admin_user:
            print("  ❌ No admin user available in mapping — cannot safely apply restrictive permissions.")
        if len(standard_users) < 1:
            print("  ❌ No standard users found — skipping permission assignments.")
        else:
            # Helper that ensures read exists first, then applies additional ops safely
            def ensure_read_then_apply(space_key: str, subject_account: str, extra_ops: List[Dict[str, str]], subject_type: str = "user"):
                # 1) ensure read
                try:
                    # add read (single op)
                    read_op = {"key": "read", "target": "space"}
                    if self._add_single_operation_permission(space_key, subject_account, read_op, subject_type):
                        # read added now; continue with extra ops
                        for op in extra_ops:
                            # call single-operation-per-request to avoid server NPEs
                            self._add_single_operation_permission(space_key, subject_account, op, subject_type)
                    else:
                        # read already existed or failed; still attempt extra ops but continue
                        for op in extra_ops:
                            self._add_single_operation_permission(space_key, subject_account, op, subject_type)
                except Exception as e:
                    print(f"    ❌ Error while ensuring read/extra ops for {subject_account} on {space_key}: {e}")

            # COLLAB: pick first standard user as space admin, others as writers/readers
            if 'COLLAB' in self.spaces:
                collab_key = 'COLLAB'
                space_admin = standard_users[0]
                writers = standard_users[1:] if len(standard_users) > 1 else []
                # ensure admin has read first, then administer
                try:
                    print(f"  ➕ Granting space-admin on {collab_key} to {space_admin['email']}")
                    ensure_read_then_apply(collab_key, space_admin['accountId'], [{"key": "administer", "target": "space"}])
                except Exception as e:
                    print(f"    ❌ Failed to grant space admin: {e}")

                # writers: give write + read (we ensure read first in helper)
                for w in writers:
                    try:
                        print(f"  ➕ Granting write/read on {collab_key} to {w['email']}")
                        write_ops = [
                            {"key": "create", "target": "page"},
                            {"key": "create", "target": "blogpost"},
                            {"key": "create", "target": "comment"},
                            {"key": "create", "target": "attachment"},
                            {"key": "delete", "target": "page"}
                        ]
                        ensure_read_then_apply(collab_key, w['accountId'], write_ops)
                    except Exception as e:
                        print(f"    ❌ Failed to grant write/read to {w['email']}: {e}")

            # RESTRICT: only admin is space admin, all standard users get read-only
            if 'RESTRICT' in self.spaces and admin_user:
                restrict_key = 'RESTRICT'
                try:
                    print(f"  ➕ Granting space-admin on {restrict_key} to site admin {admin_user['email']}")
                    ensure_read_then_apply(restrict_key, admin_user['accountId'], [{"key": "administer", "target": "space"}])
                except Exception as e:
                    print(f"    ❌ Failed to grant admin to site admin: {e}")

                for u in standard_users:
                    try:
                        print(f"  ➕ Granting read-only on {restrict_key} to {u['email']}")
                        # only read
                        self._add_single_operation_permission(restrict_key, u['accountId'], {"key": "read", "target": "space"})
                    except Exception as e:
                        print(f"    ❌ Failed to grant read to {u['email']}: {e}")

        print("⚠️ Note: This script applies basic space permissions but does not remove older/extra permissions.")

    def setup_content(self) -> None:
        """
        Create a page in COLLAB and restrict it (read) to admin + one standard user.
        """
        print("🔧 Creating content in COLLAB...")
        if 'COLLAB' not in self.spaces:
            print("  ❌ COLLAB space not present — skipping content creation.")
            return

        title = "Project Kickoff: Collaboration Page"
        html = '''
        <h1>Project Kickoff</h1>
        <p>Welcome to the collaborative workspace for our new project. Here you'll find all the resources and updates you need.</p>
        <h2>Team Goals</h2>
        <ul>
            <li>Foster open communication</li>
            <li>Share progress transparently</li>
            <li>Encourage innovation</li>
        </ul>
        <h2>Embedded Image</h2>
        <p><img src="https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png" alt="Demo Image" width="300" /></p>
        '''

        try:
            page = self.client.create_page(space_key='COLLAB', title=title, content=html)
            self.content[title] = page
            content_id = page.get('id')
            print(f"  ✅ Page created: '{title}' id={content_id}")
        except Exception as e:
            print(f"  ❌ Failed to create page: {e}")
            return

        # Choose a standard user to grant access to (first non-admin), and ensure admin remains
        standard_users = [u for u in self.users.values() if not u.get('isAdmin')]
        admin_user = next((u for u in self.users.values() if u.get('isAdmin')), None)
        if not standard_users:
            print("  ⚠️ No standard users to pick for restriction. Skipping restrictions.")
            return
        if not admin_user:
            print("  ⚠️ No admin user available in mapping — skipping restrictions to avoid evicting caller.")
            return

        target = standard_users[0]
        try:
            print(f"  🔒 Applying read restriction for admin ({admin_user['email']})")
            self.client.add_content_restriction(content_id=content_id, operation='read', account_id=admin_user['accountId'])
            time.sleep(0.3)
            print(f"  🔒 Applying read restriction for target user ({target['email']})")
            self.client.add_content_restriction(content_id=content_id, operation='read', account_id=target['accountId'])
            print(f"  ✅ Content restricted to: {admin_user['email']} and {target['email']}")
        except Exception as e:
            print(f"  ❌ Failed to apply content restriction: {e}")

    def run_setup(self) -> None:
        print("🚀 Starting Confluence minimal setup")
        print("=" * 50)
        try:
            self.setup_users()
            print()
            self.setup_groups()
            print()
            self.setup_spaces()
            print()
            self.setup_content()
            print()
            print("🎉 Setup finished. Summary:")
            print(f"  - Users loaded: {len(self.users)}")
            print(f"  - Group: {self.group_name}")
            print(f"  - Spaces: {list(self.spaces.keys())}")
            print(f"  - Content: {list(self.content.keys())}")
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise


def main():
    try:
        s = ConfluenceSetup()
        s.run_setup()
    except Exception as e:
        print(f"❌ Application failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
