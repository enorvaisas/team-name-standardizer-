import json
import logging
from typing import Dict, List, Tuple, Optional
from rapidfuzz import fuzz, process
import functions_framework
from google.cloud import storage
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamNameStandardizer:
    def __init__(self, bucket_name: str, teams_file: str = "teams.json"):
        self.bucket_name = bucket_name
        self.teams_file = teams_file
        self.storage_client = storage.Client()
        self.teams_map = self._load_teams_map()
        
    def _load_teams_map(self) -> List[Dict]:
        """Load the teams mapping from Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(self.teams_file)
            
            if blob.exists():
                content = blob.download_as_text()
                return json.loads(content)
            else:
                logger.info("Teams file doesn't exist, starting with empty map")
                return []
        except Exception as e:
            logger.error(f"Error loading teams map: {e}")
            return []
    
    def _save_teams_map(self) -> None:
        """Save the teams mapping to Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(self.teams_file)
            blob.upload_from_string(
                json.dumps(self.teams_map, indent=2),
                content_type='application/json'
            )
            logger.info("Teams map saved successfully")
        except Exception as e:
            logger.error(f"Error saving teams map: {e}")
    
    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name for better matching"""
        if not name:
            return ""
        
        # Remove common prefixes/suffixes and normalize
        name = re.sub(r'\b(FC|CF|SC|AC|BC|FK|KK|Club|Team|Basketball|Football)\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(de|del|la|le|the|of)\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[^\w\s]', ' ', name)  # Remove special characters
        name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
        return name.lower()
    
    def _get_teams_by_sport(self, sport: str) -> List[Dict]:
        """Get all teams for a specific sport"""
        return [team for team in self.teams_map if team.get('sport', '').lower() == sport.lower()]
    
    def _find_best_match(self, team_name: str, sport: str, threshold: int = 75) -> Optional[Dict]:
        """Find the best matching canonical team name"""
        if not team_name.strip():
            return None
            
        sport_teams = self._get_teams_by_sport(sport)
        if not sport_teams:
            return None
        
        # Normalize the input team name
        normalized_input = self._normalize_team_name(team_name)
        
        # Create a list of canonical names for matching
        canonical_names = [team['canonical_team_name'] for team in sport_teams]
        normalized_canonical = [self._normalize_team_name(name) for name in canonical_names]
        
        # Try different matching strategies
        strategies = [
            ('token_sort_ratio', fuzz.token_sort_ratio),
            ('token_set_ratio', fuzz.token_set_ratio),
            ('partial_ratio', fuzz.partial_ratio),
            ('ratio', fuzz.ratio)
        ]
        
        best_match = None
        best_score = 0
        best_strategy = None
        
        for strategy_name, strategy_func in strategies:
            # Match against normalized names
            match = process.extractOne(
                normalized_input, 
                normalized_canonical, 
                scorer=strategy_func,
                score_cutoff=threshold
            )
            
            if match and match[1] > best_score:
                best_score = match[1]
                matched_index = normalized_canonical.index(match[0])
                best_match = sport_teams[matched_index]
                best_strategy = strategy_name
        
        if best_match:
            logger.info(f"Found match for '{team_name}' -> '{best_match['canonical_team_name']}' "
                       f"(score: {best_score}, strategy: {best_strategy})")
        
        return best_match
    
    def _add_new_team(self, team_name: str, sport: str) -> Dict:
        """Add a new team to the canonical map"""
        new_team = {
            "sport": sport.lower(),
            "canonical_team_name": team_name.strip()
        }
        self.teams_map.append(new_team)
        logger.info(f"Added new team: {new_team}")
        return new_team
    
    def standardize_team_name(self, team_name: str, sport: str, auto_add: bool = True) -> str:
        """
        Standardize a team name to its canonical form
        
        Args:
            team_name: The team name to standardize
            sport: The sport category
            auto_add: Whether to automatically add new teams to the map
            
        Returns:
            Canonical team name
        """
        if not team_name or not team_name.strip():
            return ""
        
        # First, try to find an exact match (case insensitive)
        sport_teams = self._get_teams_by_sport(sport)
        for team in sport_teams:
            if team['canonical_team_name'].lower() == team_name.lower():
                return team['canonical_team_name']
        
        # Try fuzzy matching
        best_match = self._find_best_match(team_name, sport)
        
        if best_match:
            return best_match['canonical_team_name']
        
        # No match found - add as new team if auto_add is enabled
        if auto_add:
            new_team = self._add_new_team(team_name, sport)
            return new_team['canonical_team_name']
        
        # Return original name if not auto-adding
        return team_name
    
    def process_api_response(self, api_response: Dict, auto_save: bool = True) -> Dict:
        """
        Process an entire API response and standardize team names
        
        Args:
            api_response: The API response containing team names
            auto_save: Whether to automatically save the updated map
            
        Returns:
            Processed API response with standardized team names
        """
        processed_response = json.loads(json.dumps(api_response))  # Deep copy
        changes_made = False
        
        # This function needs to be customized based on your API response structure
        # Example implementation for a common sports betting API structure:
        
        def process_recursive(obj, path=""):
            nonlocal changes_made
            
            if isinstance(obj, dict):
                # Look for team name fields - adjust these based on your API structure
                team_fields = ['home_team', 'away_team', 'team_name', 'team', 'participant']
                sport_field = obj.get('sport', obj.get('sport_key', obj.get('category', 'unknown')))
                
                for field in team_fields:
                    if field in obj and obj[field]:
                        original_name = obj[field]
                        standardized_name = self.standardize_team_name(original_name, sport_field)
                        if standardized_name != original_name:
                            obj[field] = standardized_name
                            changes_made = True
                            logger.info(f"Standardized: '{original_name}' -> '{standardized_name}' in {path}.{field}")
                
                # Process nested objects
                for key, value in obj.items():
                    process_recursive(value, f"{path}.{key}" if path else key)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    process_recursive(item, f"{path}[{i}]" if path else f"[{i}]")
        
        process_recursive(processed_response)
        
        # Save the updated teams map if changes were made
        if changes_made and auto_save:
            self._save_teams_map()
        
        return processed_response

# Cloud Function entry point
@functions_framework.http
def standardize_team_names(request):
    """HTTP Cloud Function to standardize team names in API responses"""
    
    # Configuration - set these as environment variables
    BUCKET_NAME = "your-bucket-name"  # Replace with your bucket
    
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json:
            return {'error': 'No JSON payload provided'}, 400
        
        # Initialize standardizer
        standardizer = TeamNameStandardizer(BUCKET_NAME)
        
        # Process the API response
        processed_response = standardizer.process_api_response(request_json)
        
        return {
            'status': 'success',
            'data': processed_response,
            'message': 'Team names standardized successfully'
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {'error': str(e)}, 500

# Example usage for testing
if __name__ == "__main__":
    # Test the standardizer locally
    standardizer = TeamNameStandardizer("test-bucket")
    
    # Test cases
    test_cases = [
        ("Kaunas Zalgiris", "basketball"),
        ("BC Zalgiris Kaunas", "basketball"),
        ("Real Madrid CF", "soccer"),
        ("FC Barcelona", "soccer"),
        ("Man City", "soccer"),
    ]
    
    for team_name, sport in test_cases:
        result = standardizer.standardize_team_name(team_name, sport)
        print(f"{team_name} ({sport}) -> {result}") 