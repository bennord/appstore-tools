from enum import Enum, auto

# TODO: remove pylint "disable" directives when pylint supports python 3.9 completely
from typing import TypedDict, Optional, Union, Literal, Sequence


class Platform(Enum):
    IOS = auto()
    MAC_OS = auto()
    TV_OS = auto()


class ReleaseType(Enum):
    MANUAL = auto()
    AFTER_APPROVAL = auto()
    SCHEDULED = auto()


class VersionState(Enum):
    DEVELOPER_REMOVED_FROM_SALE = auto()
    DEVELOPER_REJECTED = auto()
    IN_REVIEW = auto()
    INVALID_BINARY = auto()
    METADATA_REJECTED = auto()
    PENDING_APPLE_RELEASE = auto()
    PENDING_CONTRACT = auto()
    PENDING_DEVELOPER_RELEASE = auto()
    PREPARE_FOR_SUBMISSION = auto()
    PREORDER_READY_FOR_SALE = auto()
    PROCESSING_FOR_APP_STORE = auto()
    READY_FOR_SALE = auto()
    REJECTED = auto()
    REMOVED_FROM_SALE = auto()
    WAITING_FOR_EXPORT_COMPLIANCE = auto()
    WAITING_FOR_REVIEW = auto()
    REPLACED_WITH_NEW_VERSION = auto()


class ScreenshotDisplayType(Enum):
    APP_IPHONE_65 = auto()
    APP_IPHONE_58 = auto()
    APP_IPHONE_55 = auto()
    APP_IPHONE_47 = auto()
    APP_IPHONE_40 = auto()
    APP_IPHONE_35 = auto()
    APP_IPAD_PRO_3GEN_129 = auto()
    APP_IPAD_PRO_3GEN_11 = auto()
    APP_IPAD_PRO_129 = auto()
    APP_IPAD_105 = auto()
    APP_IPAD_97 = auto()
    APP_DESKTOP = auto()
    APP_WATCH_SERIES_4 = auto()
    APP_WATCH_SERIES_3 = auto()
    APP_APPLE_TV = auto()
    IMESSAGE_APP_IPHONE_65 = auto()
    IMESSAGE_APP_IPHONE_58 = auto()
    IMESSAGE_APP_IPHONE_55 = auto()
    IMESSAGE_APP_IPHONE_47 = auto()
    IMESSAGE_APP_IPHONE_40 = auto()
    IMESSAGE_APP_IPAD_PRO_3GEN_129 = auto()
    IMESSAGE_APP_IPAD_PRO_3GEN_11 = auto()
    IMESSAGE_APP_IPAD_PRO_129 = auto()
    IMESSAGE_APP_IPAD_105 = auto()
    IMESSAGE_APP_IPAD_97 = auto()


class PreviewType(Enum):
    IPHONE_65 = auto()
    IPHONE_58 = auto()
    IPHONE_55 = auto()
    IPHONE_47 = auto()
    IPHONE_40 = auto()
    IPHONE_35 = auto()
    IPAD_PRO_3GEN_129 = auto()
    IPAD_PRO_3GEN_11 = auto()
    IPAD_PRO_129 = auto()
    IPAD_105 = auto()
    IPAD_97 = auto()
    DESKTOP = auto()
    WATCH_SERIES_4 = auto()
    WATCH_SERIES_3 = auto()
    APPLE_TV = auto()


class MediaAssetState(Enum):
    AWAITING_UPLOAD = auto()
    UPLOAD_COMPLETE = auto()
    COMPLETE = auto()
    FAILED = auto()


EnumList = Sequence[Union[Enum, str]]  # pylint: disable=unsubscriptable-object
PlatformList = Sequence[Union[Platform, str]]  # pylint: disable=unsubscriptable-object
VersionStateList = Sequence[
    Union[VersionState, str]  # pylint: disable=unsubscriptable-object
]


class InfoAttributes(TypedDict, total=False):  # pylint: disable=inherit-non-class
    primaryCategory: Optional[str]  # pylint: disable=unsubscriptable-object
    primarySubcategoryOne: Optional[str]  # pylint: disable=unsubscriptable-object
    primarySubcategoryTwo: Optional[str]  # pylint: disable=unsubscriptable-object
    secondaryCategory: Optional[str]  # pylint: disable=unsubscriptable-object
    secondarySubcategoryOne: Optional[str]  # pylint: disable=unsubscriptable-object
    secondarySubcategoryTwo: Optional[str]  # pylint: disable=unsubscriptable-object


class InfoLocalizationAttributes(
    TypedDict, total=False
):  # pylint: disable=inherit-non-class
    name: Optional[str]  # pylint: disable=unsubscriptable-object
    privacyPolicyText: Optional[str]  # pylint: disable=unsubscriptable-object
    privacyPolicyUrl: Optional[str]  # pylint: disable=unsubscriptable-object
    subtitle: Optional[str]  # pylint: disable=unsubscriptable-object


class VersionAttributes(TypedDict, total=False):  # pylint: disable=inherit-non-class
    copyright: Optional[str]  # pylint: disable=unsubscriptable-object
    earliestReleaseDate: Optional[str]  # pylint: disable=unsubscriptable-object
    releaseType: Optional[str]  # pylint: disable=unsubscriptable-object
    usesIdfa: Optional[bool]  # pylint: disable=unsubscriptable-object
    versionString: Optional[str]  # pylint: disable=unsubscriptable-object
    downloadable: Optional[bool]  # pylint: disable=unsubscriptable-object


class VersionLocalizationAttributes(
    TypedDict, total=False
):  # pylint: disable=inherit-non-class
    description: Optional[str]  # pylint: disable=unsubscriptable-object
    keywords: Optional[str]  # pylint: disable=unsubscriptable-object
    marketingUrl: Optional[str]  # pylint: disable=unsubscriptable-object
    promotionalText: Optional[str]  # pylint: disable=unsubscriptable-object
    supportUrl: Optional[str]  # pylint: disable=unsubscriptable-object
    whatsNew: Optional[str]  # pylint: disable=unsubscriptable-object
