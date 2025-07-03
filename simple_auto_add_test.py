#!/usr/bin/env python3

from pure_python_solution import PurePythonTeamStandardizer
import json

def main():
    # Load teams
    with open('teams.json', 'r') as f:
        teams_data = json.load(f)

    print(f'Loaded {len(teams_data)} teams from teams.json')

    # Initialize with auto-add
    standardizer = PurePythonTeamStandardizer(
        teams_data, 
        threshold=0.75,           # 75% similarity for fuzzy matching
        auto_add_threshold=0.60   # Below 60% similarity = auto-add as new team
    )

    # Test cases that will show different behaviors
    test_cases = [
        ('Kaunas Zalgiris', 'basketball'),      # Should match existing "Kauno Zalgiris"
        ('New Basketball Team XYZ', 'basketball'),  # Should be auto-added
        ('Barcelona FC', 'soccer'),             # Should match existing "Barcelona"
        ('Unknown Soccer Club', 'soccer'),      # Should be auto-added
        ('Bayern Munich', 'soccer'),            # Should match "FC Bayern Munchen"
        ('Totally New Tennis Player', 'tennis'), # Should be auto-added
    ]

    print('\nTesting auto-add functionality:')
    print('='*60)

    for team_name, sport in test_cases:
        print(f'\nInput: "{team_name}" ({sport})')
        
        result, details = standardizer.standardize_team_name(
            team_name, sport, auto_add=True, return_details=True
        )
        
        status = details['status']
        
        if status == 'fuzzy_match':
            score = details.get('score', 0)
            print(f'  Result: "{result}"')
            print(f'  Status: ✓ FUZZY MATCH ({score:.1%} similarity)')
        elif status == 'auto_added':
            best_score = details.get('best_existing_score', 0)
            print(f'  Result: "{result}"')
            print(f'  Status: + AUTO-ADDED (best existing: {best_score:.1%})')
        elif status == 'exact_match':
            print(f'  Result: "{result}"')
            print(f'  Status: ✓ EXACT MATCH')
        else:
            print(f'  Result: "{result}"')
            print(f'  Status: ? {status.upper()}')

    # Show newly added teams
    new_teams = standardizer.get_newly_added_teams()
    print(f'\n🆕 New teams added during this test: {len(new_teams)}')
    for team in new_teams:
        print(f'  - {team["sport"]}: {team["canonical_team_name"]}')

    # Show updated stats
    stats = standardizer.get_statistics()
    print(f'\n📊 Statistics:')
    print(f'  Total teams: {stats["total_teams"]} (was {len(teams_data)})')
    print(f'  New teams this session: {stats["newly_added_this_session"]}')
    print(f'  Teams by sport:')
    for sport, count in sorted(stats['sports'].items()):
        print(f'    - {sport}: {count}')
    
    print(f'\n💡 Auto-add threshold: {standardizer.auto_add_threshold:.1%}')
    print(f'   Teams with similarity below this threshold are automatically added as new teams.')

if __name__ == "__main__":
    main() 