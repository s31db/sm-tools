# Repris de https://github.com/stanislavulrych/tempo-api-python-client
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import unicode_literals

from datetime import date, datetime

from .rest_client import RestAPIClient


class Tempo(RestAPIClient):
    """
    Basic Client for accessing Tempo Rest API as provided by api.tempo.io.
    """

    def __init__(self, auth_token, base_url="https://api.tempo.io/4", limit=5000):
        self._limit = limit   # default limit for pagination (1000 is maximum for Tempo API)
        self._base_url = base_url
        super().__init__(auth_token=auth_token)

    @staticmethod
    def _resolve_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        parsed = datetime.strptime(value,  r"%Y-%m-%d").date()
        return parsed

    def get(self, path, data=None, flags=None, params=None, headers=None, not_json_response=None, trailing=None):
        path_absolute = super().url_joiner(self._base_url, path)
        resp = super().get(path_absolute, data=data, flags=flags, params=params, headers=headers,
                           not_json_response=not_json_response, trailing=trailing)

        # single item returned
        if 'results' not in resp:
            return resp

        # multiple items
        results = resp['results']

        # handle all results paginated
        while 'next' in resp.get('metadata'):
            resp = super().get(resp.get('metadata').get('next'))
            results.extend(resp['results'])

        return results

    def post(self, path, data=None, params=None, headers=None, not_json_response=None, trailing=None):
        path_absolute = super().url_joiner(self._base_url, path)
        return super().post(path_absolute, data=data, params=params, headers=headers, trailing=trailing)

    def put(self, path, data=None, params=None, headers=None, not_json_response=None, trailing=None):
        path_absolute = super().url_joiner(self._base_url, path)
        return super().put(path_absolute, data=data, params=params, headers=headers, trailing=trailing)

    def delete(self, path, data=None, params=None, headers=None, not_json_response=None, trailing=None):
        path_absolute = super().url_joiner(self._base_url, path)
        return super().delete(path_absolute, headers=headers, trailing=trailing)

