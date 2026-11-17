import os
from pathlib import Path

# Import your modular parser scripts
import mmbn1_parser
import mmbn2_parser
import mmbn3_parser
# import mmbn4_parser  # (Uncomment when you map offsets later)
# import mmbn5_parser  # (Uncomment when you map offsets later)
import mmbn6_parser 

class MainOrchestrator:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        
        # Explicit hardware routing table mapping designated slots to modules
        self.HARDWARE_SLOT_MAP = {
            1: {"name": "Mega Man Battle Network 1", "module": mmbn1_parser},
            2: {"name": "Mega Man Battle Network 2", "module": mmbn2_parser},
            3: {"name": "Mega Man Battle Network 3", "module": mmbn3_parser},
            4: {"name": "Mega Man Battle Network 4", "module": None},  # Add module when ready
            5: {"name": "Mega Man Battle Network 5", "module": None},  # Add module when ready
            6: {"name": "Mega Man Battle Network 6", "module": mmbn6_parser}
        }

    def process_inserted_cartridge(self, filename, assigned_slot):
        """
        Reads the save payload and immediately forces execution through 
        the designated game parser file based on physical slot assignment.
        """
        file_path = self.script_dir / ".." / ".." / "playground" / "save files" / filename
        print(file_path)
        if not file_path.exists():
            print(f"[-] Hardware Error: File '{filename}' not found.")
            return

        if assigned_slot not in self.HARDWARE_SLOT_MAP:
            print(f"[-] Hardware Error: Port Slot {assigned_slot} out of physical range (1-6).")
            return

        with open(file_path, "rb") as f:
            raw_bytes = bytearray(f.read())

        slot_info = self.HARDWARE_SLOT_MAP[assigned_slot]
        target_module = slot_info["module"]

        print("=" * 60)
        print(f" HARDWARE EVENT: Cartridge Active in Slot {assigned_slot}")
        print(f" HARDWARE TRACE: Bypassing signature scans. Enforcing {slot_info['name']} maps.")
        print("=" * 60)

        if target_module is None:
            print(f"[-] Software Deficit: Parser script for {slot_info['name']} is pending implementation.")
            return

        # Execute the cleanly isolated game module parser directly
        print(f"[*] Dispatching byte payload straight to: {target_module.__name__}.py")
        profile = target_module.parse_save_block(raw_bytes)

        # ----------------------------------------------------
        # PRINT FINAL COMPILED DATA PROFILE
        # ----------------------------------------------------
        if profile.get("status") == "SUCCESS":
            print("\n----------------------------------------------")
            print(f" PARSED READ SUMMARY : {profile['game']}")
            print(f" VARIANT DETAILS     : {profile.get('variant', 'Designated Slot Execution')}")
            print("----------------------------------------------")
            print(f" Wallet Balance      : {profile['zenny']:,} Zenny")
            print(f" Game Completion     : {'Yes' if profile.get('game_completed_star') else 'No'}")
            if "bugfrags" in profile:
                print(f" Deep Net Currency   : {profile['bugfrags']} BugFrags")
            print(f" Health              : {profile['max_hp']} Max HP")
            print(f" Logged Activity     : {profile['playtime']}")
            print(f" Chip Completion     : {profile['chip_completion']['percentage_complete']:.2f}%")
            print(f" Power-Up Distribution : {profile['powerups']['total_powerups_distributed']}")
            print(f" All Power-Ups Found : {'Yes' if profile['powerups']['all_powerups_found'] else 'No'}")
            print(f" All HP Memories Found : {'Yes' if profile['powerups']['hp_stats']['all_hp_memories_found'] else 'No'}")
            print(f" Navi Chips Collected : {profile['navi_chips']['total_collected']}")
            print(f" All Navi Chips Found : {'Yes' if profile['navi_chips']['all_navi_chips_found'] else 'No'}")
            print(f" Overall Completion   : {profile['completion_percentage']}")
            print("----------------------------------------------\n")
        else:
            print(f"[-] Parser Script Runtime Crash: {profile.get('message')}")

if __name__ == "__main__":
    orchestrator = MainOrchestrator()
    
    # ----------------------------------------------------
    # DETERMINISTIC SLOT EXECUTION TEST
    # ----------------------------------------------------
    # If retry.sav belongs to Battle Network 1, you pass assigned_slot=1
    # If retry.sav belongs to Battle Network 3, you pass assigned_slot=3
    
    test_slot = 1  # Force slot matching for your test file
    orchestrator.process_inserted_cartridge("m1.sav", assigned_slot=1)
    orchestrator.process_inserted_cartridge("mmbn1.2104.sav", assigned_slot=1)
    # orchestrator.process_inserted_cartridge("m2.sav", assigned_slot=2)
    # orchestrator.process_inserted_cartridge("m3_partial.sav", assigned_slot=3)
    # orchestrator.process_inserted_cartridge("m3_full.sav", assigned_slot=3)
