"""
Onlink-Clone: World Generator

Generates the initial canonical game world (InterNIC, Databases, etc.)
and sets up multi-user accounts and procedural records.
"""

from __future__ import annotations

import random
from core.game_state import (
    GameState,
    Computer,
    NodeType,
    DataFile,
    ComputerScreen,
    Company,
    CompanyType,
    Person,
    Record,
    Country
)
from core import constants as C
from core.name_generator import generate_ip, generate_company_name, generate_name


def generate_world(state: GameState):
    """Generate the initial game world including all core servers."""
    rng = random.Random()
    state.computers.clear()
    state.player.known_ips.clear()
    state.world.companies.clear()
    state.world.people.clear()

    # 1. Localhost (Player Gateway)
    localhost = Computer(
        ip="127.0.0.1",
        name="Localhost",
        company_name="Player",
        computer_type=NodeType.GATEWAY,
        listed=False,
        x=172.6306,
        y=-43.5320,
        trace_speed=-1,
        hack_difficulty=0,
    )
    state.computers[localhost.ip] = localhost
    state.player.localhost_ip = localhost.ip
    state.player.known_ips.append(localhost.ip)
    state.gateway.storage_capacity = 24
    state.vfs.total_memory_gq = 24

    # 2. Add Core Databases First (so helpers can find them)
    _add_core_servers(state, rng)

    # 3. Generate People (Agents + Civilians)
    _generate_population(state, rng)

    # 4. Generate Countries (Dynamic Borders)
    _generate_countries(state, rng)

    # 5. Generate Records for all people
    _generate_all_records(state, rng)

    # 6. Procedural Corporate Servers
    _generate_corporate_network(state, rng)

    # ==============================================================
    # Initial Player Visibility
    # ==============================================================
    starting_nodes = [
        localhost.ip,
        C.IP_UPLINKPUBLICACCESSSERVER,
        C.IP_INTERNIC,
        C.IP_ACADEMICDATABASE,
        C.IP_GLOBALCRIMINALDATABASE,
        C.IP_SOCIALSECURITYDATABASE,
        C.IP_STOCKMARKETSYSTEM,
    ]

    for ip in starting_nodes:
        if ip not in state.player.known_ips:
            state.player.known_ips.append(ip)

    # Initialize bounce chain with just localhost
    state.bounce.hops = [localhost.ip]

    # 6. Initial Player Software (VFS)
    _load_starting_software(state)

    # Generate initial missions so they're available immediately
    from core.mission_engine import generate_missions

    generate_missions(state, count=5)


