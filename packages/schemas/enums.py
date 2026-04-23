"""Domain enums for SystemDoctor AI workflow."""

from enum import Enum


class OSType(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class IssueCategory(str, Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    PERFORMANCE = "performance"
    UPDATE_DRIVER = "update_driver"
    BIOS_BOOT = "bios_boot"
    STORAGE = "storage"
    NETWORK = "network"
    OS_SPECIFIC = "os_specific"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionStatus(str, Enum):
    INTAKE = "intake"
    QUESTIONING = "questioning"
    DIAGNOSIS_READY = "diagnosis_ready"
    REMEDIATION_READY = "remediation_ready"
    VERIFYING = "verifying"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    ESCALATED = "escalated"