# Accounts

    def get_accounts(self):
        """
        Retrieves existing accounts.
        """
        return self.get("/accounts")

    # Account - Categories
    def get_account_categories(self):
        """
        Retrieves existing account categories.
        """
        return self.get("/account-categories")

    # Account - Category - Types
    def get_account_category_types(self):
        """
        Retrieves all periods for a given date range as a list.
        """
        return self.get("/account-category-types")

    # Account - Links
    ## TBD

    # Customers
    def get_customers(self, key=None):
        """
        Retrieves all customers or customer.
        :param key: Return customer for ```key```.
        """

        url = "/customers"
        if key:
            url += f"/{key}"
        return self.get(url)

    # Plans
    def get_plans(self, date_from=None, date_to=None, plan_id=None, account_id=None, account_ids=None,
                  assignee_types=None, generic_resource_id=None, generic_resource_ids=None, plan_ids=None,
                  plan_item_ids=None, plan_item_types=None, planned_time_breakdown=None, updated_from=None):
        """
        Retrieves a list of existing Plans that matches the given search parameters.
        :param date_from:
        :param date_to:
        :param plan_id: ~~~ retrieve plan ~~~
        :param account_id: ~~~ retrieve plans for user ~~~
        :param account_ids: ~~~ search plans ~~~
        :param assignee_types: ~~~ search plans ~~~
        :param generic_resource_id: ~~~ retrieve plans for generic resource ~~~
        :param generic_resource_ids: ~~~ search plans ~~~
        :param plan_ids: ~~~ search plans ~~~
        :param plan_item_ids: ~~~ search plans ~~~
        :param plan_item_types: ~~~ search plans ~~~
        :param planned_time_breakdown: ~~~ search plans ~~~
        :param updated_from: ~~~ retrieve plans for user / retrieve plans for generic resource / search plans ~~~
        """
        
        if plan_id:
            url = f"plans/{plan_id}"
            return self.get(url)
        elif account_id:
            url = f"/plans/user/{account_id}"
            params = {
                "offset": 0,
                "limit": self._limit
            }
            if planned_time_breakdown:
                params['plannedTimeBreakdown'] = planned_time_breakdown
            if date_from:
                params['from'] = self._resolve_date(date_from).isoformat()
            if date_to:
                params['to'] = self._resolve_date(date_to).isoformat()
            if updated_from:
                params['updatedFrom'] = self._resolve_date(updated_from).isoformat()

            return self.get(url, params=params)
        elif generic_resource_id:
            url = f"/plans/generic-resource/{generic_resource_id}"
            params = {
                "offset": 0,
                "limit": self._limit
            }
            if planned_time_breakdown:
                params['plannedTimeBreakdown'] = planned_time_breakdown
            if date_from:
                params['from'] = self._resolve_date(date_from).isoformat()
            if date_to:
                params['to'] = self._resolve_date(date_to).isoformat()
            if updated_from:
                params['updatedFrom'] = self._resolve_date(updated_from).isoformat()

            return self.get(url, params=params)
        elif date_from and date_to:
            data = {
                "from": self._resolve_date(date_from).isoformat(),
                "to": self._resolve_date(date_to).isoformat(),
                "offset": 0,
                "limit": self._limit
            }    
            if account_ids:
                data['accountIds'] = account_ids
            if assignee_types:
                data['assigneeTypes'] = assignee_types
            if generic_resource_ids:
                data['genericResourceIds'] = generic_resource_ids
            if plan_ids:
                data['planIds'] = plan_ids
            if plan_item_ids:
                data['planItemIds'] = plan_item_ids
            if plan_item_types:
                data['planItemTypes'] = plan_item_types
            if planned_time_breakdown:
                data['plannedTimeBreakdown'] = planned_time_breakdown
            if updated_from:
                data['updatedFrom'] = self._resolve_date(updated_from).isoformat()
            url = "/plans/search"
            return self.post(url, data=data)

    def get_plan(self, plan_id):
        return self.get_plans(plan_id=plan_id)
    
    def get_plan_for_user(self, account_id, planned_time_breakdown=None, date_from=None, date_to=None,
                          updated_from=None):
        return self.get_plans(account_id=account_id, planned_time_breakdown=planned_time_breakdown,
                              date_from=date_from, date_to=date_to, updated_from=updated_from)
    
    def get_plan_for_resource(self, generic_resource_id, planned_time_breakdown=None, date_from=None, date_to=None,
                              updated_from=None):
        return self.get_plans(generic_resource_id=generic_resource_id, planned_time_breakdown=planned_time_breakdown,
                              date_from=date_from, date_to=date_to, updated_from=updated_from)
    
    def search_plans(self, date_from, date_to, account_ids=None, assignee_types=None, generic_resource_ids=None,
                     plan_ids=None, plan_item_ids=None, plan_item_types=None, planned_time_breakdown=None,
                     updated_from=None):
        return self.get_plans(date_from=date_from, date_to=date_to, account_ids=account_ids,
                              assignee_types=assignee_types, generic_resource_ids=generic_resource_ids,
                              plan_ids=plan_ids, plan_item_ids=plan_item_ids, plan_item_types=plan_item_types,
                              planned_time_breakdown=planned_time_breakdown, updated_from=updated_from)

    def create_plan(self, assignee_id, assignee_type, start_date, end_date, plan_item_id, plan_item_type,
                    planned_seconds_per_day, description=None, include_non_working_days=None,
                    plan_approval_reviewer_id=None, plan_approval_status=None, recurrence_end_date=None, rule=None):
        """
        :param assignee_id:
        :param assignee_type:
        :param start_date:
        :param end_date:
        :param plan_item_id:
        :param plan_item_type:
        :param planned_seconds_per_day:
        :param description:
        :param include_non_working_days:
        :param plan_approval_reviewer_id:
        :param plan_approval_status:
        :param recurrence_end_date:
        :param rule:
        """
        data = self.prepare_data(assignee_id, assignee_type, description, end_date, include_non_working_days,
                                 plan_approval_reviewer_id, plan_approval_status, plan_item_id, plan_item_type,
                                 planned_seconds_per_day, recurrence_end_date, rule, start_date)

        url = "/plans"
        return self.post(url, data=data)
        
    def update_plan(self, plan_id, assignee_id, assignee_type, start_date, end_date, plan_item_id, plan_item_type,
                    planned_seconds_per_day, description=None, include_non_working_days=None,
                    plan_approval_reviewer_id=None, plan_approval_status=None, recurrence_end_date=None, rule=None):
        """
        :param plan_id:
        :param assignee_id:
        :param assignee_type:
        :param start_date:
        :param end_date:
        :param plan_item_id:
        :param plan_item_type:
        :param planned_seconds_per_day:
        :param description:
        :param include_non_working_days:
        :param plan_approval_reviewer_id:
        :param plan_approval_status:
        :param recurrence_end_date:
        :param rule:
        """
        data = self.prepare_data(assignee_id, assignee_type, description, end_date, include_non_working_days,
                                 plan_approval_reviewer_id, plan_approval_status, plan_item_id, plan_item_type,
                                 planned_seconds_per_day, recurrence_end_date, rule, start_date)

        url = f"/plans/{plan_id}"
        return self.put(url, data=data)

    def prepare_data(self, assignee_id, assignee_type, description, end_date, include_non_working_days,
                     plan_approval_reviewer_id, plan_approval_status, plan_item_id, plan_item_type,
                     planned_seconds_per_day, recurrence_end_date, rule, start_date):
        data = {
            "assigneeId": assignee_id,
            "assigneeType": assignee_type,  # Enum: "USER" "GENERIC"
            "startDate": self._resolve_date(start_date).isoformat(),
            "endDate": self._resolve_date(end_date).isoformat(),
            "planItemId": plan_item_id,
            "planItemType": plan_item_type,  # Enum: "ISSUE" "PROJECT"
            "plannedSecondsPerDay": planned_seconds_per_day
        }
        if description:
            data['description'] = description
        if include_non_working_days:
            data['includeNonWorkingDays'] = include_non_working_days
        if plan_approval_reviewer_id:
            if not plan_approval_status:
                data['planApproval'] = {
                    "reviewerId": plan_approval_reviewer_id,
                    "status": "REQUESTED"
                }
            else:
                data['planApproval'] = {
                    "reviewerId": plan_approval_reviewer_id,
                    "status": plan_approval_status  # Enum: "APPROVED" "REJECTED" "REQUESTED"
                }
        if recurrence_end_date:
            data['recurrenceEndDate'] = recurrence_end_date
        if rule:
            data['rule'] = rule  # Enum: "NEVER" "WEEKLY" "BI_WEEKLY" "MONTHLY"
        return data

    def delete_plan(self, id):
        url = f"/plans/{id}"
        return self.delete(url)
       
    # Programs

    # Roles

    # Teams
    def get_teams(self, team_id=None):
        """
        Returns teams information.
        :param team_id: Returns details for team ```team_id```.
        """

        url = 'teams'
        if team_id:
            url = f"/team/{team_id}"

        return self.get(url)

    def get_team_members(self, teamId):
        """
        Returns members for particular team.
        :param teamId: teamId
        """

        url = f"/teams/{teamId}/members"
        return self.get(url)

    # Team - Links

    # Team - Memberships
    def get_team_memberships(self, team_id):
        """
        Returns members.
        :param team_id:
        """

        url = f"/team-memberships/team/{team_id}"
        return self.get(url)

    def get_account_team_membership(self, team_id, account_id):
        """
        Returns the active team membership.
        :param account_id:
        :param team_id:
        """

        return self.get(f"/teams/{team_id}/members/{account_id}")

    def get_account_team_memberships(self, team_id, account_id):
        """
        Returns all team memberships.
        :param account_id:
        :param team_id:
        """

        return self.get(f"/teams/{team_id}/members/{account_id}/memberships")