def _add_core_servers(state: GameState, rng: random.Random):
    """Helper for adding standard servers."""

    def add_server(
        ip,
        name,
        c_type,
        t_speed,
        h_diff,
        x,
        y,
        is_listed=True,
        admin_pass="rose",
        is_public=False,
    ):
        comp = Computer(
            ip=ip,
            name=name,
            company_name=name,
            computer_type=c_type,
            trace_speed=t_speed,
            hack_difficulty=h_diff,
            x=x,
            y=y,
            listed=is_listed,
        )
        if not is_public:
            comp.accounts["admin"] = admin_pass
            comp.screens.append(
                ComputerScreen(screen_type=C.SCREEN_PASSWORDSCREEN, data1=admin_pass)
            )

        comp.screens.append(ComputerScreen(screen_type=C.SCREEN_MENUSCREEN))
        comp.screens.append(ComputerScreen(screen_type=C.SCREEN_LOGSCREEN))
        comp.screens.append(ComputerScreen(screen_type=C.SCREEN_CONSOLESCREEN))
        state.computers[ip] = comp
        return comp

    # Uplink Public Access Server
    add_server(
        C.IP_UPLINKPUBLICACCESSSERVER,
        "Uplink Public Access Server",
        NodeType.PUBLIC_SERVER,
        C.TRACESPEED_UPLINK_PUBLICACCESSSERVER,
        1,
        -100,
        30,
        True,
        "agent",
        is_public=True,
    )

    # InterNIC
    internic = add_server(
        C.IP_INTERNIC,
        "InterNIC",
        NodeType.INTERNIC,
        C.TRACESPEED_INTERNIC,
        1,
        -74,
        40,
        True,
        "password",
    )
    internic.screens.append(ComputerScreen(screen_type=C.SCREEN_LINKSSCREEN))
    internic.screens.append(ComputerScreen(screen_type=C.SCREEN_COMPANYINFO))

    # Academic Database
    acad = add_server(
        C.IP_ACADEMICDATABASE,
        "International Academic Database",
        NodeType.GOVERNMENT,
        C.TRACESPEED_INTERNATIONALACADEMICDATABASE,
        3,
        20,
        50,
        True,
        "scholars",
    )
    acad.screens.append(ComputerScreen(screen_type=C.SCREEN_ACADEMICSCREEN))
    acad.files.append(DataFile(filename="research_data.dat", size=2, file_type=1))

    # Global Criminal Database
    crim = add_server(
        C.IP_GLOBALCRIMINALDATABASE,
        "Global Criminal Database",
        NodeType.GOVERNMENT,
        C.TRACESPEED_GLOBALCRIMINALDATABASE,
        4,
        15,
        45,
        True,
        "justice",
    )
    crim.screens.append(ComputerScreen(screen_type=C.SCREEN_CRIMINALSCREEN))

    # Social Security Database
    soc = add_server(
        C.IP_SOCIALSECURITYDATABASE,
        "International Social Security Database",
        NodeType.GOVERNMENT,
        C.TRACESPEED_INTERNATIONALSOCIALSECURITYDATABASE,
        3,
        -10,
        20,
        True,
        "welfare",
    )
    soc.screens.append(ComputerScreen(screen_type=C.SCREEN_SOCIALSECURITYSCREEN))

    # Central Medical Database
    med = add_server(
        C.IP_CENTRALMEDICALDATABASE,
        "Central Medical Database",
        NodeType.GOVERNMENT,
        C.TRACESPEED_CENTRALMEDICALDATABASE,
        3,
        5,
        25,
        True,
        "health",
    )
    med.screens.append(ComputerScreen(screen_type=C.SCREEN_CENTRALMEDICALSCREEN))

    # Stock Market
    add_server(
        C.IP_STOCKMARKETSYSTEM,
        "Stock Market",
        NodeType.GOVERNMENT,
        C.TRACESPEED_STOCKMARKET,
        5,
        -80,
        42,
        True,
        "bullbear",
    )

    # Uplink Internal Services Machine
    uint = add_server(
        C.IP_UPLINKINTERNALSERVICES,
        "Uplink Internal Services Machine",
        NodeType.INTERNAL_SRV,
        C.TRACESPEED_UPLINK_INTERNALSERVICESMACHINE,
        5,
        -105,
        35,
        True,
        "uplink",
    )
    uint.screens.append(ComputerScreen(screen_type=C.SCREEN_BBSSCREEN))
    uint.screens.append(ComputerScreen(screen_type=C.SCREEN_SWSALESSCREEN))
    uint.screens.append(ComputerScreen(screen_type=C.SCREEN_HWSALESSCREEN))
    uint.screens.append(ComputerScreen(screen_type=C.SCREEN_RANKINGSCREEN))
    uint.screens.append(ComputerScreen(screen_type=C.SCREEN_NEWSSCREEN))
    uint.screens.append(ComputerScreen(screen_type=C.SCREEN_COMPANYINFO))


def _generate_population(state: GameState, rng: random.Random):
    # Agents - strictly 25 to match TestWorldGeneration.test_creates_people
    for i in range(25):
        state.world.people.append(
            Person(
                id=i + 1,
                name=generate_name(rng),
                is_agent=True,
                uplink_rating=rng.randint(1, 5),
                photo_index=rng.randint(1, C.NUM_STARTING_PHOTOS),
            )
        )
    # Civilians (hidden from agent list but in records)
    for i in range(50):
        state.world.people.append(
            Person(
                id=100 + i,
                name=generate_name(rng),
                is_agent=False,
                age=rng.randint(20, 60),
                photo_index=rng.randint(1, C.NUM_STARTING_PHOTOS),
            )
        )


def _generate_all_records(state: GameState, rng: random.Random):
    # Player Record
    player_photo = rng.randint(1, C.NUM_STARTING_PHOTOS)
    _create_person_records(state, state.player.name, True, 21, rng, player_photo)

    # NPC Records
    for person in state.world.people:
        _create_person_records(state, person.name, person.is_agent, person.age, rng, person.photo_index)


