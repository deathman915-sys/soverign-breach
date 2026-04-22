"""
Onlink-Clone: News Engine

Generates procedural news articles based on game events and ambient stories.
Ported from the Uplink reference code and adapted for GameState.
"""
from __future__ import annotations

import logging
import random

from core.game_state import GameState, NewsItem
from core.name_generator import generate_name

log = logging.getLogger(__name__)

# ============================================================
# Timing constants
# ============================================================
AMBIENT_NEWS_TICK_INTERVAL = 6000  # roughly every 20 game-minutes at 5 ticks/min
AMBIENT_MAX_PER_CYCLE = 2
AMBIENT_GENERATION_PROBABILITY = 0.40

# ============================================================
# Article templates keyed by event_type
# ============================================================
_TEMPLATES = {
    "arrest": {
        "headlines": [
            "Hacker '{agent_name}' Arrested by Federal Agents",
            "Uplink Agent '{agent_name}' Apprehended in Dawn Raid",
            "Cybercriminal '{agent_name}' Apprehended",
            "Federal Bureau Arrests Notorious Hacker '{agent_name}'",
            "'{agent_name}' Taken Into Custody After Hacking Spree",
        ],
        "bodies": [
            (
                "Federal Investigation Bureau agents stormed the gateway of the "
                "hacker known as '{agent_name}' early this morning. The suspect is "
                "believed to have been involved in multiple unauthorized computer "
                "intrusions over recent weeks. Equipment was confiscated and the "
                "suspect's Uplink account has been suspended pending trial."
            ),
            (
                "Authorities have confirmed the arrest of '{agent_name}', a "
                "freelance hacker operating through the Uplink network. Sources "
                "close to the investigation say the suspect failed to adequately "
                "cover their tracks after a recent intrusion. If convicted, "
                "'{agent_name}' faces up to 15 years in federal custody."
            ),
        ],
        "category": "crime",
    },
    "company_hack": {
        "headlines": [
            "{company_name} Suffers Major Security Breach",
            "Hackers Penetrate {company_name} Mainframe",
            "{company_name} Data Compromised in Cyber Attack",
            "Security Failure at {company_name} Exposes Sensitive Files",
            "{company_name} Internal Systems Breached by Unknown Hacker",
        ],
        "bodies": [
            (
                "{company_name} confirmed today that their internal computer "
                "systems were accessed by an unauthorized third party. A "
                "spokesperson said that the breach was detected by their security "
                "monitoring systems but not before significant data was accessed. "
                "The company has engaged forensic investigators and is cooperating "
                "with federal authorities."
            ),
            (
                "Shares in {company_name} fell sharply after reports emerged that "
                "hackers had penetrated the company's central mainframe. Industry "
                "analysts warn that the breach could have serious implications for "
                "the company's competitive position. {company_name} has declined "
                "to comment on the nature of the data stolen."
            ),
        ],
        "category": "corporate",
    },
    "stock_crash": {
        "headlines": [
            "{company_name} Shares Plummet After Financial Irregularities",
            "Stock Market Turmoil: {company_name} Loses {percent}%",
            "Investors Flee {company_name} as Share Price Collapses",
            "Trading Halted on {company_name} After Dramatic Sell-Off",
        ],
        "bodies": [
            (
                "Shares in {company_name} lost {percent}% of their value in "
                "frantic trading today amid rumours of financial irregularities. "
                "The crash wiped millions off the company's market capitalisation. "
                "Regulators are examining whether insider trading or external "
                "manipulation may have contributed to the sudden decline."
            ),
            (
                "The stock market was rocked today as {company_name} experienced "
                "its worst single-day loss in history. Analysts attributed the "
                "sell-off to concerns about data integrity in the company's "
                "financial systems. There is speculation that hackers may have "
                "tampered with the company's accounting records."
            ),
        ],
        "category": "financial",
    },
    "revelation_spread": {
        "headlines": [
            "Mystery Virus Spreads to New Systems",
            "Revelation Virus Claims Another Network",
            "Unstoppable Digital Plague Continues to Spread",
            "Computer Scientists Baffled by Self-Replicating Code",
        ],
        "bodies": [
            (
                "The so-called 'Revelation' virus has been detected on yet more "
                "computer systems worldwide. The virus, which appears to destroy "
                "all data on infected machines, has so far resisted all attempts "
                "at containment. Leading anti-virus researchers admit they have "
                "never seen anything like it. Internet traffic continues to be "
                "disrupted as administrators scramble to isolate affected systems."
            ),
            (
                "Officials today confirmed that the Revelation virus has spread "
                "to an additional {count} systems. The self-replicating program "
                "continues to evade all known counter-measures. Government "
                "cybersecurity advisors have issued an emergency alert urging all "
                "organisations to disconnect non-essential systems from the network "
                "until further notice."
            ),
        ],
        "category": "technology",
    },
    "system_failure": {
        "headlines": [
            "{system_name} Experiences Critical System Failure",
            "Major Outage Hits {system_name}",
            "{system_name} Goes Offline After Hardware Failure",
            "Users Report Widespread {system_name} Downtime",
        ],
        "bodies": [
            (
                "{system_name} suffered a critical failure today, leaving "
                "thousands of users without access to essential services. "
                "Engineers are working around the clock to restore operations. "
                "A spokesperson attributed the outage to 'an unexpected hardware "
                "malfunction' but declined to rule out external interference."
            ),
            (
                "Operations at {system_name} ground to a halt this morning after "
                "a catastrophic system failure. Backup systems also failed to "
                "engage, suggesting possible sabotage. Federal investigators have "
                "been called in to determine whether the outage was the result of "
                "a deliberate cyber attack."
            ),
        ],
        "category": "technology",
    },
    "agent_promotion": {
        "headlines": [
            "Uplink Agent '{agent_name}' Achieves {rating_name} Status",
            "'{agent_name}' Rises Through Uplink Ranks to {rating_name}",
            "Rising Star: '{agent_name}' Now Rated {rating_name}",
        ],
        "bodies": [
            (
                "The Uplink Corporation has confirmed that agent '{agent_name}' "
                "has been promoted to {rating_name} status. The promotion follows "
                "a string of successful operations and reflects the agent's "
                "growing reputation within the hacking community. '{agent_name}' "
                "is now ranked among the top operatives on the network."
            ),
            (
                "Sources within Uplink Corporation report that '{agent_name}' has "
                "achieved the coveted {rating_name} rating. Industry watchers note "
                "that few agents reach this level, and those who do tend to attract "
                "the attention of both employers and law enforcement in equal measure."
            ),
        ],
        "category": "community",
    },
    "corporate_merger": {
        "headlines": [
            "Market Shakeup: {company_a} and {company_b} announce merger",
            "Mega-Corp Alert: {new_name} formed from high-profile merger",
            "{company_a} acquired by rival {company_b} in hostile takeover",
            "Consolidation Crisis: {new_name} dominates the {company_a} market sector",
        ],
        "bodies": [
            (
                "In a move that has shocked financial analysts, {company_a} and "
                "{company_b} have confirmed their merger into the new conglomerate "
                "'{new_name}'. Network administrators are currently synchronizing "
                "internal server records across both corporate infrastructures."
            ),
            (
                "The digital landscape has shifted following the formation of '{new_name}'. "
                "The entity, born from the union of {company_a} and {company_b}, now "
                "controls a significant portion of regional data traffic. Critics warn "
                "of a growing monopoly in the tech sector."
            ),
        ],
        "category": "corporate",
    },
}

