"""This module implements a block to select valid accounts."""


import pandas as pd
from typing import List, Set, Tuple


from waad.utils.asset import Account


class SelectValidAccounts:
    """Select all valid accounts, with the following definitions : \n
    * There is an event 4624 for which TargetUserName = A et TargetDomainName = B ;
    * There is an event 4624 for which SubjectUserName = A et SubjectDomainName = B ;
    * There is an event 4672 for which SubjectUserName = A et SubjectDomainName = B ;
    * There is an event 4634 for which TargetUserName = A et TargetDomainName = B ;
    * There is an event 4648 for which SubjectUserName = A et SubjectUserName = B ;
    """

    def __init__(self, data: pd.DataFrame, subject_eventid_filter: Tuple[int, ...] = (4624, 4648, 4672), target_eventid_filter: Tuple[int, ...] = (4624, 4634)):
        self.data = data

        self.subject_eventid_filter = subject_eventid_filter
        self.target_eventid_filter = target_eventid_filter

        self.valid_accounts: Set[Account] = set()

    def run(self):
        for row in self.data.iterrows():
            if row[1]["eventid"] in self.subject_eventid_filter:
                if row[1]["subjectusername"] != "?":
                    self.valid_accounts.update({Account(row[1]["subjectusername"], row[1]["subjectdomainname"], row[1]["subjectusersid"])})
            if row[1]["eventid"] in self.target_eventid_filter:
                if row[1]["targetusername"] != "?":
                    self.valid_accounts.update({Account(row[1]["targetusername"], row[1]["targetdomainname"], row[1]["targetusersid"])})


class FilterOnSID:
    """Filter accounts on their SID following ANSSI's requirements."""

    def __init__(self, input_accounts: List[Account]):
        self.input_accounts = input_accounts
        self.non_standard_accounts: Set[Account] = set()

    def run(self):
        for account in self.input_accounts:
            if FilterOnSID.is_non_standard_SID(account.sid):
                self.non_standard_accounts.update({account})

    @staticmethod
    def is_non_standard_SID(sid: str) -> bool:
        return sid.startswith("S-1-5-21-") or sid == "?"
