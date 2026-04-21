"""
Onlink-Clone: Central Game State (Mediator)

All shared simulation data lives here as plain dataclasses.
No subsystem imports another subsystem — they all read/write through GameState.

This file covers ALL models from the ajhenley fork, translated from
SQLAlchemy ORM to pure dataclasses for in-memory operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


# =========================================================================
# Enums
# =========================================================================
class NodeType(IntEnum):
    GATEWAY = 4
    PUBLIC_SERVER = 0
    INTERNAL_SRV = 1
    MAINFRAME = 2
    BANK = 3
    GOVERNMENT = 5
    POWER_PLANT = 6
    INTERNIC = 7
    AIRPORT = 8
    PORT = 9
    VEHICLE = 10


class CompanyType(IntEnum):
    GENERAL = 0
    FINANCIAL = 1
    LOGISTICS = 2
    PMC = 3
    MEDICAL = 4
    GOVERNMENT = 5
    ACADEMIC = 6


class SoftwareType(IntEnum):
    NONE = 0
    FILE_UTIL = 1
    HW_DRIVER = 2
    LOG_TOOLS = 3
    CRACKERS = 4
    BYPASSERS = 5
    LAN_TOOL = 6
    LOG_NUKER = 7
    VDPIN_DEFEATER = 8
    HUD_UPGRADE = 9
    OTHER = 10


class PersonStatus(IntEnum):
    NONE = 0
    ARRESTED = 1
    DEAD = 2
    DISAVOWED = 3


class VehicleType(IntEnum):
    TRUCK = 0
    AIRCRAFT = 1
    SHIP = 2


class ManifestStatus(IntEnum):
    IN_TRANSIT = 0
    DELIVERED = 1
    HIJACKED = 2
    LOST = 3
    INTERCEPTED = 4


class SquadStatus(IntEnum):
    IDLE = 0
    DEPLOYED = 1
    COMBAT = 2
    RECOVERY = 3


# =========================================================================
# Computer & related (fork: Computer, ComputerScreenDef, SecuritySystem,
#                      AccessLog, DataFile, VLocation)
# =========================================================================
@dataclass
class Record:
    """A single record in a record bank (fork: Record)."""

    name: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    photo_index: int = 0
@dataclass
class ComputerScreen:
    """A single screen definition on a computer (fork: ComputerScreenDef)."""

    screen_type: int = 0
    next_page: Optional[int] = None
    sub_page: int = 0
    data1: Optional[str] = None
    data2: Optional[str] = None
    data3: Optional[str] = None


@dataclass
class SecuritySystem:
    """A security subsystem installed on a computer (fork: SecuritySystem)."""

    security_type: int = 0  # 1=proxy, 2=firewall, 3=monitor, 4=encrypter
    level: int = 1
    is_active: bool = True
    is_bypassed: bool = False


@dataclass
class AccessLog:
    """A log entry on a computer (fork: AccessLog)."""

    log_time: str = ""
    from_ip: str = ""
    from_name: str = ""
    subject: str = ""
    log_type: int = 0
    is_visible: bool = True
    is_deleted: bool = False
    suspicion_level: int = 0
    tick_created: int = 0

    suspicion_level: int = 0  # 0=none, 1=low, 2=medium, 3=high/under investigation
    _suspicious_ticks: float = 0.0  # internal tracking for escalation


@dataclass
class DataFile:
    """A file stored on a computer (fork: DataFile). NOT the player's VFS."""

    filename: str = ""
    size: int = 1
    file_type: int = 1  # 1=data, 2=software
    softwaretype: int = 0
    encrypted_level: int = 0
    data: Optional[str] = None
    owner: Optional[str] = None