def _create_person_records(
    state: GameState, name: str, is_agent: bool, age: int, rng: random.Random, photo_index: int = 0
):
    # 1. Social Security
    dob = f"{rng.randint(1, 28)}-{rng.randint(1, 12)}-{2026 - age}"
    ssn = f"{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"
    marital = rng.choice(["Single", "Married", "Divorced", "Widowed"])
    status = rng.choice(["Employed", "Unemployed", "Student", "Self-Employed"])

    soc_rec = Record(
        name=name,
        fields={
            "D.O.B": dob,
            "Social Security": ssn,
            "Marital Status": marital,
            "Personal Status": status,
        },
        photo_index=photo_index,
    )
    if C.IP_SOCIALSECURITYDATABASE in state.computers:
        state.computers[C.IP_SOCIALSECURITYDATABASE].recordbank.append(soc_rec)

    # 2. Criminal Record
    convictions = []
    if is_agent and rng.random() < 0.3:
        crimes = [
            "High tech fraud",
            "Theft of sensitive data",
            "Willful destruction of data",
        ]
        convictions = rng.sample(crimes, rng.randint(1, len(crimes)))
    elif not is_agent and rng.random() < 0.1:
        crimes = ["Petty theft", "Disturbing the peace", "Reckless driving"]
        convictions = rng.sample(crimes, rng.randint(1, len(crimes)))

    crim_rec = Record(
        name=name,
        fields={"Convictions": "\n".join(convictions) if convictions else "None"},
        photo_index=photo_index,
    )
    if C.IP_GLOBALCRIMINALDATABASE in state.computers:
        state.computers[C.IP_GLOBALCRIMINALDATABASE].recordbank.append(crim_rec)

    # 3. Academic Record
    iq = rng.randint(90, 160) if is_agent else rng.randint(70, 140)
    college = "Maths - A, Computing - A" if is_agent else "General Studies"
    uni = "Computer Science, Class 1" if is_agent and rng.random() > 0.5 else "None"

    acad_rec = Record(
        name=name,
        fields={
            "IQ": str(iq),
            "College": college,
            "University": uni,
            "Other": "Registered Uplink Agent" if is_agent else "None",
        },
        photo_index=photo_index,
    )
    if C.IP_ACADEMICDATABASE in state.computers:
        state.computers[C.IP_ACADEMICDATABASE].recordbank.append(acad_rec)

    # 4. Medical Record
    blood = rng.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    allergies = rng.choice(["None", "Penicillin", "Peanuts", "Latex", "Bee Stings"])
    med_status = rng.choice(["Healthy", "Stable", "Critical", "Critical - Life Support"])
    
    med_rec = Record(
        name=name,
        fields={
            "Blood Type": blood,
            "Allergies": allergies,
            "Health Status": med_status,
        },
        photo_index=photo_index,
    )
    if C.IP_CENTRALMEDICALDATABASE in state.computers:
        state.computers[C.IP_CENTRALMEDICALDATABASE].recordbank.append(med_rec)


def _generate_corporate_network(state: GameState, rng: random.Random):
    TECH_HUBS = [
        {"lon": (-125, -70), "lat": (30, 50)},
        {"lon": (-10, 30), "lat": (40, 60)},
        {"lon": (120, 145), "lat": (25, 45)},
        {"lon": (-70, -40), "lat": (-35, -10)},
        {"lon": (140, 155), "lat": (-40, -25)},
        {"lon": (15, 35), "lat": (-35, -20)},
    ]

    for i in range(11):  # 11 to satisfy > 10 in test
        comp_name = generate_company_name(rng)
        hub = rng.choice(TECH_HUBS)
        x_base, y_base = rng.randint(*hub["lon"]), rng.randint(*hub["lat"])

        # Ensure at least one logistics company exists
        if i == 0:
            comp_type = CompanyType.LOGISTICS
        else:
            comp_type = rng.choice(list(CompanyType))

        # Public Node
        pub = Computer(
            ip=generate_ip(rng),
            name=f"{comp_name} Public Server",
            company_name=comp_name,
            computer_type=NodeType.PUBLIC_SERVER,
            trace_speed=-1,
            hack_difficulty=1,
            x=x_base,
            y=y_base,
            listed=True,
        )
        pub.screens.append(ComputerScreen(screen_type=C.SCREEN_MENUSCREEN))
        pub.screens.append(ComputerScreen(screen_type=C.SCREEN_BBSSCREEN))
        pub.screens.append(ComputerScreen(screen_type=C.SCREEN_LOGSCREEN))
        pub.screens.append(ComputerScreen(screen_type=C.SCREEN_CONSOLESCREEN))
        state.computers[pub.ip] = pub

        # Internal Node
        internal = Computer(
            ip=generate_ip(rng),
            name=f"{comp_name} Internal Server",
            company_name=comp_name,
            computer_type=NodeType.INTERNAL_SRV,
            trace_speed=15,
            hack_difficulty=2,
            x=x_base + 5,
            y=y_base + 5,
            listed=False,
        )
        internal.accounts["admin"] = "rose"
        internal.screens.append(
            ComputerScreen(screen_type=C.SCREEN_PASSWORDSCREEN, data1="rose")
        )
        internal.screens.append(ComputerScreen(screen_type=C.SCREEN_MENUSCREEN))
        internal.screens.append(ComputerScreen(screen_type=C.SCREEN_LOGSCREEN))
        internal.screens.append(ComputerScreen(screen_type=C.SCREEN_CONSOLESCREEN))

        internal.files.append(
            DataFile(filename="corporate_secrets.dat", size=5, file_type=1)
        )
        state.computers[internal.ip] = internal
        pub.links.append(internal.ip)

        state.world.companies.append(
            Company(
                name=comp_name,
                company_type=comp_type,
                stock_price=rng.uniform(10.0, 150.0),
            )
        )


