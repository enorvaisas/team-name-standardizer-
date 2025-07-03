#!/usr/bin/env python3
"""
Script to fix duplicate team names and specifically address the LA Lakers / Los Angeles Lakers problem
"""

import json
import os
import re
from datetime import datetime

def fix_teams_database():
    # Load the teams.json file
    print("Loading teams.json...")
    with open('teams.json', 'r', encoding='utf-8') as file:
        teams = json.load(file)
    
    print(f"Original team count: {len(teams)}")
    
    # Track unique combinations of sport and canonical_team_name
    unique_teams = []
    unique_keys = set()
    duplicates = 0
    removed_la_lakers = False
    
    # Find any LA Lakers entries
    la_lakers_entries = []
    for i, team in enumerate(teams):
        if (team['sport'].lower() == 'basketball' and 
            (team['canonical_team_name'] == 'LA Lakers' or 
             re.search(r'\bLA Lakers\b', team['canonical_team_name'], re.IGNORECASE))):
            la_lakers_entries.append(i)
            print(f"Found 'LA Lakers' entry at index {i}: {team}")
    
    # Filter out duplicates and LA Lakers
    for i, team in enumerate(teams):
        sport = team['sport'].lower()
        name = team['canonical_team_name']
        
        # Skip LA Lakers entries (except the last one if we need to keep one)
        if i in la_lakers_entries:
            if i == la_lakers_entries[-1] and not any(t['sport'].lower() == 'basketball' and 
                                                     t['canonical_team_name'] == 'Los Angeles Lakers' 
                                                     for t in teams):
                print(f"Keeping entry {i} as we don't have a Los Angeles Lakers entry")
            else:
                print(f"Removing LA Lakers entry at index {i}")
                removed_la_lakers = True
                duplicates += 1
                continue
            
        key = (sport, name)
        
        if key not in unique_keys:
            unique_keys.add(key)
            unique_teams.append(team)
        else:
            duplicates += 1
    
    print(f"Found {duplicates} duplicates or problematic entries")
    print(f"Unique team count: {len(unique_teams)}")
    
    # Backup the original file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f'teams_backup_{timestamp}.json'
    print(f"Creating backup at {backup_file}")
    os.rename('teams.json', backup_file)
    
    # Write the cleaned teams back to teams.json
    print("Writing cleaned teams to teams.json...")
    with open('teams.json', 'w', encoding='utf-8') as file:
        json.dump(unique_teams, file, indent=4)
    
    if removed_la_lakers:
        print("Successfully removed problematic LA Lakers entries.")
    else:
        print("No LA Lakers entries needed to be removed.")
    
    print("Done! teams.json has been updated.")

if __name__ == "__main__":
    fix_teams_database() 