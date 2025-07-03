#!/usr/bin/env python3
"""
Test script to demonstrate all team name standardization solutions
using the existing teams.json data.
"""

import json
import time
from typing import List, Dict

def load_teams_data(filename: str = "teams.json") -> List[Dict]:
    """Load teams data from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please ensure the file exists in the current directory.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {filename}")
        return []

def test_rapidfuzz_solution(teams_data: List[Dict]):
    """Test the RapidFuzz solution"""
    print("=" * 60)
    print("TESTING RAPIDFUZZ SOLUTION")
    print("=" * 60)
    
    try:
        # For testing without Cloud Storage, we'll modify the class temporarily
        from team_name_standardizer import TeamNameStandardizer
        
        class LocalTeamStandardizer(TeamNameStandardizer):
            def __init__(self, teams_data):
                self.teams_map = teams_data
                # Skip Cloud Storage initialization for local testing
            
            def _save_teams_map(self):
                # Skip saving for testing
                pass
        
        standardizer = LocalTeamStandardizer(teams_data)
        
        # Test cases with variations of existing team names
        test_cases = [
            ("Kaunas Zalgiris", "basketball"),  # Should match "Kauno Zalgiris"
            ("Real Madrid CF", "soccer"),        # Should match "Real Madrid"
            ("FC Barcelona", "soccer"),          # Should match "Barcelona"
            ("Man City", "soccer"),              # Should match "Manchester City"
            ("Bayern Munich", "soccer"),         # Should match "FC Bayern Munchen"
            ("Liverpool FC", "soccer"),          # Should match "Liverpool"
            ("Lakers", "basketball"),            # Should match "Los Angeles Lakers"
            ("New Team XYZ", "soccer"),          # Should be added as new
        ]
        
        print(f"Testing with {len(teams_data)} existing teams...")
        print()
        
        for team_name, sport in test_cases:
            start_time = time.time()
            result = standardizer.standardize_team_name(team_name, sport)
            end_time = time.time()
            
            status = "MATCHED" if result != team_name else "NEW TEAM"
            print(f"Input: '{team_name}' ({sport})")
            print(f"Output: '{result}' [{status}]")
            print(f"Time: {(end_time - start_time)*1000:.2f}ms")
            print("-" * 40)
        
    except ImportError as e:
        print(f"Error importing RapidFuzz solution: {e}")
        print("Please install required dependencies: pip install rapidfuzz")

def test_ngram_solution(teams_data: List[Dict]):
    """Test the N-gram solution"""
    print("=" * 60)
    print("TESTING N-GRAM SOLUTION")
    print("=" * 60)
    
    try:
        from ngram_solution import NGramTeamMatcher
        
        matcher = NGramTeamMatcher(n=3, threshold=0.6)
        
        # Group teams by sport
        sports_teams = {}
        for team in teams_data:
            sport = team.get('sport', '').lower()
            canonical_name = team.get('canonical_team_name', '')
            if sport and canonical_name:
                if sport not in sports_teams:
                    sports_teams[sport] = []
                sports_teams[sport].append(canonical_name)
        
        test_cases = [
            ("Kaunas Zalgiris", "basketball"),
            ("Real Madrid CF", "soccer"),
            ("FC Barcelona", "soccer"),
            ("Man City", "soccer"),
            ("Bayern Munich", "soccer"),
            ("Liverpool FC", "soccer"),
        ]
        
        print(f"Testing with sports: {list(sports_teams.keys())}")
        print()
        
        for team_name, sport in test_cases:
            if sport in sports_teams:
                start_time = time.time()
                result = matcher.find_best_match(team_name, sports_teams[sport])
                end_time = time.time()
                
                if result:
                    matched_team, score = result
                    print(f"Input: '{team_name}' ({sport})")
                    print(f"Match: '{matched_team}' (score: {score:.3f})")
                    print(f"Time: {(end_time - start_time)*1000:.2f}ms")
                else:
                    print(f"Input: '{team_name}' ({sport})")
                    print("No match found (below threshold)")
                print("-" * 40)
            else:
                print(f"No teams found for sport: {sport}")
                
    except ImportError as e:
        print(f"Error importing N-gram solution: {e}")

def test_tfidf_solution(teams_data: List[Dict]):
    """Test the TF-IDF solution"""
    print("=" * 60)
    print("TESTING TF-IDF SOLUTION")
    print("=" * 60)
    
    try:
        from tfidf_solution import AdvancedTeamStandardizer
        
        standardizer = AdvancedTeamStandardizer()
        standardizer.load_teams_map(teams_data)
        
        test_cases = [
            ("Kaunas Zalgiris", "basketball"),
            ("Real Madrid CF", "soccer"),
            ("FC Barcelona", "soccer"),
            ("Man City", "soccer"),
            ("Bayern Munich", "soccer"),
            ("Liverpool FC", "soccer"),
            ("Milwaukee Bucks Basketball", "basketball"),
        ]
        
        print(f"TF-IDF matchers created for sports: {list(standardizer.tfidf_matchers.keys())}")
        print()
        
        for team_name, sport in test_cases:
            start_time = time.time()
            result = standardizer.standardize_team_name(team_name, sport, auto_add=False)
            end_time = time.time()
            
            status = "MATCHED" if result != team_name else "NO MATCH"
            print(f"Input: '{team_name}' ({sport})")
            print(f"Output: '{result}' [{status}]")
            print(f"Time: {(end_time - start_time)*1000:.2f}ms")
            print("-" * 40)
            
    except ImportError as e:
        print(f"Error importing TF-IDF solution: {e}")
        print("Please install required dependencies: pip install scikit-learn numpy")

def compare_solutions_performance(teams_data: List[Dict]):
    """Compare performance of different solutions"""
    print("=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    
    test_team = "Real Madrid CF"
    sport = "soccer"
    
    # Get soccer teams for comparison
    soccer_teams = [team['canonical_team_name'] for team in teams_data 
                   if team.get('sport', '').lower() == 'soccer' and team.get('canonical_team_name')]
    
    print(f"Testing with: '{test_team}' against {len(soccer_teams)} soccer teams")
    print()
    
    results = {}
    
    # Test RapidFuzz
    try:
        from team_name_standardizer import TeamNameStandardizer
        class LocalStandardizer(TeamNameStandardizer):
            def __init__(self, teams_data):
                self.teams_map = teams_data
            def _save_teams_map(self):
                pass
        
        standardizer = LocalStandardizer(teams_data)
        
        times = []
        for _ in range(10):  # Run 10 times for average
            start = time.time()
            result = standardizer.standardize_team_name(test_team, sport)
            end = time.time()
            times.append(end - start)
        
        avg_time = sum(times) / len(times) * 1000
        results['RapidFuzz'] = {'result': result, 'avg_time_ms': avg_time}
        
    except ImportError:
        results['RapidFuzz'] = {'result': 'N/A', 'avg_time_ms': 'N/A (missing dependency)'}
    
    # Test N-gram
    try:
        from ngram_solution import NGramTeamMatcher
        matcher = NGramTeamMatcher(n=3, threshold=0.6)
        
        times = []
        for _ in range(10):
            start = time.time()
            result = matcher.find_best_match(test_team, soccer_teams)
            end = time.time()
            times.append(end - start)
        
        avg_time = sum(times) / len(times) * 1000
        match_result = result[0] if result else "No match"
        results['N-gram'] = {'result': match_result, 'avg_time_ms': avg_time}
        
    except ImportError:
        results['N-gram'] = {'result': 'N/A', 'avg_time_ms': 'N/A (missing dependency)'}
    
    # Test TF-IDF
    try:
        from tfidf_solution import AdvancedTeamStandardizer
        standardizer = AdvancedTeamStandardizer()
        standardizer.load_teams_map(teams_data)
        
        times = []
        for _ in range(10):
            start = time.time()
            result = standardizer.standardize_team_name(test_team, sport, auto_add=False)
            end = time.time()
            times.append(end - start)
        
        avg_time = sum(times) / len(times) * 1000
        results['TF-IDF'] = {'result': result, 'avg_time_ms': avg_time}
        
    except ImportError:
        results['TF-IDF'] = {'result': 'N/A', 'avg_time_ms': 'N/A (missing dependency)'}
    
    # Print comparison table
    print(f"{'Solution':<15} {'Result':<20} {'Avg Time (ms)':<15}")
    print("-" * 50)
    for solution, data in results.items():
        result = data['result'][:18] + "..." if len(str(data['result'])) > 20 else data['result']
        time_str = f"{data['avg_time_ms']:.2f}" if isinstance(data['avg_time_ms'], (int, float)) else str(data['avg_time_ms'])
        print(f"{solution:<15} {result:<20} {time_str:<15}")

def analyze_data_statistics(teams_data: List[Dict]):
    """Analyze the loaded teams data"""
    print("=" * 60)
    print("DATA ANALYSIS")
    print("=" * 60)
    
    # Count teams by sport
    sport_counts = {}
    total_teams = 0
    empty_names = 0
    
    for team in teams_data:
        sport = team.get('sport', 'unknown').lower()
        canonical_name = team.get('canonical_team_name', '')
        
        if not canonical_name.strip():
            empty_names += 1
        else:
            total_teams += 1
            sport_counts[sport] = sport_counts.get(sport, 0) + 1
    
    print(f"Total teams: {total_teams}")
    print(f"Empty team names: {empty_names}")
    print(f"Total entries: {len(teams_data)}")
    print()
    
    print("Teams by sport:")
    for sport, count in sorted(sport_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_teams) * 100
        print(f"  {sport.capitalize():<15}: {count:>4} teams ({percentage:.1f}%)")
    
    print()
    
    # Sample team names for each sport
    print("Sample team names by sport:")
    for sport in sorted(sport_counts.keys()):
        sport_teams = [team['canonical_team_name'] for team in teams_data 
                      if team.get('sport', '').lower() == sport and team.get('canonical_team_name', '').strip()]
        if sport_teams:
            samples = sport_teams[:3]  # First 3 teams
            print(f"  {sport.capitalize()}: {', '.join(samples)}")

def main():
    """Main function to run all tests"""
    print("Team Name Standardizer - Solution Testing")
    print("Loading teams data...")
    
    teams_data = load_teams_data()
    if not teams_data:
        return
    
    print(f"Loaded {len(teams_data)} team entries")
    print()
    
    # Run analysis
    analyze_data_statistics(teams_data)
    
    # Test each solution
    test_rapidfuzz_solution(teams_data)
    test_ngram_solution(teams_data)
    test_tfidf_solution(teams_data)
    
    # Performance comparison
    compare_solutions_performance(teams_data)
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
    print("\nRecommendations:")
    print("1. For production use: RapidFuzz solution (best balance)")
    print("2. For minimal dependencies: N-gram solution")
    print("3. For large datasets: TF-IDF solution")
    print("4. Consider hybrid approach for maximum accuracy")

if __name__ == "__main__":
    main() 