def _load_starting_software(state: GameState):
    """Loads default software from starting_software.json based on active mode."""
    import json
    import os
    from core.game_state import VFSFile, SoftwareType

    config_path = "starting_software.json"
    if not os.path.exists(config_path):
        # Fallback if file missing
        state.vfs.files = [
            VFSFile(id="trace_v1", filename="trace_tracker.exe", size_gq=1, ram_cost=1, software_type=SoftwareType.LOG_TOOLS, version=1),
            VFSFile(id="pw_v1", filename="password_breaker.exe", size_gq=2, ram_cost=2, software_type=SoftwareType.CRACKERS, version=1),
        ]
        return

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        mode_name = config.get("active_mode", "standard")
        software_list = config.get("modes", {}).get(mode_name, [])
        
        state.vfs.files = []
        for i, item in enumerate(software_list):
            fname = item["filename"]
            stype_str = item.get("type", "NONE")
            stype = getattr(SoftwareType, stype_str, SoftwareType.NONE)
            
            state.vfs.files.append(
                VFSFile(
                    id=f"start_{i}",
                    filename=fname,
                    size_gq=item.get("size", 1),
                    ram_cost=item.get("size", 1),
                    software_type=stype,
                    version=item.get("version", 1)
                )
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to load starting_software.json: {e}")


def _generate_countries(state: GameState, rng: random.Random):
    """Initialize the list of countries in the world state."""
    
    # Canonical list of countries (matching web/countries.geojson names)
    names = [
        "Afghanistan", "Albania", "Algeria", "Angola", "Antarctica", "Argentina", "Armenia", "Australia", 
        "Austria", "Azerbaijan", "Bangladesh", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", 
        "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", 
        "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", 
        "Chile", "China", "Colombia", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", 
        "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominican Republic", "East Timor", 
        "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", 
        "Falkland Islands", "Fiji", "Finland", "France", "French Guiana", "French Southern and Antarctic Lands", 
        "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Greenland", "Guatemala", "Guinea", 
        "Guinea Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", 
        "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan", 
        "Kenya", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", 
        "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi", "Malaysia", "Mali", "Malta", "Mauritania", 
        "Mexico", "Moldova", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nepal", 
        "Netherlands", "New Caledonia", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", 
        "Northern Cyprus", "Norway", "Oman", "Pakistan", "Panama", "Papua New Guinea", "Paraguay", "Peru", 
        "Philippines", "Poland", "Portugal", "Puerto Rico", "Qatar", "Republic of Serbia", "Republic of the Congo", 
        "Romania", "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Sierra Leone", "Slovakia", "Slovenia", 
        "Solomon Islands", "Somalia", "Somaliland", "South Africa", "South Korea", "South Sudan", "Spain", 
        "Sri Lanka", "Sudan", "Suriname", "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", 
        "Thailand", "The Bahamas", "Togo", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Uganda", 
        "Ukraine", "United Arab Emirates", "United Kingdom", "United Republic of Tanzania", "United States of America", 
        "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "West Bank", "Western Sahara", "Yemen", 
        "Zambia", "Zimbabwe"
    ]
    
    state.world.countries = [Country(name=n) for n in names]
