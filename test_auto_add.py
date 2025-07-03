#!/usr/bin/env python3
"""
Test script for the auto-add functionality of the Pure Python Team Standardizer
Tests with real data from teams.json and demonstrates automatic team addition
"""

import json
import sys
from pure_python_solution import PurePythonTeamStandardizer

def test_auto_add_functionality():
    """Test the auto-add functionality with various scenarios"""
    
    print("🧪 Testing Auto-Add Functionality for Team Name Standardizer")
    print("=" * 65)
    
    # Load existing teams data
    try:
        with open("teams.json", 'r') as f:
            teams_data = json.load(f)
        print(f"✅ Loaded {len(teams_data)} teams from teams.json")
    except Exception as e:
        print(f"❌ Error loading teams.json: {e}")
        return
    
    # Count teams by sport for reference
    sport_counts = {}
    for team in teams_data:
        sport = team.get('sport', 'unknown').lower()
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
    
    print(f"📊 Initial teams by sport: {dict(sport_counts)}")
    print()
    
    # Initialize standardizer with specific thresholds
    standardizer = PurePythonTeamStandardizer(
        teams_data,
        threshold=0.75,           # Must score 75%+ for fuzzy match
        auto_add_threshold=0.60   # Below 60% similarity = add as new team
    )
    
    print(f"⚙️  Configuration:")
    print(f"   - Fuzzy match threshold: {standardizer.threshold:.2f}")
    print(f"   - Auto-add threshold: {standardizer.auto_add_threshold:.2f}")
    print(f"   - Teams scoring below {standardizer.auto_add_threshold:.2f} will be auto-added")
    print()
    
    # Test cases: mix of existing variations and completely new teams
    test_cases = [
        # Should match existing teams
        ("Kaunas Zalgiris", "basketball", "Should match 'Kauno Zalgiris'"),
        ("BC Kaunas Zalgiris", "basketball", "Should match 'Kauno Zalgiris'"),
        ("Real Madrid Basketball", "basketball", "Should match 'Real Madrid'"),
        ("Barcelona FC", "soccer", "Should match 'Barcelona'"),
        ("Bayern Munich", "soccer", "Should match 'FC Bayern Munchen'"),
        ("Liverpool FC", "soccer", "Should match 'Liverpool'"),
        
        # New teams that should be auto-added
        ("Lietuvos Rytas Vilnius", "basketball", "New Lithuanian team"),
        ("Žalgiris-2", "basketball", "Reserve team"),
        ("Manchester United Academy", "soccer", "Academy team"),
        ("Real Sociedad B", "soccer", "Reserve team"),
        ("Vilnius Basketball Club", "basketball", "New club"),
        ("Paris FC", "soccer", "Different from PSG"),
        
        # Edge cases
        ("", "basketball", "Empty name"),
        ("X", "basketball", "Very short name"),
        ("Team with Very Long Name That Probably Doesn't Exist Anywhere", "soccer", "Very long name"),
        
        # Different sports
        ("New Tennis Player", "tennis", "Tennis player"),
        ("Unknown Hockey Team", "hockey", "New sport category"),
    ]
    
    print(f"🎯 Running {len(test_cases)} test cases:")
    print()
    
    results = []
    
    for i, (team_name, sport, description) in enumerate(test_cases, 1):
        print(f"Test {i:2d}: {description}")
        print(f"         Input: '{team_name}' ({sport})")
        
        if not team_name.strip():
            print(f"         Result: Skipping empty team name")
            print(f"         Status: ⚠️  EMPTY NAME")
            print()
            continue
        
        # Get detailed results
        result, details = standardizer.standardize_team_name(
            team_name, sport, auto_add=True, return_details=True
        )
        
        # Format status message
        status_icons = {
            "exact_match": "✅",
            "fuzzy_match": "🔍", 
            "auto_added": "🆕",
            "no_match_no_add": "❌",
            "empty": "⚠️"
        }
        
        status_messages = {
            "exact_match": f"EXACT MATCH (100% similarity)",
            "fuzzy_match": f"FUZZY MATCH (similarity: {details.get('score', 0):.1%})",
            "auto_added": f"AUTO-ADDED (best existing: {details.get('best_existing_score', 0):.1%})",
            "no_match_no_add": f"NO MATCH (best: {details.get('best_existing_score', 0):.1%}, threshold: {details.get('auto_add_threshold', 0):.1%})",
            "empty": "EMPTY NAME"
        }
        
        status = details.get('status', 'unknown')
        icon = status_icons.get(status, "❓")
        message = status_messages.get(status, status)
        
        print(f"         Result: '{result}'")
        print(f"         Status: {icon} {message}")
        
        # Store result for summary
        results.append({
            'input': team_name,
            'output': result,
            'sport': sport,
            'status': status,
            'details': details
        })
        
        print()
    
    # Show summary of newly added teams
    new_teams = standardizer.get_newly_added_teams()
    if new_teams:
        print(f"🆕 New teams added during testing ({len(new_teams)}):")
        for team in new_teams:
            print(f"   - {team['sport']}: {team['canonical_team_name']}")
        print()
    else:
        print(f"ℹ️  No new teams were added during testing")
        print()
    
    # Show statistics
    stats = standardizer.get_statistics()
    print(f"📈 Final Statistics:")
    print(f"   - Total teams: {stats['total_teams']} (was {len(teams_data)})")
    print(f"   - New teams this session: {stats['newly_added_this_session']}")
    print(f"   - Empty names: {stats['empty_names']}")
    print()
    
    print(f"   Teams by sport:")
    for sport, count in sorted(stats['sports'].items()):
        original_count = sport_counts.get(sport, 0)
        change = count - original_count
        change_str = f" (+{change})" if change > 0 else ""
        print(f"     - {sport}: {count}{change_str}")
    print()
    
    # Summary by result type
    result_summary = {}
    for result in results:
        status = result['status']
        result_summary[status] = result_summary.get(status, 0) + 1
    
    print(f"📊 Results Summary:")
    for status, count in sorted(result_summary.items()):
        icon = status_icons.get(status, "❓")
        print(f"   {icon} {status.replace('_', ' ').title()}: {count}")
    print()
    
    # Ask user if they want to save the updated teams
    if new_teams:
        response = input(f"💾 Save {len(new_teams)} new teams to 'teams_with_additions.json'? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            success = standardizer.save_teams_to_file("teams_with_additions.json")
            if success:
                print(f"✅ Saved updated teams to teams_with_additions.json")
            else:
                print(f"❌ Failed to save teams")
        else:
            print(f"ℹ️  Teams not saved")

def test_api_response_processing():
    """Test processing a mock API response"""
    
    print("\n" + "="*65)
    print("🌐 Testing API Response Processing with Auto-Add")
    print("="*65)
    
    # Load teams
    try:
        with open("teams.json", 'r') as f:
            teams_data = json.load(f)
    except:
        print("❌ Could not load teams.json")
        return
    
    # Initialize standardizer
    standardizer = PurePythonTeamStandardizer(
        teams_data,
        threshold=0.75,
        auto_add_threshold=0.60
    )
    
    # Mock API response from a betting site
    mock_api_response = {
        "sport": "basketball",
        "league": "Lithuanian Basketball League",
        "matches": [
            {
                "match_id": "12345",
                "home_team": "Zalgiris Kaunas",        # Should match existing
                "away_team": "Nevezis Kedainiai",      # Might be new
                "odds": {"home": 1.25, "away": 3.80}
            },
            {
                "match_id": "12346", 
                "home_team": "Lietkabelis Panevezys",  # Should match existing
                "away_team": "Siauliai Basketball",    # Might be new
                "odds": {"home": 2.10, "away": 1.75}
            }
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    print("📥 Processing mock API response...")
    print(f"Original response: {len(json.dumps(mock_api_response))} characters")
    print()
    
    # Process the response
    processed = standardizer.process_api_response(
        mock_api_response, 
        auto_save=False  # Don't save during demo
    )
    
    # Show the results
    print("📤 Processed response:")
    print(json.dumps(processed, indent=2))
    print()
    
    # Show processing summary
    summary = processed.get("_processing_summary", {})
    print("📋 Processing Summary:")
    print(f"   - Teams processed: {summary.get('teams_processed', 0)}")
    print(f"   - Changes made: {summary.get('changes_made', False)}")
    print(f"   - New teams added: {summary.get('new_teams_added', 0)}")
    print()
    
    # Show any new teams
    new_teams = standardizer.get_newly_added_teams()
    if new_teams:
        print("🆕 New teams discovered in API response:")
        for team in new_teams:
            print(f"   - {team['canonical_team_name']} ({team['sport']})")
    else:
        print("ℹ️  No new teams discovered in API response")

def main():
    """Main test function"""
    try:
        test_auto_add_functionality()
        test_api_response_processing()
        
        print("\n" + "="*65)
        print("✅ Auto-add testing completed successfully!")
        print("="*65)
        print()
        print("💡 Key Benefits of Auto-Add:")
        print("   - Automatically discovers new teams from betting APIs")
        print("   - Maintains consistency with existing canonical names") 
        print("   - Configurable similarity thresholds")
        print("   - Tracks and logs all additions")
        print("   - Works with any sport category")
        print("   - No manual intervention required")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 