_AMBIENT_HEADLINES = [
    "Global Internet Traffic Reaches New Record High",
    "Government Proposes Stricter Cybercrime Legislation",
    "Uplink Corporation Reports Record Quarterly Profits",
    "New Encryption Standard Proposed by International Committee",
    "Debate Rages Over Digital Privacy Rights",
    "Tech Giants Invest Billions in Quantum Computing Research",
    "Cybersecurity Experts Warn of Rising Threat Landscape",
    "International Academic Database Celebrates 10 Million Records",
    "Federal Bureau Announces New Cybercrime Task Force",
    "Stock Market Reaches All-Time High on Tech Sector Strength",
    "Analysts Predict Surge in Corporate Espionage",
    "Internet Freedom Group Condemns Government Monitoring",
    "New Gateway Hardware Announced by Leading Manufacturer",
    "Social Security Database Upgrade Completed Successfully",
    "Central Medical Database Expands Coverage to New Regions",
    "InterNIC Reports Domain Registration Boom",
    "Software Piracy Costs Industry Billions Annually",
    "Virtual Reality Interfaces Gaining Traction in Corporate Sector",
    "Artificial Intelligence Lab Announces Breakthrough",
    "Cloud Computing Adoption Accelerates Worldwide",
]

_AMBIENT_BODIES = [
    (
        "In a report released today, analysts noted that global internet traffic "
        "has reached unprecedented levels. The growth is attributed to increased "
        "corporate connectivity and the proliferation of always-on gateway systems. "
        "Network engineers warn that infrastructure may struggle to keep pace with "
        "demand in the coming years."
    ),
    (
        "Industry observers report a significant shift in the digital landscape "
        "as more organisations embrace connected systems. Experts warn that this "
        "increased connectivity also brings heightened security risks, with "
        "corporate espionage and data theft on the rise. Companies are urged to "
        "invest in robust security measures."
    ),
    (
        "A new study from the International Computing Research Institute suggests "
        "that cybercrime costs the global economy over 200 billion credits "
        "annually. The report calls for greater cooperation between law "
        "enforcement agencies and the private sector to combat the growing threat."
    ),
    (
        "Technology sector stocks continued their upward trend today, buoyed by "
        "strong earnings reports from several major corporations. Market analysts "
        "remain cautiously optimistic, though some warn that current valuations "
        "may not be sustainable in the long term."
    ),
    (
        "Digital rights advocates have raised concerns about proposed new "
        "legislation that would grant law enforcement expanded powers to monitor "
        "internet communications. Critics argue the measures go too far and could "
        "be used to target legitimate privacy tools used by ordinary citizens."
    ),
]

