"""
Onlink-Clone: Logistics Engine

Generates and manages transport manifests and logistical micro-data,
including creating moving temporary Computer nodes for Planes and Ships.
"""
from __future__ import annotations

import logging
import random

from core.game_state import (
    CompanyType,
    Computer,
    ComputerScreen,
    DataFile,
    GameState,
    ManifestStatus,
    NodeType,
    TransportManifest,
    VehicleType,
)
from core.name_generator import generate_ip

log = logging.getLogger(__name__)

LOGISTICS_TICK_INTERVAL = 1000  # Generate a new trip every ~3.3 mins

class LogisticsEngine:
    def __init__(self):
        self._id_counter = random.randint(1000, 9999)

    def tick(self, state: GameState):
        if state.clock.tick_count % LOGISTICS_TICK_INTERVAL == 0:
            self._generate_ambient_trip(state)

        # Update progress and coordinates for moving vehicles
        for company in state.world.companies:
            for vehicle in company.vehicles:
                if vehicle.status == "IN_TRANSIT":
                    # Find active manifest for this vehicle
                    manifest = next((m for m in state.world.manifests if m.vehicle_ip == vehicle.ip and m.status == ManifestStatus.IN_TRANSIT), None)
                    if not manifest:
                        vehicle.status = "IDLE"
                        continue

                    # Variable speeds based on vehicle type
                    speed = 0.001 # Default Truck
                    if manifest.vehicle_type == VehicleType.AIRCRAFT:
                        speed = 0.002
                    elif manifest.vehicle_type == VehicleType.SHIP:
                        speed = 0.0005

                    manifest.progress += speed * vehicle.speed_multiplier
                    if manifest.progress >= 1.0:
                        manifest.status = ManifestStatus.DELIVERED
                        vehicle.status = "IDLE"
                        # Bonus for player company
                        if company.owner_id == "PLAYER":
                            state.player.balance += int(manifest.value * 0.1)
                            log.info(f"CONTRACT FULFILLED: {manifest.id} Payout: {int(manifest.value * 0.1)}c")

                        if vehicle.ip in state.computers:
                            del state.computers[vehicle.ip]
                    elif vehicle.ip in state.computers:
                        # Interpolate coordinates
                        v_node = state.computers[vehicle.ip]
                        orig_nodes = [c for c in state.computers.values() if c.name == manifest.origin]

                        # Use hacked destination if set
                        target_dest = manifest.hacked_destination or manifest.destination
                        dest_nodes = [c for c in state.computers.values() if c.name == target_dest]

                        if orig_nodes and dest_nodes:
                            x1, y1 = orig_nodes[0].x, orig_nodes[0].y
                            x2, y2 = dest_nodes[0].x, dest_nodes[0].y
                            vehicle.current_x = x1 + (x2 - x1) * manifest.progress
                            vehicle.current_y = y1 + (y2 - y1) * manifest.progress
                            v_node.x, v_node.y = vehicle.current_x, vehicle.current_y

    def _generate_ambient_trip(self, state: GameState):
        logistics_companies = [c for c in state.world.companies if c.company_type == CompanyType.LOGISTICS]
        if not logistics_companies:
            return

        company = random.choice(logistics_companies)

        drivers = [p for p in state.world.people if p.employer == company.name and "Driver" in p.job_role]
        driver_name = random.choice(drivers).name if drivers else "Contract Driver"

        # Roll transport type
        roll = random.random()
        vehicle_type = VehicleType.TRUCK

        orig_node, dest_node = None, None

        if roll < 0.25:
            vehicle_type = VehicleType.AIRCRAFT
            airports = [c for c in state.computers.values() if c.computer_type == NodeType.AIRPORT]
            if len(airports) >= 2:
                orig_node, dest_node = random.sample(airports, 2)
        elif roll < 0.40:
            vehicle_type = VehicleType.SHIP
            ports = [c for c in state.computers.values() if c.computer_type == NodeType.PORT]
            if len(ports) >= 2:
                orig_node, dest_node = random.sample(ports, 2)

        if not orig_node or not dest_node:
            vehicle_type = VehicleType.TRUCK
            # Fixed cities lookup
            cities = ["London", "New York", "Tokyo", "Paris", "Berlin", "San Francisco", "Sydney", "Singapore"]
            orig_name = random.choice(cities)
            dest_name = random.choice([c for c in cities if c != orig_name])
        else:
            orig_name = orig_node.name
            dest_name = dest_node.name

        cargo_items = ["GPU Crates", "Medical Supplies", "Industrial Chemicals", "Luxury Goods", "Server Hardware"]

        manifest = TransportManifest(
            id=f"TRK-{self._id_counter}",
            origin=orig_name,
            destination=dest_name,
            cargo=f"{random.choice(cargo_items)} (Driver: {driver_name})",
            value=random.randint(5000, 50000),
            carrier_company=company.name,
            vehicle_type=vehicle_type,
            status=ManifestStatus.IN_TRANSIT,
            security_level=random.uniform(10.0, 50.0)
        )
        self._id_counter += 1

        # Instantiate moving target
        if vehicle_type in (VehicleType.AIRCRAFT, VehicleType.SHIP) and orig_node:
            v_ip = generate_ip()
            manifest.vehicle_ip = v_ip
            v_name = f"{company.name} {vehicle_type.name} {manifest.id}"

            # Create the temporary hackable node
            vehicle_node = Computer(
                ip=v_ip, name=v_name, company_name=company.name,
                computer_type=NodeType.VEHICLE,
                trace_speed=5.0, hack_difficulty=25.0,
                x=orig_node.x, y=orig_node.y, listed=False,
                screens=[
                    ComputerScreen(screen_type=1, next_page=2, sub_page=0), # password
                    ComputerScreen(screen_type=2, next_page=3, sub_page=0), # menu
                    ComputerScreen(screen_type=3, next_page=4, sub_page=0), # files
                    ComputerScreen(screen_type=39, next_page=5, sub_page=0), # logistics control
                    ComputerScreen(screen_type=5, next_page=6, sub_page=0)  # logs
                ]
            )
            vehicle_node.files.append(DataFile(filename="cargo_manifest.doc", size=2, file_type=1, data=f"MANIFEST: {manifest.id}\nCARGO: {manifest.cargo}\nVAL: {manifest.value}"))
            state.computers[v_ip] = vehicle_node

        state.world.manifests.append(manifest)
        if len(state.world.manifests) > 100:
            # Cleanup old computers if they got stuck
            old = state.world.manifests.pop(0)
            if old.vehicle_ip and old.vehicle_ip in state.computers:
                del state.computers[old.vehicle_ip]
