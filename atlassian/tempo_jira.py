import atlassian.tempo_jira
from atlassian.tempo import client_v4
from datetime import timedelta, date, datetime
import json


class Tempo:
    _tempo: client_v4.Tempo
    _project: str
    _teams: list[str]
    _url_server: str
    _fields_change_ignored: list[str]
    _type_base: list[str]
    _path_data: str
    _epic_fields: dict
    _fields: dict
    _super: dict
    _board_id: int
    _trc: bool = False
    _tempo_exclude: str
    _tempo_replace: dict

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, '_' + key, value)

    def conn(self) -> 'atlassian.tempo_jira.Tempo':
        self._tempo = client_v4.Tempo(base_url=self._url_server+'rest/tempo-planning/1', auth_token=self._token_auth)
        return self

    def planned(self, start_date: str, date_to: str,
                frm: str = '%Y-%m-%d', file: bool = True) -> 'atlassian.tempo_jira.Tempo':
        # https://www.tempo.io/server-api-documentation/planner#tag/Allocation/operation/getAllocations
        teams_datas = {team: {} for team in self._teams}
        plan = {}
        self.tempo_teams(start_date, teams_datas)
        members_used = []
        for team, members in teams_datas.items():
            for member, values in members.items():
                if member not in members_used:
                    end_date_member = date_to if 'dateToANSI' not in values else values['dateToANSI']
                    if end_date_member >= start_date:
                        plan[member] = {}
                        members_used.append(member)
                        self._tempo._base_url = self._url_server + 'rest/tempo-planning/1'

                        worklogs = self._tempo.get_allocation(
                            startDate=start_date,
                            endDate=end_date_member,
                            assigneeKeys=member
                        )

                        for i in worklogs:
                            if 'assignee' in i and not i['planItem']['summary'].startswith(self._tempo_exclude):
                                start = i['start']
                                end = i['end']
                                d = date.fromisoformat(max((start, start_date)))
                                end_date = date.fromisoformat(min((end, date_to)))
                                while d <= end_date:
                                    if d.strftime(frm) not in plan[member]:
                                        plan[member][d.strftime(frm)] = {}
                                    plan_date = plan[member][d.strftime(frm)]
                                    key = i['planItem']['key']
                                    if key in plan_date:
                                        plan_date[key]['secondsPerDay'] += i['secondsPerDay']
                                    else:
                                        summary = i['planItem']['summary']
                                        for old, new in self._tempo_replace.items():
                                            summary = summary.replace(old, new)
                                        plan_date[key] = {'summary': summary, 'secondsPerDay': i['secondsPerDay']}
                                    d += timedelta(days=1)
        now = datetime.now().strftime('%Y%m%d')
        end_file = f"{start_date.replace('-', '')}_{date_to.replace('-', '')}_{now}.json"
        if file:
            with open(f"{self._path_data}plan{end_file}", 'w', encoding='utf-8') as f:
                json.dump(plan, f, indent=2)
            with open(f"{self._path_data}teams{end_file}", 'w', encoding='utf-8') as f:
                json.dump(teams_datas, f, indent=2)
        return self

    def tempo_teams(self, start_date, teams) -> 'atlassian.tempo_jira.Tempo':
        for team, members in teams.items():
            self._tempo._base_url = f'{self._url_server}rest/tempo-teams/2'
            teams_info = self._tempo.get_team_members(team)
            for team_info in teams_info:
                member = {'role': team_info['membership']['role']['name']}
                if ('dateToANSI' not in team_info['membership']
                        or not team_info['membership']['dateToANSI']
                        or team_info['membership']['dateToANSI'] <= start_date):
                    if 'dateFromANSI' in team_info['membership'] and team_info['membership']['dateFromANSI']:
                        member['dateFromANSI'] = team_info['membership']['dateFromANSI']
                    if 'dateToANSI' in team_info['membership'] and team_info['membership']['dateToANSI']:
                        member['dateToANSI'] = team_info['membership']['dateToANSI']
                members[team_info['member']['name']] = member
        return self
