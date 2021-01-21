from typing import Union
from enum import Enum
from .types import EnumList, VersionState

editable_version_states = [
    VersionState.PREPARE_FOR_SUBMISSION,
    VersionState.WAITING_FOR_REVIEW,
    VersionState.WAITING_FOR_EXPORT_COMPLIANCE,
    VersionState.REJECTED,
    VersionState.METADATA_REJECTED,
    VersionState.DEVELOPER_REJECTED,
]

live_version_state = VersionState.READY_FOR_SALE


def enum_name(x: Union[Enum, str]):  # pylint: disable=unsubscriptable-object
    return x.name if isinstance(x, Enum) else x


def enum_names(x_list: EnumList):
    return (enum_name(x) for x in x_list)


def version_state_is_editable(
    version_state: Union[VersionState, str]  # pylint: disable=unsubscriptable-object
) -> bool:
    """Test whether or not the version state is 'editable' in the App Store."""
    return enum_name(version_state) in enum_names(editable_version_states)


def version_state_is_live(
    version_state: Union[VersionState, str]  # pylint: disable=unsubscriptable-object
) -> bool:
    """Test whether or not the version state is 'live' in the App Store."""
    return enum_name(version_state) == enum_name(live_version_state)