# Periods

    def get_periods(self, date_from, date_to):
        """
        Retrieves periods.
        :param date_from:
        :param date_to:
        """

        params = {
            "from": self._resolve_date(date_from).isoformat(),
            "to": self._resolve_date(date_to).isoformat()
            }

        return self.get("/periods", params=params)

# Timesheet Approvals

    def get_timesheet_approvals_waiting(self):
        """
        Retrieve waiting timesheet approvals
        """

        return self.get("/timesheet-approvals/waiting")

    def get_timesheet_approvals(self, date_from=None, date_to=None, user_id=None, team_id=None):
        """
        Retrieves timesheet approvals.
        :param date_from:
        :param date_to:
        :param user_id:
        :param team_id:
        """
        params = {}
        if date_from:
            params["from"] = self._resolve_date(date_from).isoformat()
        if date_to:
            params["to"] = self._resolve_date(date_to).isoformat()

        url = "/timesheet-approvals"
        if user_id:
            url += f"/user/{user_id}"
        elif team_id:
            url += f"/team/{team_id}"
        return self.get(url, params=params)

    # User Schedule
    def get_user_schedule(self, date_from, date_to, user_id=None):
        """
        Returns user schedule.
        :param date_from:
        :param date_to:
        :param user_id:
        """

        params = {
            "from": self._resolve_date(date_from).isoformat(),
            "to": self._resolve_date(date_to).isoformat()
            }
        url = "/user-schedule"
        if user_id:
            url += f"/{user_id}"
        return self.get(url, params=params)

    # Work Attributes
    def get_work_attributes(self):
        """
        Returns worklog attributes.
        """
        return self.get("/work-attributes")

    # Workload Schemes
    def get_workload_schemes(self, workload_schemes_id=None):
        url = "/workload-schemes"
        if workload_schemes_id:
            url += f"/{workload_schemes_id}"
        return self.get(url)