@dataclass
class Computer:
    """
    A full network computer (merges fork's Computer + VLocation).

    This replaces the old NetNode. It is keyed by IP in GameState.computers.
    """

    ip: str = ""
    name: str = ""
    company_name: str = ""
    computer_type: int = 0  # matches NodeType values
    trace_speed: float = -1.0
    hack_difficulty: float = 0.0
    is_running: bool = True

    # World map position (absorbed from VLocation)
    x: float = 0.0
    y: float = 0.0
    listed: bool = True  # visible on InterNIC

    # Region (for blackout grouping — original to us)
    region: str = "Global"
    is_online: bool = True

    # Sub-components
    screens: list[ComputerScreen] = field(default_factory=list)
    security_systems: list[SecuritySystem] = field(default_factory=list)
    files: list[DataFile] = field(default_factory=list)
    logs: list[AccessLog] = field(default_factory=list)
    internal_logs: list[AccessLog] = field(default_factory=list)
    recordbank: list[Record] = field(default_factory=list)

    # Network links (IPs of connected computers — original to us)
    links: list[str] = field(default_factory=list)

    # Login System Accounts (username -> password mapping)
    accounts: dict[str, str] = field(default_factory=dict)
    # Console state
    console_cwd: str = "/"

    def add_log(self, entry: AccessLog):
        """Adds a log to both public and internal backup lists."""
        import copy
        self.logs.append(entry)
        # Internal backup is a separate copy that remains untouched by deleters
        self.internal_logs.append(copy.deepcopy(entry))

    def log_modified(self, index: int) -> bool:
        """Check if a log entry has been modified (framed).
        Returns True if the public log differs from the internal backup.
        """
        if index < 0 or index >= len(self.logs) or index >= len(self.internal_logs):
            return False
        pub = self.logs[index]
        priv = self.internal_logs[index]
        return (pub.from_ip != priv.from_ip) or (pub.subject != priv.subject)

    def recover_log(self, index: int) -> bool:
        """Recover original log values from internal backup.
        Returns True if recovery was performed.
        """
        if index < 0 or index >= len(self.logs) or index >= len(self.internal_logs):
            return False
        if not self.log_modified(index):
            return False
        self.logs[index].from_ip = self.internal_logs[index].from_ip
        self.logs[index].subject = self.internal_logs[index].subject
        return True


# Alias for backward compatibility with our existing code
NetNode = Computer


# =========================================================================
# Gateway / Hardware (ours — fork only has the basic Gateway model)
# =========================================================================
@dataclass
class CPUCore:
    id: int = 0
    model: str = "Standard"
    base_speed: int = 10
    speed: int = 10
    health: float = 100.0
    overclock: float = 1.0


@dataclass
class GatewayState:
    """Player's physical gateway hardware."""

    name: str = "Gateway ALPHA"
    modem_speed: int = 1
    has_self_destruct: bool = False
    has_motion_sensor: bool = False

    # Advanced Hardware Engineering
    cpu_slots: int = 4
    cpus: list[CPUCore] = field(
        default_factory=lambda: [
            CPUCore(id=1, model="CPU ( 60 Ghz )", base_speed=60, speed=60),
        ]
    )

    memory_gq: int = 8 # Uplink: Memory for active tools/apps (GQ)
    storage_gq: int = 24 # Uplink: Storage for VFS files (GQ)

    ram_slots: int = 16 # Legacy/Advanced (Onlink)
    ram_used: int = 0
    ram_health: float = 100.0
    ram_overclock: float = 1.0

    storage_capacity: int = 64 # Legacy/Advanced (Onlink)
    storage_used: int = 0
    storage_health: float = 100.0
    storage_overclock: float = 1.0
    fragmentation: float = 0.0

    # Thermals & Power
    cooling_power: float = 1.0  # multiplier for AMBIENT_COOLING
    psu_capacity: float = 500.0  # watts
    power_draw: float = 50.0
    heat: float = 25.0
    is_melted: bool = False

    @property
    def cpu_speed(self) -> int:
        """Combined speed of all active CPUs."""
        return sum(c.speed for c in self.cpus if getattr(c, "is_active", True))

    max_heat: float = 90.0
    coolant_efficiency: float = 1.0
    is_melted: bool = False

    @property
    def cpu_speed(self) -> int:
        return sum(c.speed for c in self.cpus) if self.cpus else 60

    @property
    def memory_size(self) -> int:
        return self.storage_capacity


# =========================================================================
# Player (fork: Player)
# =========================================================================
@dataclass
class PlayerState:
    name: str = "Agent"
    handle: str = "AGENT"
    password: str = "AGENT" # Default login code
    balance: int = 3000
    uplink_rating: int = 1
    neuromancer_rating: int = 5
    credit_rating: int = 10
    status: PersonStatus = PersonStatus.NONE
    is_arrested: bool = False
    jail_sentence_ticks: int = 0
    arrest_count: int = 0
    disavow_countdown_ticks: int = 0
    bail_amount: int = 0
    localhost_ip: str = "127.0.0.1"
    last_login_ip: str = ""
    gateway_id: int = 0
    company_id: Optional[str] = None # NEW: ID of company owned by player
    known_ips: list[str] = field(default_factory=list)
    known_passwords: dict[str, str] = field(default_factory=dict)


# =========================================================================
# VFS — player's gateway memory (original to us)
# =========================================================================
@dataclass
class VFSFile:
    """A file on the player's gateway (our abstraction over fork's DataFile)."""

    id: str = ""
    filename: str = ""
    size_gq: int = 1
    ram_cost: int = 1
    file_type: int = 1
    software_type: SoftwareType = SoftwareType.NONE
    version: int = 1
    encrypted_level: int = 0
    data: str = ""
    blocks: list[int] = field(default_factory=list)
    compressed: bool = False
    is_active: bool = False  # Is it loaded into RAM?


