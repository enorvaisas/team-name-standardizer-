#!/usr/bin/env python3
"""
Quick test of pure Python solution with real teams.json data
"""

from pure_python_solution import PurePythonTeamStandardizer
import json

def main():
    # Load real teams data
    with open('teams.json', 'r') as f:
        teams_data = json.load(f)

    print(f"Loaded {len(teams_data)} teams from teams.json")
    
    # Count teams by sport
    sports_count = {}
    for team in teams_data:
        sport = team.get('sport', '').lower()
        if sport:
            sports_count[sport] = sports_count.get(sport, 0) + 1
    
    print(f"Sports available: {dict(sports_count)}")
    print()

    standardizer = PurePythonTeamStandardizer(teams_data, threshold=0.70)

    # Test some variations with real data
    test_cases = [
        ('Kaunas Zalgiris', 'basketball'),
        ('Real Madrid CF', 'soccer'), 
        ('FC Barcelona', 'soccer'),
        ('Man City', 'soccer'),
        ('Bayern Munich', 'soccer'),
        ('Lakers', 'basketball'),
        ('Celtics', 'basketball'),
    ]

    print('Testing Pure Python Solution with REAL data:')
    print('=' * 55)
    
    for team, sport in test_cases:
        result = standardizer.standardize_team_name(team, sport, auto_add=False)
        status = 'MATCHED' if result != team else 'NO MATCH'
        print(f"Input:  '{team}' ({sport})")
        print(f"Output: '{result}' [{status}]")
        print("-" * 40)

if __name__ == "__main__":
    main() 