import json
import logging
from typing import Dict, List, Optional, Set
from collections import Counter
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class NGramTeamMatcher:
    """Team name standardizer using N-gram similarity"""
    
    def __init__(self, n: int = 3, threshold: float = 0.6):
        self.n = n
        self.threshold = threshold
    
    def _generate_ngrams(self, text: str, n: int) -> Set[str]:
        """Generate n-grams from text"""
        text = text.lower().strip()
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    
    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union
    
    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts using character frequencies"""
        # Count character frequencies
        counter1 = Counter(text1.lower())
        counter2 = Counter(text2.lower())
        
        # Get all unique characters
        all_chars = set(counter1.keys()) | set(counter2.keys())
        
        # Create vectors
        vec1 = [counter1.get(char, 0) for char in all_chars]
        vec2 = [counter2.get(char, 0) for char in all_chars]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name for comparison"""
        if not name:
            return ""
        
        # Remove common prefixes/suffixes
        name = re.sub(r'\b(FC|CF|SC|AC|BC|FK|KK|Club|Team|Basketball|Football|Real|Club)\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(de|del|la|le|the|of|and|&)\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[^\w\s]', ' ', name)  # Remove special characters
        name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
        return name.lower()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two team names using multiple methods"""
        
        # Normalize texts
        norm1 = self._normalize_team_name(text1)
        norm2 = self._normalize_team_name(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Calculate different similarity measures
        scores = []
        
        # 1. N-gram Jaccard similarity
        ngrams1 = self._generate_ngrams(norm1, self.n)
        ngrams2 = self._generate_ngrams(norm2, self.n)
        jaccard_score = self._jaccard_similarity(ngrams1, ngrams2)
        scores.append(jaccard_score)
        
        # 2. Character-level cosine similarity
        cosine_score = self._cosine_similarity(norm1, norm2)
        scores.append(cosine_score)
        
        # 3. Sequence matcher similarity (built-in difflib)
        seq_score = SequenceMatcher(None, norm1, norm2).ratio()
        scores.append(seq_score)
        
        # 4. Word-level Jaccard similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        word_jaccard = self._jaccard_similarity(words1, words2)
        scores.append(word_jaccard)
        
        # Return weighted average (you can adjust weights based on your needs)
        weights = [0.3, 0.2, 0.3, 0.2]  # N-gram, cosine, sequence, word
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return weighted_score
    
    def find_best_match(self, query_team: str, candidate_teams: List[str]) -> Optional[tuple]:
        """Find the best matching team name from candidates"""
        if not query_team or not candidate_teams:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidate_teams:
            score = self.calculate_similarity(query_team, candidate)
            if score > best_score and score >= self.threshold:
                best_score = score
                best_match = candidate
        
        if best_match:
            return (best_match, best_score)
        
        return None

# Example usage
if __name__ == "__main__":
    matcher = NGramTeamMatcher(n=3, threshold=0.6)
    
    # Test cases
    canonical_teams = [
        "BC Kaunas Zalgiris",
        "Real Madrid",
        "FC Barcelona", 
        "Manchester City",
        "Liverpool FC"
    ]
    
    test_teams = [
        "Kaunas Zalgiris",
        "Zalgiris Kaunas",
        "Real Madrid CF",
        "Barcelona",
        "Man City",
        "Liverpool"
    ]
    
    for test_team in test_teams:
        result = matcher.find_best_match(test_team, canonical_teams)
        if result:
            print(f"'{test_team}' -> '{result[0]}' (score: {result[1]:.3f})")
        else:
            print(f"'{test_team}' -> No match found") 