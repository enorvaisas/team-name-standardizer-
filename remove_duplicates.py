import json
import os

def remove_duplicates_from_teams_json():
    # Load the teams.json file
    print("Loading teams.json...")
    with open('teams.json', 'r') as file:
        teams = json.load(file)
    
    print(f"Original team count: {len(teams)}")
    
    # Track unique combinations of sport and canonical_team_name
    unique_teams = []
    unique_keys = set()
    duplicates = 0
    empty_names = 0
    
    # Filter out duplicates
    for team in teams:
        sport = team['sport']
        name = team['canonical_team_name']
        
        # Count empty names
        if name == "":
            empty_names += 1
            
        key = (sport, name)
        
        if key not in unique_keys:
            unique_keys.add(key)
            unique_teams.append(team)
        else:
            duplicates += 1
    
    print(f"Found {duplicates} duplicates")
    print(f"Found {empty_names} entries with empty canonical_team_name")
    print(f"Unique team count: {len(unique_teams)}")
    
    # Backup the original file
    backup_file = 'teams_backup.json'
    print(f"Creating backup at {backup_file}")
    os.rename('teams.json', backup_file)
    
    # Write the unique teams back to teams.json
    print("Writing unique teams to teams.json...")
    with open('teams.json', 'w') as file:
        json.dump(unique_teams, file, indent=4)
    
    print("Done! teams.json has been updated with duplicate entries removed.")

if __name__ == "__main__":
    remove_duplicates_from_teams_json() 