# Holiday Schemes

    def get_holiday_schemes(self, holiday_scheme_id=None, year=None):
        """
        Retrieve holidays for an existing holiday scheme.
        :param holiday_scheme_id:
        :param year:
        """
        url = "/holiday-schemes"
        if holiday_scheme_id:
            url += f"/{holiday_scheme_id}/holidays"

        params = {}

        if year:
            params["year"] = year

        return self.get(url, params=params)

    def create_holiday_scheme(self, scheme_name, scheme_description=None):
        """
        Create holiday scheme
        :param scheme_name:
        :param scheme_description:
        """

        url = "/holiday-schemes"

        data = {"name": scheme_name, "description": scheme_description}

        return self.post(url, data=data)

    def create_holiday(self, holiday_scheme_id, type_data=None, name=None, description=None,
                       duration_seconds=None, date_holiday=None, data=None):
        """
        Create holiday scheme
        :param data: 
        :param date_holiday: 
        :param duration_seconds: 
        :param holiday_scheme_id:
        :param type_data:
        :param name:
        :param description:
        """

        # either provide data, or build from other params
        if not data:
            data = {
                "type": type_data,
                "name": name,
                "description": description,
                "durationSeconds": duration_seconds,
                "date": date_holiday
          }

        url = f"/holiday-schemes/{holiday_scheme_id}/holidays"

        return self.post(url, data=data)

# Worklogs

    def get_worklogs(self, date_from, date_to, updated_from=None, worklog_id=None, jira_worklog_id=None,
                     jira_filter_id=None, account_key=None, project_id=None, team_id=None, account_id=None,
                     issue_id=None):
        """
        Returns worklogs for particular parameters.
        :param issue_id:
        :param date_from:
        :param date_to:
        :param updated_from:
        :param worklog_id:
        :param jira_worklog_id:
        :param jira_filter_id:
        :param account_key:
        :param project_id:
        :param team_id:
        :param account_id:
        :param issue:
        """

        params = {
            "from": self._resolve_date(date_from).isoformat(),
            "to": self._resolve_date(date_to).isoformat(),
            "offset": 0,
            "limit": self._limit
            }

        if project_id:
            params['projectId'] = project_id

        if updated_from:
            params["updatedFrom"] = self._resolve_date(updated_from).isoformat()

        url = "/worklogs"
        if worklog_id:
            url += f"/{worklog_id}"
        elif jira_worklog_id:
            url += f"/jira/{jira_worklog_id}"
        elif jira_filter_id:
            url += f"/jira/filter/{jira_filter_id}"
        elif account_key:
            url += f"/account/{account_key}"
        elif team_id:
            url += f"/team/{team_id}"
        elif account_id:
            url += f"/user/{account_id}"
        elif issue_id:
            url += f"/issue/{issue_id}"

        return self.get(url, params=params)

    def search_worklogs(self, date_from, date_to, updated_from=None, author_ids=None, issue_ids=None, project_ids=None,
                        offset=None, limit=None):
        """
        Retrieves a list of existing Worklogs that matches the given search parameter.
        :param project_ids:
        :param issue_ids:
        :param author_ids:
        :param updated_from:
        :param date_to:
        :param date_from:
        :param offset:
        :param limit:
        """

        params = {
            "offset": 0 if offset is None else offset,
            "limit": self._limit if limit is None else limit
        }

        data = {
            "from": self._resolve_date(date_from).isoformat(),
            "to": self._resolve_date(date_to).isoformat()
        }

        if updated_from:
            data["updatedFrom"] = updated_from
        if author_ids:
            data["authorIds"] = author_ids
        if issue_ids:
            data["issueIds"] = issue_ids
        if project_ids:
            data["projectIds"] = project_ids

        url = "/worklogs/search"

        return self.post(url, params=params, data=data)

    def get_allocation(self, **params):
        url = "/allocation"
        return self.get(url, params=params)