@dataclass
class VFSState:
    total_memory_gq: int = 24
    files: list[VFSFile] = field(default_factory=list)

    @property
    def used_gq(self) -> int:
        return sum(f.size_gq for f in self.files)

    @property
    def free_gq(self) -> int:
        return self.total_memory_gq - self.used_gq


# =========================================================================
# Running Task (fork: RunningTask + our CPU/power extensions)
# =========================================================================
@dataclass
class RunningTask:
    task_id: int = 0
    tool_name: str = ""
    tool_version: int = 1
    target_ip: str = ""
    target_data: Optional[str] = None  # NEW — fork uses this for tool context
    progress: float = 0.0
    ticks_remaining: float = 0.0
    is_active: bool = True
    # Our extensions
    cpu_cost_ghz: float = 10.0
    power_cost: float = 5.0
    extra: dict = field(default_factory=dict)


# =========================================================================
# Connection & Bounce (fork: Connection, ConnectionNode)
# =========================================================================
@dataclass
class ConnectionNode:
    """A single hop in a bounce chain."""

    position: int = 0
    ip: str = ""
    is_traced: bool = False


@dataclass
class Connection:
    """An active network connection through a bounce chain (fork: Connection)."""

    target_ip: Optional[str] = None
    is_active: bool = False
    trace_progress: float = 0.0
    trace_active: bool = False
    nodes: list[ConnectionNode] = field(default_factory=list)


# Keep BounceChain as a convenience alias
@dataclass
class BounceChain:
    hops: list[str] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.hops)


# =========================================================================
# Person / NPC (fork: Person)
# =========================================================================
@dataclass
class Person:
    """An NPC in the game world (fork: Person)."""

    id: int = 0
    name: str = ""
    age: int = 30
    is_agent: bool = False
    localhost_ip: Optional[str] = None
    rating: int = 0
    uplink_rating: int = 0
    neuromancer_rating: int = 0
    has_criminal_record: bool = False
    voice_index: int = 0
    photo_index: int = 0

    # World Sim Extensions
    employer: Optional[str] = None
    job_role: str = "Civilian"
    ssn: str = ""
    home_ip: str = ""
    bank_account_num: str = ""
    status: PersonStatus = PersonStatus.NONE
    convictions: list[str] = field(default_factory=list)


# =========================================================================
# Mission (fork: Mission)
# =========================================================================
@dataclass
class Mission:
    id: int = 0
    mission_type: int = 0
    description: str = ""
    employer_name: str = ""
    payment: int = 0
    original_payment: int = 0  # stored to allow reverting
    negotiated_payment: int = 0  # if negotiated, otherwise same as payment
    is_negotiated: bool = False
    difficulty: int = 0
    min_rating: int = 0
    target_computer_ip: Optional[str] = None
    target_data: Optional[str] = None
    # Completion criteria (Uplink-style comparison strings)
    completion_a: Optional[str] = None
    completion_b: Optional[str] = None
    completion_c: Optional[str] = None
    completion_d: Optional[str] = None
    completion_e: Optional[str] = None

    is_accepted: bool = False
    is_completed: bool = False
    accepted_by: Optional[str] = None
    created_at_tick: int = 0
    due_at_tick: Optional[int] = None


# =========================================================================
# Message / Email (fork: Message)
# =========================================================================
@dataclass
class Message:
    id: int = 0
    from_name: str = ""
    subject: str = ""
    body: str = ""
    is_read: bool = False
    created_at_tick: int = 0


# =========================================================================
# Finance (fork: BankAccount, LoanRecord, StockEntry, StockHolding)
# =========================================================================
@dataclass
class TransactionRecord:
    hash: str = ""
    amount: int = 0
    from_account: str = ""
    to_account: str = ""
    tick: int = 0
    from_ip: str = ""
    to_ip: str = ""


@dataclass
class BankAccount:
    id: int = 0
    owner_name: str = ""
    bank_ip: str = ""
    balance: int = 0
    loan_amount: int = 0
    is_player: bool = False
    account_number: str = ""
    transaction_log: list[TransactionRecord] = field(default_factory=list)


@dataclass
class LoanRecord:
    id: int = 0
    bank_account_id: int = 0
    amount: int = 0
    interest_rate: float = 0.0
    created_at_tick: int = 0
    is_paid: bool = False


@dataclass
class StockHolding:
    company_name: str = ""
    shares: int = 0
    purchase_price: int = 0


# =========================================================================
# News (fork: NewsArticle — extends our NewsItem)
# =========================================================================
@dataclass
class NewsItem:
    headline: str = ""
    body: str = ""
    category: str = "general"
    tick_created: int = 0
    expires_at_tick: Optional[int] = None


# =========================================================================
# Scheduled Events (fork: ScheduledEvent)
# =========================================================================
@dataclass
class ScheduledEvent:
    id: int = 0
    event_type: str = ""
    trigger_tick: int = 0
    data: str = "{}"
    is_processed: bool = False


