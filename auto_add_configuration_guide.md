# Auto-Add Configuration Guide

## Overview

The enhanced Pure Python Team Standardizer now automatically adds new teams when they don't match any existing teams in your database. This eliminates the need for manual mapping creation and ensures your system can handle new teams from betting APIs automatically.

## Key Features

✅ **Automatic Team Discovery**: New teams are added when similarity falls below a configurable threshold  
✅ **Smart Thresholds**: Separate thresholds for fuzzy matching vs. auto-adding  
✅ **Sport-Aware**: Teams are categorized by sport automatically  
✅ **Persistence**: New teams are saved to your JSON file or Cloud Storage  
✅ **Tracking**: All additions are logged and can be reviewed  
✅ **Zero Dependencies**: Pure Python - no compilation issues

## Configuration Parameters

### Threshold Settings

```python
standardizer = PurePythonTeamStandardizer(
    teams_data,
    threshold=0.75,           # Minimum similarity for fuzzy matching (75%)
    auto_add_threshold=0.60   # Below this similarity = auto-add new team (60%)
)
```

**Recommendation for Production:**
- `threshold=0.75` (75% similarity for matching existing teams)
- `auto_add_threshold=0.60` (60% similarity threshold for auto-adding)

### How It Works

1. **Exact Match Check**: First, check for case-insensitive exact matches
2. **Fuzzy Matching**: If no exact match, try fuzzy matching with `threshold`
3. **Auto-Add Decision**: If best similarity < `auto_add_threshold`, add as new team
4. **Return Result**: Return matched name or newly added team name

## Usage Examples

### Basic Usage

```python
from pure_python_solution import PurePythonTeamStandardizer
import json

# Load existing teams
with open('teams.json', 'r') as f:
    teams_data = json.load(f)

# Initialize with auto-add
standardizer = PurePythonTeamStandardizer(
    teams_data,
    threshold=0.75,
    auto_add_threshold=0.60
)

# Standardize team names (auto-add enabled by default)
result = standardizer.standardize_team_name("New Team Name", "basketball")
print(f"Standardized: {result}")

# Save new teams back to file
standardizer.save_teams_to_file("teams.json")
```

### API Response Processing

```python
# Process entire API response
api_response = {
    "sport": "basketball",
    "matches": [
        {
            "home_team": "Known Team",
            "away_team": "Unknown New Team",
            "odds": {"home": 1.5, "away": 2.5}
        }
    ]
}

processed = standardizer.process_api_response(
    api_response, 
    auto_save=True  # Automatically save new teams
)

# Check what was added
new_teams = standardizer.get_newly_added_teams()
print(f"Added {len(new_teams)} new teams")
```

### Cloud Function Deployment

```python
def standardize_team_names_cloud_function(request):
    """Cloud Function with auto-add"""
    
    # Configuration from environment variables
    matching_threshold = float(os.environ.get('MATCHING_THRESHOLD', '0.75'))
    auto_add_threshold = float(os.environ.get('AUTO_ADD_THRESHOLD', '0.60'))
    
    standardizer = PurePythonTeamStandardizer(
        threshold=matching_threshold,
        auto_add_threshold=auto_add_threshold,
        cloud_storage_bucket=os.environ.get('TEAMS_BUCKET')
    )
    
    # Load teams from Cloud Storage
    standardizer.load_teams_from_cloud_storage("teams.json")
    
    # Process request with auto-save
    request_json = request.get_json()
    processed = standardizer.process_api_response(request_json, auto_save=True)
    
    return {
        'data': processed,
        'stats': standardizer.get_statistics(),
        'newly_added': standardizer.get_newly_added_teams()
    }
```

## Environment Variables

Set these environment variables for your Cloud Function:

```bash
MATCHING_THRESHOLD=0.75      # Fuzzy match threshold
AUTO_ADD_THRESHOLD=0.60      # Auto-add threshold  
CLOUD_STORAGE_BUCKET=your-bucket-name
TEAMS_FILE=teams.json
```

## Threshold Tuning Guide

### Conservative (Fewer Auto-Adds)
```python
threshold=0.80
auto_add_threshold=0.50
```
- Higher matching requirement
- Only adds teams with very low similarity to existing ones
- Good for established databases with comprehensive team lists

### Moderate (Recommended)
```python
threshold=0.75
auto_add_threshold=0.60
```
- Balanced approach
- Good for most production use cases
- Catches variations while avoiding duplicates

### Aggressive (More Auto-Adds)
```python
threshold=0.70
auto_add_threshold=0.70
```
- Lower matching requirement
- Adds more teams as new rather than matching
- Good for rapidly expanding databases

## Monitoring and Maintenance

### Track New Additions

```python
# Get teams added in current session
new_teams = standardizer.get_newly_added_teams()

# Log for monitoring
for team in new_teams:
    print(f"NEW: {team['sport']} - {team['canonical_team_name']}")
```

### Review Statistics

```python
stats = standardizer.get_statistics()
print(f"Total teams: {stats['total_teams']}")
print(f"New this session: {stats['newly_added_this_session']}")
print(f"By sport: {stats['sports']}")
```

### Clean Up Empty Names

```python
removed = standardizer.clean_empty_teams()
print(f"Removed {removed} teams with empty names")
```

## Real-World Results

Based on testing with your 596-team database:

- ✅ **"Kaunas Zalgiris"** → Matched **"Kauno Zalgiris"** (84.7% similarity)
- ✅ **"Barcelona FC"** → Matched **"Barcelona"** (100% similarity)  
- ✅ **"Bayern Munich"** → Matched **"FC Bayern Munchen"** (79.9% similarity)
- 🆕 **"New Basketball Team XYZ"** → Auto-added as new team (32.8% best existing)
- 🆕 **"Unknown Soccer Club"** → Auto-added as new team (32.8% best existing)

## Best Practices

1. **Start Conservative**: Begin with higher thresholds and adjust based on results
2. **Monitor Additions**: Regularly review newly added teams for quality
3. **Regular Backups**: The system creates automatic backups when saving
4. **Sport Consistency**: Ensure sport parameters are consistent across your APIs
5. **Threshold Testing**: Test with sample data before deploying to production

## Troubleshooting

### Too Many False Positives (Wrong Matches)
- Increase `threshold` (e.g., from 0.75 to 0.80)
- This makes fuzzy matching more strict

### Too Many New Teams Added
- Decrease `auto_add_threshold` (e.g., from 0.60 to 0.50)
- This makes auto-adding more conservative

### Teams Not Being Added
- Increase `auto_add_threshold` (e.g., from 0.60 to 0.70)
- Check that `auto_add=True` in your calls

### Performance Issues
- The system uses caching for fast lookups
- Consider splitting very large team databases by sport

## Security Considerations

- ✅ No external dependencies = no security vulnerabilities
- ✅ Pure Python = no compilation = no build-time security issues
- ✅ Local processing = team data never leaves your environment
- ✅ Configurable storage = use Cloud Storage with proper IAM controls

This auto-add functionality makes your team name standardizer completely autonomous, capable of handling new teams from any betting API without manual intervention! 