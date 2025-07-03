#!/usr/bin/env python3
"""
Enhanced Pure Python Team Name Standardizer with Auto-Add Functionality
No external dependencies - uses only Python standard library
Perfect for Cloud Functions where you want to avoid compilation issues

Features:
- Automatic addition of new teams when no match found
- Configurable similarity thresholds for auto-add decisions
- Google Cloud Storage integration for persistence
- Manual team addition methods
- Statistics and cleanup utilities
"""

import json
import logging
import re
import difflib
from typing import Dict, List, Optional, Tuple, Set
from collections import Counter
import functools
import operator
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PurePythonFuzzyMatcher:
    """
    Pure Python fuzzy string matcher using multiple algorithms
    No external dependencies required
    """
    
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Expand common city abbreviations
        city_abbrev = {
            r'\bla\b': 'los angeles',
            r'\bn\.y\.\b': 'new york',
            r'\bny\b': 'new york',
            r'\bs\.f\.\b': 'san francisco',
            r'\bsf\b': 'san francisco',
            r'\bd\.c\.\b': 'washington',
            r'\bdc\b': 'washington',
            r'\bl\.a\.\b': 'los angeles',
            r'\bchi\b': 'chicago',
            r'\bphila\b': 'philadelphia',
            r'\bn\.o\.\b': 'new orleans',
            r'\bno\b': 'new orleans',
            r'\bs\.a\.\b': 'san antonio',
            r'\bsa\b': 'san antonio',
            r'\butd\b': 'united',
            r'\bfc\b': '',  # Football Club is often optional
            r'\bsc\b': '',  # Sport Club is often optional
            r'\bac\b': '',  # Athletic Club is often optional
            r'\bbc\b': '',  # Basketball Club is often optional
            r'\bht\b': 'heat',  # Example: Miami Ht -> Miami Heat
            r'\bmn\b': 'minnesota',
            r'\bman\.\b': 'manchester'
        }
        
        for abbrev, expansion in city_abbrev.items():
            text = re.sub(abbrev, expansion, text, flags=re.IGNORECASE)
        
        # Remove common prefixes/suffixes
        patterns_to_remove = [
            r'\b(fc|cf|sc|ac|bc|fk|kk|club|team|basketball|football)\b',
            r'\b(real|de|del|la|le|the|of|and|&)\b'
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove special characters and normalize whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if not s1:
            return len(s2)
        if not s2:
            return len(s1)
        
        # Create matrix
        rows = len(s1) + 1
        cols = len(s2) + 1
        matrix = [[0] * cols for _ in range(rows)]
        
        # Initialize first row and column
        for i in range(rows):
            matrix[i][0] = i
        for j in range(cols):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, rows):
            for j in range(1, cols):
                if s1[i-1] == s2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        return matrix[rows-1][cols-1]
    
    def _levenshtein_ratio(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio based on Levenshtein distance"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        distance = self._levenshtein_distance(s1, s2)
        return 1.0 - (distance / max_len)
    
    def _jaro_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro similarity between two strings"""
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        
        # Calculate the match window
        match_window = max(len1, len2) // 2 - 1
        if match_window < 0:
            match_window = 0
        
        # Initialize match arrays
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        
        matches = 0
        transpositions = 0
        
        # Identify matches
        for i in range(len1):
            start = max(0, i - match_window)
            end = min(i + match_window + 1, len2)
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Count transpositions
        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        # Calculate Jaro similarity
        jaro = (matches / len1 + matches / len2 + 
                (matches - transpositions / 2) / matches) / 3.0
        
        return jaro
    
    def _get_ngrams(self, text: str, n: int = 2) -> Set[str]:
        """Generate n-grams from text"""
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    
    def _jaccard_similarity(self, s1: str, s2: str, n: int = 2) -> float:
        """Calculate Jaccard similarity using n-grams"""
        ngrams1 = self._get_ngrams(s1, n)
        ngrams2 = self._get_ngrams(s2, n)
        
        if not ngrams1 and not ngrams2:
            return 1.0
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def _token_sort_ratio(self, s1: str, s2: str) -> float:
        """Calculate similarity after sorting tokens"""
        tokens1 = sorted(s1.split())
        tokens2 = sorted(s2.split())
        
        sorted_s1 = ' '.join(tokens1)
        sorted_s2 = ' '.join(tokens2)
        
        return self._levenshtein_ratio(sorted_s1, sorted_s2)
    
    def _token_set_ratio(self, s1: str, s2: str) -> float:
        """Calculate similarity using token sets"""
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())
        
        if not tokens1 and not tokens2:
            return 1.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        # Create strings from different combinations
        sorted_inter = ' '.join(sorted(intersection))
        sorted_1 = ' '.join(sorted(tokens1))
        sorted_2 = ' '.join(sorted(tokens2))
        
        # Calculate ratios for different combinations
        ratios = [
            self._levenshtein_ratio(sorted_inter, sorted_1),
            self._levenshtein_ratio(sorted_inter, sorted_2),
            self._levenshtein_ratio(sorted_1, sorted_2)
        ]
        
        return max(ratios)
    
    def calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate comprehensive similarity score using multiple algorithms
        Returns a value between 0.0 and 1.0
        """
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        # Normalize strings
        norm1 = self._normalize_text(s1)
        norm2 = self._normalize_text(s2)
        
        if norm1 == norm2:
            return 1.0
        
        # Calculate different similarity measures
        scores = []
        
        # 1. Levenshtein ratio
        lev_score = self._levenshtein_ratio(norm1, norm2)
        scores.append(lev_score)
        
        # 2. Jaro similarity
        jaro_score = self._jaro_similarity(norm1, norm2)
        scores.append(jaro_score)
        
        # 3. N-gram Jaccard similarity
        jaccard_score = self._jaccard_similarity(norm1, norm2, n=2)
        scores.append(jaccard_score)
        
        # 4. Token sort ratio
        token_sort_score = self._token_sort_ratio(norm1, norm2)
        scores.append(token_sort_score)
        
        # 5. Token set ratio
        token_set_score = self._token_set_ratio(norm1, norm2)
        scores.append(token_set_score)
        
        # 6. Difflib sequence matcher (another reference)
        difflib_score = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        scores.append(difflib_score)
        
        # Weighted average (adjusted weights to prioritize token-based matching)
        # Original weights: [0.25, 0.15, 0.15, 0.20, 0.15, 0.10]
        weights = [0.20, 0.10, 0.10, 0.30, 0.25, 0.05]  # Increased weight for token_sort and token_set
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return min(1.0, max(0.0, weighted_score))  # Ensure it's between 0 and 1
    
    def find_best_match(self, query: str, candidates: List[str]) -> Optional[Tuple[str, float]]:
        """Find the best matching candidate for the query"""
        if not query or not candidates:
            return None
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self.calculate_similarity(query, candidate)
            if score > best_score and score >= self.threshold:
                best_score = score
                best_match = candidate
        
        if best_match:
            return (best_match, best_score)
        
        return None

class PurePythonTeamStandardizer:
    """
    Complete team name standardizer using pure Python
    Features automatic team addition and Cloud Storage integration
    """
    
    def __init__(self, teams_data: List[Dict] = None, threshold: float = 0.75, 
                 auto_add_threshold: float = 0.70, cloud_storage_bucket: str = None):
        self.teams_map = teams_data or []
        self.threshold = threshold
        self.auto_add_threshold = auto_add_threshold  # Threshold below which we consider it a new team
        self.cloud_storage_bucket = cloud_storage_bucket
        self.matcher = PurePythonFuzzyMatcher(threshold)
        
        # Cache for performance
        self._sport_teams_cache = {}
        self._new_teams_added = []  # Track newly added teams
        self._build_cache()
    
    def _build_cache(self):
        """Build cache of teams by sport for faster lookups"""
        self._sport_teams_cache = {}
        for team in self.teams_map:
            sport = team.get('sport', '').lower()
            canonical_name = team.get('canonical_team_name', '')
            
            if sport and canonical_name:
                if sport not in self._sport_teams_cache:
                    self._sport_teams_cache[sport] = []
                self._sport_teams_cache[sport].append(canonical_name)
    
    def load_teams_from_file(self, filename: str = "teams.json"):
        """Load teams data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.teams_map = json.load(f)
            self._build_cache()
            logger.info(f"Loaded {len(self.teams_map)} teams from {filename}")
            return True
        except FileNotFoundError:
            logger.error(f"File {filename} not found")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            return False
    
    def load_teams_from_cloud_storage(self, filename: str = "teams.json"):
        """Load teams data from Google Cloud Storage"""
        if not self.cloud_storage_bucket:
            logger.error("Cloud Storage bucket not configured")
            return False
        
        try:
            # This would be the actual GCS implementation
            # For now, fallback to local file
            return self.load_teams_from_file(filename)
        except Exception as e:
            logger.error(f"Error loading from Cloud Storage: {e}")
            return False
    
    def save_teams_to_file(self, filename: str = "teams.json", backup: bool = True):
        """Save teams data to JSON file with optional backup"""
        try:
            # Create backup if requested
            if backup and os.path.exists(filename):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{filename}.backup_{timestamp}"
                os.rename(filename, backup_filename)
                logger.info(f"Created backup: {backup_filename}")
            
            # Save the current data
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.teams_map, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.teams_map)} teams to {filename}")
            
            # Log newly added teams
            if self._new_teams_added:
                logger.info(f"New teams added in this session: {len(self._new_teams_added)}")
                for team in self._new_teams_added[-5:]:  # Show last 5
                    logger.info(f"  - {team['sport']}: {team['canonical_team_name']}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving teams to {filename}: {e}")
            return False
    
    def save_teams_to_cloud_storage(self, filename: str = "teams.json"):
        """Save teams data to Google Cloud Storage"""
        if not self.cloud_storage_bucket:
            logger.error("Cloud Storage bucket not configured")
            return False
        
        try:
            # This would be the actual GCS implementation
            # For now, save locally and then upload would happen here
            success = self.save_teams_to_file(filename, backup=False)
            if success:
                logger.info(f"Would upload {filename} to gs://{self.cloud_storage_bucket}/")
            return success
        except Exception as e:
            logger.error(f"Error saving to Cloud Storage: {e}")
            return False
    
    def add_team_manually(self, team_name: str, sport: str, force: bool = False) -> bool:
        """
        Manually add a team to the map
        
        Args:
            team_name: The canonical team name to add
            sport: The sport category
            force: Whether to add even if a similar team exists
            
        Returns:
            True if team was added, False if it already exists (and force=False)
        """
        if not team_name or not team_name.strip():
            logger.error("Team name cannot be empty")
            return False
        
        team_name = team_name.strip()
        sport = sport.lower()
        
        # Check if team already exists (exact match)
        if sport in self._sport_teams_cache:
            for existing_name in self._sport_teams_cache[sport]:
                if existing_name.lower() == team_name.lower():
                    if not force:
                        logger.warning(f"Team '{team_name}' already exists in {sport}")
                        return False
                    else:
                        logger.info(f"Force adding duplicate team '{team_name}' in {sport}")
        
        # Check for similar teams if not forcing
        if not force and sport in self._sport_teams_cache:
            candidates = self._sport_teams_cache[sport]
            match_result = self.matcher.find_best_match(team_name, candidates)
            if match_result:
                similar_name, score = match_result
                logger.warning(f"Similar team exists: '{similar_name}' (similarity: {score:.3f})")
                logger.warning(f"Use force=True to add anyway")
                return False
        
        # Add the team
        new_team = {
            "sport": sport,
            "canonical_team_name": team_name
        }
        self.teams_map.append(new_team)
        self._new_teams_added.append(new_team)
        
        # Update cache
        if sport not in self._sport_teams_cache:
            self._sport_teams_cache[sport] = []
        self._sport_teams_cache[sport].append(team_name)
        
        logger.info(f"Manually added team: {new_team}")
        return True
    
    def standardize_team_name(self, team_name: str, sport: str, auto_add: bool = True, 
                            return_details: bool = False) -> str:
        """
        Standardize a team name to its canonical form
        
        Args:
            team_name: The team name to standardize
            sport: The sport category
            auto_add: Whether to automatically add new teams
            return_details: Whether to return matching details
            
        Returns:
            Canonical team name or tuple (name, details) if return_details=True
        """
        if not team_name or not team_name.strip():
            return "" if not return_details else ("", {"status": "empty"})
        
        team_name = team_name.strip()
        sport = sport.lower()
        
        # Check for exact match first (case insensitive)
        if sport in self._sport_teams_cache:
            for canonical_name in self._sport_teams_cache[sport]:
                if canonical_name.lower() == team_name.lower():
                    details = {"status": "exact_match", "score": 1.0}
                    return canonical_name if not return_details else (canonical_name, details)
        
        # Try fuzzy matching
        if sport in self._sport_teams_cache:
            candidates = self._sport_teams_cache[sport]
            match_result = self.matcher.find_best_match(team_name, candidates)
            
            if match_result:
                matched_name, score = match_result
                logger.info(f"Fuzzy matched '{team_name}' -> '{matched_name}' (score: {score:.3f})")
                details = {"status": "fuzzy_match", "score": score, "matched_name": matched_name}
                return matched_name if not return_details else (matched_name, details)
        
        # No good match found - check if we should auto-add
        best_score = 0.0
        best_candidate = None
        
        if sport in self._sport_teams_cache:
            for candidate in self._sport_teams_cache[sport]:
                score = self.matcher.calculate_similarity(team_name, candidate)
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
        
        # Decide whether to auto-add based on threshold
        should_add = auto_add and best_score < self.auto_add_threshold
        
        if should_add:
            # Add new team
            new_team = {
                "sport": sport,
                "canonical_team_name": team_name
            }
            self.teams_map.append(new_team)
            self._new_teams_added.append(new_team)
            
            # Update cache
            if sport not in self._sport_teams_cache:
                self._sport_teams_cache[sport] = []
            self._sport_teams_cache[sport].append(team_name)
            
            logger.info(f"Auto-added new team: {new_team} (best existing similarity: {best_score:.3f})")
            details = {
                "status": "auto_added", 
                "best_existing_score": best_score,
                "best_existing_team": best_candidate
            }
            return team_name if not return_details else (team_name, details)
        else:
            # Return original name but don't add
            logger.info(f"No auto-add for '{team_name}' (best similarity: {best_score:.3f} >= threshold: {self.auto_add_threshold})")
            details = {
                "status": "no_match_no_add", 
                "best_existing_score": best_score,
                "best_existing_team": best_candidate,
                "auto_add_threshold": self.auto_add_threshold
            }
            return team_name if not return_details else (team_name, details)
    
    def clean_empty_teams(self) -> int:
        """Remove teams with empty canonical names"""
        original_count = len(self.teams_map)
        self.teams_map = [team for team in self.teams_map 
                         if team.get('canonical_team_name', '').strip()]
        self._build_cache()
        
        removed_count = original_count - len(self.teams_map)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} teams with empty names")
        
        return removed_count
    
    def get_newly_added_teams(self) -> List[Dict]:
        """Get list of teams added in this session"""
        return self._new_teams_added.copy()
    
    def reset_new_teams_tracker(self):
        """Reset the tracker for newly added teams"""
        self._new_teams_added = []
    
    def process_api_response(self, api_response: Dict, auto_save: bool = False, 
                           sport_override: str = None) -> Dict:
        """
        Process an API response and standardize team names
        
        Args:
            api_response: The API response containing team names
            auto_save: Whether to save the updated teams map
            sport_override: Override sport detection with this value
            
        Returns:
            Processed API response with standardized team names
        """
        # Deep copy the response
        processed_response = json.loads(json.dumps(api_response))
        changes_made = False
        teams_processed = 0
        
        def process_recursive(obj, path=""):
            nonlocal changes_made, teams_processed
            
            if isinstance(obj, dict):
                # Look for team name fields
                team_fields = ['home_team', 'away_team', 'team_name', 'team', 'participant']
                sport_field = sport_override or obj.get('sport', obj.get('sport_key', obj.get('category', 'unknown')))
                
                for field in team_fields:
                    if field in obj and obj[field]:
                        original_name = obj[field]
                        standardized_name, details = self.standardize_team_name(
                            original_name, sport_field, return_details=True
                        )
                        
                        teams_processed += 1
                        
                        if standardized_name != original_name:
                            obj[field] = standardized_name
                            changes_made = True
                            logger.info(f"Standardized: '{original_name}' -> '{standardized_name}' ({details['status']})")
                        
                        # Add metadata about the standardization
                        obj[f"{field}_standardization"] = {
                            "original": original_name,
                            "standardized": standardized_name,
                            "details": details
                        }
                
                # Process nested objects
                for key, value in obj.items():
                    process_recursive(value, f"{path}.{key}" if path else key)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    process_recursive(item, f"{path}[{i}]" if path else f"[{i}]")
        
        process_recursive(processed_response)
        
        # Save if requested and changes were made
        if auto_save and (changes_made or self._new_teams_added):
            self.save_teams_to_file()
        
        # Add processing summary
        processed_response["_processing_summary"] = {
            "teams_processed": teams_processed,
            "changes_made": changes_made,
            "new_teams_added": len(self._new_teams_added),
            "auto_save_performed": auto_save and (changes_made or self._new_teams_added)
        }
        
        return processed_response
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about the teams database"""
        stats = {
            'total_teams': len(self.teams_map),
            'sports': {},
            'empty_names': 0,
            'newly_added_this_session': len(self._new_teams_added),
            'configuration': {
                'matching_threshold': self.threshold,
                'auto_add_threshold': self.auto_add_threshold,
                'cloud_storage_bucket': self.cloud_storage_bucket
            }
        }
        
        for team in self.teams_map:
            sport = team.get('sport', 'unknown').lower()
            canonical_name = team.get('canonical_team_name', '')
            
            if not canonical_name.strip():
                stats['empty_names'] += 1
            else:
                stats['sports'][sport] = stats['sports'].get(sport, 0) + 1
        
        return stats

# Cloud Function entry point (enhanced with auto-add)
def standardize_team_names_pure_python(request):
    """
    Enhanced Pure Python Cloud Function for team name standardization
    Features automatic team addition and cloud persistence
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json:
            return {'error': 'No JSON payload provided'}, 400
        
        # Configuration from environment or request
        matching_threshold = float(os.environ.get('MATCHING_THRESHOLD', '0.75'))
        auto_add_threshold = float(os.environ.get('AUTO_ADD_THRESHOLD', '0.70'))
        cloud_bucket = os.environ.get('CLOUD_STORAGE_BUCKET')
        teams_file = os.environ.get('TEAMS_FILE', 'teams.json')
        
        # Initialize standardizer
        standardizer = PurePythonTeamStandardizer(
            threshold=matching_threshold,
            auto_add_threshold=auto_add_threshold,
            cloud_storage_bucket=cloud_bucket
        )
        
        # Load existing teams data
        if cloud_bucket:
            standardizer.load_teams_from_cloud_storage(teams_file)
        else:
            standardizer.load_teams_from_file(teams_file)
        
        # Process the API response
        sport_override = request_json.get('sport')  # Allow sport override
        auto_save = request_json.get('auto_save', True)
        
        processed_response = standardizer.process_api_response(
            request_json, 
            auto_save=auto_save,
            sport_override=sport_override
        )
        
        # Prepare response
        response_data = {
            'status': 'success',
            'data': processed_response,
            'message': 'Team names standardized successfully (Pure Python with Auto-Add)',
            'stats': standardizer.get_statistics(),
            'newly_added_teams': standardizer.get_newly_added_teams()
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {'error': str(e)}, 500

# Example usage and testing
def main():
    """Test the enhanced pure Python solution with auto-add functionality"""
    print("Enhanced Pure Python Team Name Standardizer - Auto-Add Testing")
    print("=" * 70)
    
    # Load real teams data
    try:
        with open("teams.json", 'r') as f:
            teams_data = json.load(f)
        print(f"Loaded {len(teams_data)} teams from teams.json")
    except:
        print("Could not load teams.json, using minimal test data")
        teams_data = [
            {"sport": "basketball", "canonical_team_name": "Kauno Zalgiris"},
            {"sport": "basketball", "canonical_team_name": "Real Madrid"},
            {"sport": "soccer", "canonical_team_name": "Barcelona"},
            {"sport": "soccer", "canonical_team_name": "Manchester City"},
        ]
    
    # Initialize standardizer with different thresholds
    standardizer = PurePythonTeamStandardizer(
        teams_data, 
        threshold=0.75,           # Minimum for fuzzy matching
        auto_add_threshold=0.65   # Below this = auto-add new team
    )
    
    # Test cases including completely new teams
    test_cases = [
        ("Kaunas Zalgiris", "basketball"),          # Should match existing
        ("BC Zalgiris Kaunas", "basketball"),       # Should match existing  
        ("Real Madrid Basketball", "basketball"),    # Should match existing
        ("Barcelona FC", "soccer"),                 # Should match existing
        ("New Hampshire Patriots", "basketball"),    # Should be auto-added (new team)
        ("Vilnius Lietkabelis", "basketball"),      # Should be auto-added (new team)
        ("Chelsea Football Club", "soccer"),        # May or may not exist
        ("Tottenham Hotspur", "soccer"),           # May or may not exist
        ("Unknown Basketball Team XYZ", "basketball"), # Should be auto-added
    ]
    
    print(f"Configuration:")
    print(f"- Matching threshold: {standardizer.threshold}")
    print(f"- Auto-add threshold: {standardizer.auto_add_threshold}")
    print(f"- Teams below auto-add threshold will be added as new teams")
    print()
    
    # Process each test case
    for team_name, sport in test_cases:
        print(f"Input: '{team_name}' ({sport})")
        
        result, details = standardizer.standardize_team_name(
            team_name, sport, auto_add=True, return_details=True
        )
        
        status_msg = {
            "exact_match": "✓ EXACT MATCH",
            "fuzzy_match": f"≈ FUZZY MATCH (score: {details.get('score', 0):.3f})",
            "auto_added": f"+ AUTO-ADDED (best existing: {details.get('best_existing_score', 0):.3f})",
            "no_match_no_add": f"? NO MATCH (best: {details.get('best_existing_score', 0):.3f}, threshold: {details.get('auto_add_threshold', 0):.3f})"
        }.get(details['status'], details['status'])
        
        print(f"Output: '{result}'")
        print(f"Status: {status_msg}")
        print("-" * 50)
    
    # Show newly added teams
    new_teams = standardizer.get_newly_added_teams()
    if new_teams:
        print(f"\n🆕 New teams added in this session ({len(new_teams)}):")
        for team in new_teams:
            print(f"  - {team['sport']}: {team['canonical_team_name']}")
    
    # Show final statistics
    stats = standardizer.get_statistics()
    print(f"\n📊 Final Statistics:")
    print(f"Total teams: {stats['total_teams']}")
    print(f"New teams this session: {stats['newly_added_this_session']}")
    print(f"Sports breakdown:")
    for sport, count in stats['sports'].items():
        print(f"  - {sport}: {count} teams")
    
    # Test manual team addition
    print(f"\n🔧 Testing manual team addition:")
    manual_success = standardizer.add_team_manually("Test Team Manual", "soccer")
    print(f"Manual add result: {manual_success}")
    
    # Save the updated teams (optional)
    print(f"\n💾 Saving updated teams...")
    save_success = standardizer.save_teams_to_file("teams_updated.json")
    print(f"Save result: {save_success}")
    
    # Test API response processing
    print(f"\n🌐 Testing API response processing:")
    sample_api_response = {
        "sport": "basketball",
        "matches": [
            {
                "home_team": "Zalgiris Kaunas",
                "away_team": "Some New Team Name",
                "odds": {"home": 1.5, "away": 2.5}
            }
        ]
    }
    
    processed = standardizer.process_api_response(sample_api_response)
    print(f"Processed API response:")
    print(json.dumps(processed, indent=2))

if __name__ == "__main__":
    main() 