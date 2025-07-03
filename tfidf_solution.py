import json
import logging
from typing import Dict, List, Optional, Tuple
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class TFIDFTeamMatcher:
    """Advanced team name standardizer using TF-IDF vectorization"""
    
    def __init__(self, threshold: float = 0.6, ngram_range: Tuple[int, int] = (1, 3)):
        self.threshold = threshold
        self.ngram_range = ngram_range
        self.vectorizer = None
        self.canonical_vectors = None
        self.canonical_teams = []
        
    def _preprocess_text(self, text: str) -> str:
        """Preprocess team name for better vectorization"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common prefixes/suffixes but keep them as separate tokens
        # This allows TF-IDF to learn their importance
        text = re.sub(r'\b(fc|cf|sc|ac|bc|fk|kk)\b', 'club', text)
        text = re.sub(r'\b(real|club|team)\b', lambda m: f"prefix_{m.group(1)}", text)
        
        # Replace special characters with spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def fit(self, canonical_teams: List[str]) -> None:
        """Fit the TF-IDF vectorizer on canonical team names"""
        if not canonical_teams:
            return
            
        self.canonical_teams = canonical_teams
        
        # Preprocess all team names
        processed_teams = [self._preprocess_text(team) for team in canonical_teams]
        
        # Create and fit TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            analyzer='char_wb',  # Character n-grams within word boundaries
            lowercase=True,
            strip_accents='unicode',
            min_df=1,
            max_features=5000
        )
        
        # Fit and transform canonical team names
        self.canonical_vectors = self.vectorizer.fit_transform(processed_teams)
        
        logger.info(f"TF-IDF vectorizer fitted on {len(canonical_teams)} teams")
    
    def find_best_match(self, query_team: str) -> Optional[Tuple[str, float]]:
        """Find the best matching canonical team name"""
        if not query_team or self.vectorizer is None:
            return None
        
        # Preprocess query team name
        processed_query = self._preprocess_text(query_team)
        
        # Transform query to TF-IDF vector
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate cosine similarities
        similarities = cosine_similarity(query_vector, self.canonical_vectors).flatten()
        
        # Find best match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score >= self.threshold:
            return (self.canonical_teams[best_idx], best_score)
        
        return None

class AdvancedTeamStandardizer:
    """
    Advanced team name standardizer combining multiple approaches
    """
    
    def __init__(self):
        self.teams_map = []
        self.tfidf_matchers = {}  # One matcher per sport
        
    def load_teams_map(self, teams_data: List[Dict]) -> None:
        """Load teams mapping and prepare matchers for each sport"""
        self.teams_map = teams_data
        
        # Group teams by sport
        sports_teams = {}
        for team in teams_data:
            sport = team.get('sport', '').lower()
            canonical_name = team.get('canonical_team_name', '')
            
            if sport and canonical_name:
                if sport not in sports_teams:
                    sports_teams[sport] = []
                sports_teams[sport].append(canonical_name)
        
        # Create and fit TF-IDF matcher for each sport
        for sport, teams in sports_teams.items():
            if teams:
                matcher = TFIDFTeamMatcher(threshold=0.5)
                matcher.fit(teams)
                self.tfidf_matchers[sport] = matcher
                logger.info(f"Created TF-IDF matcher for {sport} with {len(teams)} teams")
    
    def standardize_team_name(self, team_name: str, sport: str, auto_add: bool = True) -> str:
        """Standardize a team name using TF-IDF matching"""
        if not team_name or not team_name.strip():
            return ""
        
        sport = sport.lower()
        
        # Check if we have a matcher for this sport
        if sport not in self.tfidf_matchers:
            if auto_add:
                # Create new team entry
                new_team = {
                    "sport": sport,
                    "canonical_team_name": team_name.strip()
                }
                self.teams_map.append(new_team)
                
                # Create new matcher for this sport
                matcher = TFIDFTeamMatcher(threshold=0.5)
                matcher.fit([team_name.strip()])
                self.tfidf_matchers[sport] = matcher
                
                return team_name.strip()
            return team_name
        
        # Use TF-IDF matcher to find best match
        matcher = self.tfidf_matchers[sport]
        match_result = matcher.find_best_match(team_name)
        
        if match_result:
            canonical_name, score = match_result
            logger.info(f"TF-IDF match: '{team_name}' -> '{canonical_name}' (score: {score:.3f})")
            return canonical_name
        
        # No match found
        if auto_add:
            # Add new team to the map
            new_team = {
                "sport": sport,
                "canonical_team_name": team_name.strip()
            }
            self.teams_map.append(new_team)
            
            # Refit the matcher with the new team
            sport_teams = [team['canonical_team_name'] for team in self.teams_map 
                          if team.get('sport', '').lower() == sport]
            matcher.fit(sport_teams)
            
            logger.info(f"Added new team: {new_team}")
            return team_name.strip()
        
        return team_name

# Hybrid approach combining multiple methods
class HybridTeamMatcher:
    """
    Hybrid team matcher that combines TF-IDF, fuzzy matching, and n-grams
    """
    
    def __init__(self):
        self.tfidf_weight = 0.4
        self.fuzzy_weight = 0.4
        self.ngram_weight = 0.2
        
    def calculate_hybrid_similarity(self, team1: str, team2: str) -> float:
        """Calculate similarity using hybrid approach"""
        
        # 1. TF-IDF similarity (simplified version)
        tfidf_matcher = TFIDFTeamMatcher(threshold=0.0)
        tfidf_matcher.fit([team1, team2])
        tfidf_score = 0.0
        if tfidf_matcher.canonical_vectors is not None:
            similarities = cosine_similarity(
                tfidf_matcher.canonical_vectors[0:1], 
                tfidf_matcher.canonical_vectors[1:2]
            )
            tfidf_score = similarities[0][0]
        
        # 2. Simple fuzzy similarity (using difflib)
        from difflib import SequenceMatcher
        fuzzy_score = SequenceMatcher(None, team1.lower(), team2.lower()).ratio()
        
        # 3. N-gram similarity
        from ngram_solution import NGramTeamMatcher
        ngram_matcher = NGramTeamMatcher(threshold=0.0)
        ngram_score = ngram_matcher.calculate_similarity(team1, team2)
        
        # Combine scores
        hybrid_score = (
            self.tfidf_weight * tfidf_score +
            self.fuzzy_weight * fuzzy_score +
            self.ngram_weight * ngram_score
        )
        
        return hybrid_score

# Example usage and testing
if __name__ == "__main__":
    # Test with sample data
    sample_teams = [
        {"sport": "basketball", "canonical_team_name": "BC Kaunas Zalgiris"},
        {"sport": "basketball", "canonical_team_name": "Real Madrid"},
        {"sport": "soccer", "canonical_team_name": "FC Barcelona"},
        {"sport": "soccer", "canonical_team_name": "Manchester City"},
        {"sport": "soccer", "canonical_team_name": "Liverpool FC"},
    ]
    
    # Test TF-IDF approach
    standardizer = AdvancedTeamStandardizer()
    standardizer.load_teams_map(sample_teams)
    
    test_cases = [
        ("Kaunas Zalgiris", "basketball"),
        ("Zalgiris Kaunas", "basketball"),
        ("Real Madrid Basketball", "basketball"),
        ("Barcelona", "soccer"),
        ("Man City", "soccer"),
        ("Liverpool", "soccer"),
        ("New Team", "soccer"),  # Should be added as new
    ]
    
    print("TF-IDF Results:")
    for team_name, sport in test_cases:
        result = standardizer.standardize_team_name(team_name, sport)
        print(f"'{team_name}' ({sport}) -> '{result}'")
    
    print("\nHybrid Similarity Testing:")
    hybrid = HybridTeamMatcher()
    test_pairs = [
        ("Kaunas Zalgiris", "BC Kaunas Zalgiris"),
        ("Real Madrid", "Real Madrid Basketball"),
        ("Barcelona", "FC Barcelona"),
        ("Man City", "Manchester City"),
    ]
    
    for team1, team2 in test_pairs:
        score = hybrid.calculate_hybrid_similarity(team1, team2)
        print(f"'{team1}' vs '{team2}': {score:.3f}") 