class _SafeFormatDict(dict):
    """A dict subclass that returns the key name wrapped in braces for missing keys,
    preventing KeyError in str.format_map calls."""
    def __missing__(self, key):
        return "{" + key + "}"

def _build_defaults(rng: random.Random) -> dict[str, str]:
    """Build sensible default placeholder values for templates."""
    return {
        "agent_name": generate_name(rng),
        "company_name": "TechCorp",
        "percent": str(rng.randint(5, 45)),
        "count": str(rng.randint(3, 50)),
        "system_name": rng.choice([
            "International Academic Database",
            "Global Criminal Database",
            "Social Security Database",
            "Central Medical Database",
            "InterNIC",
            "Stock Market System",
        ]),
        "rating_name": "Intermediate",
    }

def _generate_ambient_article(state: GameState, current_tick: int, rng: random.Random) -> NewsItem:
    """Generate a random news item using ambient templates."""
    headline = rng.choice(_AMBIENT_HEADLINES)
    body = rng.choice(_AMBIENT_BODIES)

    news = NewsItem(
        headline=headline,
        body=body,
        category="general",
        tick_created=current_tick,
    )
    state.world.news.append(news)
    return news

def tick_news(state: GameState, current_tick: int) -> list[dict]:
    """Generate ambient/random news periodically."""
    if current_tick % AMBIENT_NEWS_TICK_INTERVAL != 0:
        return []

    rng = random.Random()
    events = []

    count = rng.randint(1, AMBIENT_MAX_PER_CYCLE)
    for _ in range(count):
        if rng.random() > AMBIENT_GENERATION_PROBABILITY:
            continue
        news = _generate_ambient_article(state, current_tick, rng)
        if news:
            events.append({"type": "news", "headline": news.headline})

    # Financial monitoring
    for comp in state.world.companies:
        if comp.name in ("Government", "InterNIC"):
            continue
        if comp.stock_previous_price > 0:
            change_pct = (comp.stock_price - comp.stock_previous_price) / comp.stock_previous_price * 100
            if change_pct < -15:
                add_news(state, "stock_crash", company_name=comp.name, percent=f"{abs(change_pct):.0f}")
            elif change_pct > 20:
                # We could add stock_boom to templates too
                add_news(state, "company_hack", company_name=comp.name)

    return events

def add_news(state: GameState, event_type: str, **kwargs) -> NewsItem | None:
    """Generate a news article based on a game event."""
    rng = random.Random()
    template = _TEMPLATES.get(event_type)

    if template is None:
        log.warning("Unknown news event_type: %s -- generating ambient", event_type)
        return _generate_ambient_article(state, state.clock.tick_count, rng)

    defaults = _build_defaults(rng)
    merged = {**defaults, **kwargs}

    headline = rng.choice(template["headlines"]).format_map(_SafeFormatDict(merged))
    body = rng.choice(template["bodies"]).format_map(_SafeFormatDict(merged))
    category = template.get("category", "general")

    news = NewsItem(
        headline=headline,
        body=body,
        category=category,
        tick_created=state.clock.tick_count,
    )
    state.world.news.append(news)
    return news

def get_recent_news(state: GameState, count: int = 20) -> list[dict]:
    """Get the most recent news items."""
    sorted_news = sorted(state.world.news, key=lambda n: n.tick_created, reverse=True)
    return [
        {
            "headline": n.headline,
            "body": n.body,
            "category": n.category,
            "tick": n.tick_created,
        }
        for n in sorted_news[:count]
    ]

def create_npc_mission_news(state: GameState, npc_name: str, mission_desc: str) -> NewsItem:
    """Generate a news item reporting a rival agent's mission completion."""
    templates = [
        "Rival agent '{name}' successfully completes contract: {desc}",
        "Global cyber-security alert: '{name}' linked to breach involving {desc}",
        "Uplink BBS reports completion of high-priority task '{desc}' by agent {name}",
        "Authorities confirm data breach: '{name}' is the primary suspect in {desc}"
    ]

    headline = random.choice(templates).format(name=npc_name, desc=mission_desc)
    news = NewsItem(
        headline=headline,
        body=f"Reports are circulating within the underground that the agent known as '{npc_name}' "
             f"has successfully fulfilled a high-stakes contract involving '{mission_desc}'. "
             f"Public systems are adjusting to the ripple effects of this breach.",
        category="criminal",
        tick_created=state.clock.tick_count
    )
    state.world.news.append(news)
    return news
