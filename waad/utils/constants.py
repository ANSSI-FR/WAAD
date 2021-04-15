"""This module contains some constants of the process."""


from enum import Enum
from typing import Tuple


DATABASE_FIELDS = {
    "EventRecordID": "BIGINT",
    "EventID": "INTEGER",
    "SystemTime": "TEXT",
    "SubjectUserSid": "TEXT",
    "SubjectUserName": "TEXT",
    "SubjectDomainName": "TEXT",
    "SubjectLogonId": "TEXT",
    "PrivilegeList": "TEXT",
    "TargetUserSid": "TEXT",
    "TargetUserName": "TEXT",
    "TargetDomainName": "TEXT",
    "TargetLogonId": "TEXT",
    "TargetLogonGuid": "TEXT",
    "TargetServerName": "TEXT",
    "TargetInfo": "TEXT",
    "LogonType": "INTEGER",
    "LogonProcessName": "TEXT",
    "AuthenticationPackageName": "TEXT",
    "WorkstationName": "TEXT",
    "LogonGuid": "TEXT",  #
    "TransmittedServices": "TEXT",  #
    "ProcessName": "TEXT",
    "IpAddress": "TEXT",
    "IpPort": "INTEGER",
    "ImpersonationLevel": "TEXT",  #
    "RestrictedAdminMode": "TEXT",  #
    "TargetOutboundUserName": "TEXT",
    "TargetOutboundDomainName": "TEXT",
    "TargetLinkedLogonId": "TEXT",
    "ElevatedToken": "TEXT",  #
    "Keywords": "TEXT",  #
    "Opcode": "INTEGER",  #
    "Provider_Guid": "TEXT",  #
    "Security_UserID": "TEXT",  #
    "Task": "INTEGER",  #
    "Version": "INTEGER",  #
    "Host": "TEXT",
    "ComputerType": "TEXT",
    "Status": "TEXT",
    "SubStatus": "TEXT",
    "FailureReason": "TEXT",
    "VirtualAccount": "TEXT",  #
    "LmPackageName": "TEXT",
}


"""Dictionary containing all database field values and type."""


class Fields(Enum):
    SubjectUser = ("subjectusersid", "subjectusername", "subjectdomainname")
    TargetUser = ("targetusersid", "targetusername", "targetdomainname")
    TargetAuthent = ("targetservername", "targetinfo")
    Failure = ("failurereason", "status", "substatus")
    AuthMethod = ("authenticationpackagename", "lmpackagename")
    TargetOutbound = ("targetoutboundusername", "targetoutbounddomainname")

    @staticmethod
    def get_meta_field_from_tuple(tuple_to_find: Tuple[str, ...]):
        for field in Fields:
            if field.value == tuple_to_find:
                return field
        return None


class TupleAnalysisFields(Enum):
    FIRST_FIELDS_OF_INTERESTS = [
        Fields.SubjectUser.value,
        Fields.TargetUser.value,
        Fields.TargetAuthent.value,
        Fields.Failure.value,
        "logontype",
        "eventid",
        "ipaddress",
        "logonprocessname",
        Fields.AuthMethod.value,
        "workstationname",
        "host",
    ]
    SECOND_FIELDS_OF_INTERESTS = ["privilegelist", Fields.TargetOutbound.value]


STATUS_SUBSTATUS_TRANSLATION = {
    "0XC000005E": "There are currently no logon servers available to service the logon request.",
    "0XC0000064": "User logon with misspelled or bad user account",
    "0XC000006A": "User logon with misspelled or bad password",
    "0XC000006D": "This is either due to a bad username or authentication information",
    "0XC000006E": "Unknown user name or bad password.",
    "0XC000006F": "User logon outside authorized hours",
    "0XC0000070": "User logon from unauthorized workstation",
    "0XC0000071": "User logon with expired password",
    "0XC0000072": "User logon to account disabled by administrator",
    "0XC00000DC": "Indicates the Sam Server was in the wrong state to perform the desired operation.",
    "0XC0000133": "Clocks between DC and other computer too far out of sync",
    "0XC000015B": "The user has not been granted the requested logon type (aka logon right) at this machine",
    "0XC000018C": "The logon request failed because the trust relationship between the primary domain and the trusted domain failed.",
    "0XC0000192": "An attempt was made to logon, but the Netlogon service was not started.",
    "0XC0000193": "User logon with expired account",
    "0XC0000224": "User is required to change password at next logon",
    "0XC0000225": "Evidently a bug in Windows and not a risk",
    "0XC0000234": "User logon with account locked",
    "0XC00002EE": "Failure Reason: An Error occurred during Logon",
    "0XC0000413": "Logon Failure: The machine you are logging onto is protected by an authentication firewall. The specified account is not allowed to authenticate to the machine.",
    "0X0": "Status OK.",
}

"""Dictionary containing translation for all status and substatus codes."""
