"""
Confluence Cloud REST API Client (final)

- Robust URL normalization so CONFLUENCE_URL can include or omit '/wiki'
- Correct endpoints for group member addition (groupId-based)
- Convenience helpers for group lookups & member addition
- Space permission helpers (add user admin/read/write)
- Basic content & restriction helpers
"""

import os
import time
from typing import Any, Dict, Optional, List

import requests
from dotenv import load_dotenv

load_dotenv()


class ConfluenceClient:
    def __init__(self, base_url: str = None, email: str = None, api_token: str = None):
        self.base_url = base_url or os.getenv('CONFLUENCE_URL')
        self.email = email or os.getenv('CONFLUENCE_EMAIL')
        self.api_token = api_token or os.getenv('CONFLUENCE_API_TOKEN')

        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Missing CONFLUENCE_URL, CONFLUENCE_EMAIL or CONFLUENCE_API_TOKEN in environment.")

        # ensure no trailing slash on base
        self.base_url = self.base_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (self.email, self.api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    # ----------------------------
    # HTTP helper
    # ----------------------------
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Robust request wrapper that handles CONFLUENCE_URL with or without '/wiki'.

        - endpoint may be '/rest/api/...' or '/wiki/rest/api/...' or '/...'
        - normalizes to base_api + '/rest/api/...' where base_api contains exactly one '/wiki'
        """
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint

        base = self.base_url.rstrip('/')
        if base.endswith('/wiki'):
            base_api = base
        else:
            base_api = base + '/wiki'

        ep = endpoint
        if ep.startswith('/wiki/rest/api/'):
            ep = ep[len('/wiki'):]  # drop leading /wiki

        if not ep.startswith('/rest/api/'):
            ep = '/rest/api' + ep

        url = base_api + ep  # final normalized URL

        try:
            resp = self.session.request(method, url, timeout=30, **kwargs)
            resp.raise_for_status()
            if resp.content:
                try:
                    return resp.json()
                except ValueError:
                    return resp.text
            return {}
        except requests.exceptions.RequestException as e:
            msg = f"API request failed: {method} {url} -> {e}"
            if hasattr(e, 'response') and e.response is not None:
                msg += f"\nResponse status: {e.response.status_code}, body: {e.response.text}"
            raise type(e)(msg) from e

    # ----------------------------
    # Group APIs
    # ----------------------------
    def create_group(self, group_name: str) -> Dict[str, Any]:
        """Create a new group. If group already exists, return a dict indicating that."""
        data = {"name": group_name}
        try:
            return self._make_request('POST', '/rest/api/group', json=data)
        except Exception as e:
            txt = str(e)
            if '409' in txt or 'Conflict' in txt or 'Group already exists' in txt:
                return {"status": 409, "error": "Group already exists"}
            raise

    def get_group_id(self, group_name: str) -> Optional[str]:
        """
        Lookup group by name using the 'group/picker' endpoint and return its id.
        """
        try:
            resp = self._make_request('GET', f'/rest/api/group/picker?query={group_name}&limit=50')
            results = resp.get('results') if isinstance(resp, dict) else None
            if isinstance(results, list):
                for g in results:
                    if g.get('name') == group_name:
                        return g.get('id') or g.get('key') or g.get('name')
            # Fallback: direct lookup
            try:
                resp2 = self._make_request('GET', f'/rest/api/group?groupname={group_name}')
                if isinstance(resp2, dict) and resp2.get('name') == group_name:
                    return resp2.get('id')
            except Exception:
                pass
        except Exception:
            pass
        return None

    def add_user_to_group_by_groupid(self, group_id: str, account_id: str) -> Dict[str, Any]:
        """
        Add a user to a group using the groupId-based endpoint:
        POST /rest/api/group/userByGroupId?groupId={groupId}
        Body: {"accountId": "<id>"}
        """
        endpoint = f'/rest/api/group/userByGroupId?groupId={group_id}'
        body = {'accountId': account_id}
        return self._make_request('POST', endpoint, json=body)

    def add_user_to_group_by_name(self, group_name: str, account_id: str) -> Dict[str, Any]:
        """
        Resolve group name -> groupId and add user. Raises if group not found.
        """
        group_id = self.get_group_id(group_name)
        if not group_id:
            raise ValueError(f"Group '{group_name}' not found (cannot add user).")
        return self.add_user_to_group_by_groupid(group_id, account_id)

    # ----------------------------
    # Space APIs
    # ----------------------------
    def create_space(self, space_key: str, name: str, description: str = "") -> Dict[str, Any]:
        data = {
            'key': space_key,
            'name': name,
            'description': {'value': description, 'representation': 'storage'}
        }
        return self._make_request('POST', '/rest/api/space', json=data)

    def get_space(self, space_key: str) -> Dict[str, Any]:
        return self._make_request('GET', f'/rest/api/space/{space_key}')

    # ----------------------------
    # Space permission APIs
    # ----------------------------
    # def add_space_permission(self, space_key: str, subject_type: str, identifier: str, operations: List[Dict[str, str]]) -> Dict[str, Any]:
    #     """
    #     Add a permission to a space.

    #     subject_type: 'user' | 'group' | 'anonymous'
    #     identifier: for user -> accountId, for group -> group name or id
    #     operations: list of operation objects, e.g. [{"key": "administer", "target": "space"}]
    #     """
    #     body = {
    #         "subject": {"type": subject_type, "identifier": identifier},
    #         "operations": operations
    #     }
    #     endpoint = f'/rest/api/space/{space_key}/permission'
    #     return self._make_request('POST', endpoint, json=body)
    def add_space_permission(self, space_key: str, subject_type: str, identifier: str, operations: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Add a permission to a space.

        subject_type: 'user' | 'group' | 'anonymous'
        identifier: for user -> accountId, for group -> group name/id
        operations: list of operation objects, e.g. [{"key":"administer","target":"space"}]

        Note: Confluence's REST parser expects a single operation under "operation": {...}
        when only one operation is provided. When given multiple, we send "operations": [...]
        but many Cloud installations work best with "operation" for single-item requests.
        """
        if not isinstance(operations, list) or len(operations) == 0:
            raise ValueError("operations must be a non-empty list")

        # For a single operation use "operation" (object). For >1 use "operations".
        if len(operations) == 1:
            body = {
                "subject": {"type": subject_type, "identifier": identifier},
                "operation": operations[0]
            }
        else:
            body = {
                "subject": {"type": subject_type, "identifier": identifier},
                "operations": operations
            }

        endpoint = f'/rest/api/space/{space_key}/permission'
        try:
            return self._make_request('POST', endpoint, json=body)
        except Exception as e:
            # surface helpful debug for callers
            txt = str(e)
            raise RuntimeError(f"Failed to add space permission (space={space_key}, subject={subject_type}:{identifier}) -> {txt}") from e

    def add_user_space_admin(self, space_key: str, account_id: str) -> Dict[str, Any]:
        """Grant space-level administer permission to a user (accountId)."""
        ops = [{"key": "administer", "target": "space"}]
        return self.add_space_permission(space_key, "user", account_id, ops)

    def add_user_space_read(self, space_key: str, account_id: str) -> Dict[str, Any]:
        """Grant read permission to a user (accountId)."""
        ops = [{"key": "read", "target": "space"}]
        return self.add_space_permission(space_key, "user", account_id, ops)

    def add_user_space_write(self, space_key: str, account_id: str) -> Dict[str, Any]:
        """
        Give a user the ability to create content in the space.
        Grants create targets (page/blogpost/comment/attachment) and optionally delete page.
        """
        ops = [
            {"key": "create", "target": "page"},
            {"key": "create", "target": "blogpost"},
            {"key": "create", "target": "comment"},
            {"key": "create", "target": "attachment"},
            {"key": "delete", "target": "page"}
        ]
        return self.add_space_permission(space_key, "user", account_id, ops)

    # ----------------------------
    # Content APIs
    # ----------------------------
    def create_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
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

    def get_content(self, content_id: str) -> Dict[str, Any]:
        return self._make_request('GET', f'/rest/api/content/{content_id}')

    def add_content_restriction(self, content_id: str, operation: str, account_id: str) -> Any:
        """
        Add a user-based restriction for a specific operation on content.

        Uses:
          PUT /rest/api/content/{id}/restriction/byOperation/{operation}/user?accountId=<accountId>

        operation: 'read' or 'update'
        """
        endpoint = f'/rest/api/content/{content_id}/restriction/byOperation/{operation}/user'
        params = {'accountId': account_id}
        return self._make_request('PUT', endpoint, params=params)