# =========================================================================
# Company (ours + fork's Company + StockEntry merged)
# =========================================================================
@dataclass
class TransportManifest:
    id: str = ""
    origin: str = ""
    destination: str = ""
    cargo: str = ""
    value: int = 0
    carrier_company: str = ""
    status: ManifestStatus = ManifestStatus.IN_TRANSIT
    vehicle_type: VehicleType = VehicleType.TRUCK
    vehicle_ip: Optional[str] = None
    progress: float = 0.0
    security_level: float = 10.0
    hacked_destination: Optional[str] = None
    is_security_sabotaged: bool = False


@dataclass
class Vehicle:
    """A persistent moving transport asset (Ship, Aircraft, Truck)."""
    id: str = ""
    name: str = ""
    vehicle_type: VehicleType = VehicleType.TRUCK
    owner_company: str = ""
    current_x: float = 0.0
    current_y: float = 0.0
    status: str = "IDLE"  # IDLE, IN_TRANSIT, DISABLED, HIJACKED
    ip: Optional[str] = None  # Hackable node IP if applicable
    speed_multiplier: float = 1.0


@dataclass
class PMCSquad:
    """A tactical squad owned by a PMC company."""
    id: str = ""
    name: str = ""
    owner_company: str = ""
    combat_rating: float = 10.0
    stealth_rating: float = 10.0
    tech_rating: float = 10.0
    status: SquadStatus = SquadStatus.IDLE
    location_x: float = 0.0
    location_y: float = 0.0
    target_manifest_id: Optional[str] = None
    salary: int = 500


@dataclass
class Company:
    name: str = ""
    company_type: CompanyType = CompanyType.GENERAL
    size: int = 20
    growth: int = 10
    alignment: int = 0
    boss_name: str = ""
    region: str = "Global"
    # Stock data (merged from fork's StockEntry)
    stock_price: float = 100.0
    stock_previous_price: float = 100.0
    stock_volatility: float = 0.05
    # World Sim extensions
    owner_id: Optional[str] = None
    assets: list[str] = field(default_factory=list)
    vehicles: list[Vehicle] = field(default_factory=list)  # Tracking owned transport


# =========================================================================
# World State
# =========================================================================
@dataclass
class WorldState:
    companies: list[Company] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)
    people: list[Person] = field(default_factory=list)  # was npc_agents dicts
    manifests: list[TransportManifest] = field(default_factory=list)
    pmc_squads: list[PMCSquad] = field(default_factory=list)


# =========================================================================
# Clock
# =========================================================================
@dataclass
class GameClock:
    tick_count: int = 0
    speed_multiplier: int = 1
    game_date: tuple = (24, 3, 2010)


@dataclass
class PassiveTrace:
    """NPC forensic investigation crawling through log trails."""

    trace_id: int
    current_node_ip: str
    target_ip: str
    ticks_until_next_hop: int
    is_active: bool = True


# =========================================================================
# Root State — the single object passed to all subsystems
# =========================================================================
@dataclass
class GameState:
    player: PlayerState = field(default_factory=PlayerState)
    gateway: GatewayState = field(default_factory=GatewayState)
    vfs: VFSState = field(default_factory=VFSState)
    clock: GameClock = field(default_factory=GameClock)
    world: WorldState = field(default_factory=WorldState)

    # Network (ip → Computer, replaces old nodes dict)
    computers: dict[str, Computer] = field(default_factory=dict)

    # Active connection state
    connection: Connection = field(default_factory=Connection)
    bounce: BounceChain = field(default_factory=BounceChain)

    # Passive Traces (Forensics)
    passive_traces: list[PassiveTrace] = field(default_factory=list)
    next_trace_id: int = 1

    # System Recovery Tracking (ip -> tick_hacked)
    compromised_ips: dict[str, int] = field(default_factory=dict)

    # Running hacking tools
    tasks: list[RunningTask] = field(default_factory=list)
    next_task_id: int = 1

    # Missions
    missions: list[Mission] = field(default_factory=list)
    next_mission_id: int = 1

    # Messages / Email inbox
    messages: list[Message] = field(default_factory=list)
    next_message_id: int = 1

    # Finance
    bank_accounts: list[BankAccount] = field(default_factory=list)
    loans: list[LoanRecord] = field(default_factory=list)
    stock_holdings: list[StockHolding] = field(default_factory=list)
    next_account_id: int = 1
    next_loan_id: int = 1

    # Scheduled events
    scheduled_events: list[ScheduledEvent] = field(default_factory=list)
    next_event_id: int = 1

    # Plot / storyline progression
    plot_state: int = 0

    # Backward compat alias: old code used state.nodes
    @property
    def nodes(self) -> dict[str, Computer]:
        return self.computers
