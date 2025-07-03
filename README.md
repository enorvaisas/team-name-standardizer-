# Team Name Standardizer

A comprehensive solution for standardizing sports team names from different API providers using various similarity matching algorithms.

## Problem Statement

Different sports betting API providers use different team names for the same teams (e.g., "BC Kaunas Zalgiris", "Kaunas Zalgiris", "Zalgiris Kaunas"). This creates inconsistency in data processing. This solution provides automatic team name standardization with multiple approaches.

## Solutions Provided

### 1. **RapidFuzz Solution (Recommended)** 📁 `team_name_standardizer.py`

**Best for: General use, production environments**

- Uses the `rapidfuzz` library for fuzzy string matching
- Multiple matching strategies (token_sort_ratio, token_set_ratio, partial_ratio)
- Cloud Function ready with Google Cloud Storage integration
- Automatic team addition and map persistence

**Advantages:**
- ✅ Fast and reliable
- ✅ Handles various team name formats well
- ✅ Production-ready with error handling
- ✅ Configurable similarity thresholds

### 2. **N-gram Solution** 📁 `ngram_solution.py`

**Best for: Custom similarity requirements, research**

- Character-level n-gram analysis
- Jaccard similarity, cosine similarity, sequence matching
- Word-level similarity analysis
- Weighted scoring system

**Advantages:**
- ✅ No external dependencies (uses built-in libraries)
- ✅ Highly customizable scoring
- ✅ Good for short team names
- ✅ Multiple similarity measures combined

### 3. **TF-IDF Solution** 📁 `tfidf_solution.py`

**Best for: Large datasets, advanced text analysis**

- TF-IDF vectorization with scikit-learn
- Character n-gram analysis within word boundaries
- Cosine similarity matching
- Separate models per sport category

**Advantages:**
- ✅ Excellent for large datasets
- ✅ Learns importance of different text features
- ✅ Scales well with many teams
- ✅ Advanced text preprocessing

## Quick Start

### 1. Setup Dependencies

```bash
pip install -r requirements.txt
```

### 2. Basic Usage (RapidFuzz Solution)

```python
from team_name_standardizer import TeamNameStandardizer

# Initialize with your Cloud Storage bucket
standardizer = TeamNameStandardizer("your-bucket-name")

# Standardize a team name
result = standardizer.standardize_team_name("Kaunas Zalgiris", "basketball")
print(result)  # Output: "BC Kaunas Zalgiris" (if exists in map)
```

### 3. Process API Response

```python
# Example API response
api_response = {
    "sport": "basketball",
    "matches": [
        {"home_team": "Zalgiris Kaunas", "away_team": "Real Madrid"},
        {"home_team": "Barcelona", "away_team": "Man City"}
    ]
}

# Process and standardize
processed = standardizer.process_api_response(api_response)
```

## Cloud Function Deployment

### Using Google Cloud Functions

1. **Set up Google Cloud Storage bucket:**
```bash
gsutil mb gs://your-team-data-bucket
gsutil cp teams.json gs://your-team-data-bucket/
```

2. **Deploy the function:**
```bash
gcloud functions deploy standardize-team-names \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --source . \
  --entry-point standardize_team_names \
  --memory 512MB \
  --timeout 60s \
  --set-env-vars BUCKET_NAME=your-team-data-bucket
```

3. **Test the function:**
```bash
curl -X POST "https://REGION-PROJECT.cloudfunctions.net/standardize-team-names" \
  -H "Content-Type: application/json" \
  -d '{
    "sport": "basketball",
    "matches": [
      {"home_team": "Zalgiris Kaunas", "away_team": "Real Madrid"}
    ]
  }'
```

## Data Structure

### Input Format (teams.json)
```json
[
  {"sport": "soccer", "canonical_team_name": "Celtic"},
  {"sport": "basketball", "canonical_team_name": "BC Kaunas Zalgiris"},
  {"sport": "tennis", "canonical_team_name": "Radulov, Iliyan"}
]
```

### API Request Format
```json
{
  "sport": "basketball",
  "matches": [
    {
      "home_team": "Kaunas Zalgiris",
      "away_team": "Real Madrid Basketball"
    }
  ]
}
```

### API Response Format
```json
{
  "status": "success",
  "data": {
    "sport": "basketball",
    "matches": [
      {
        "home_team": "BC Kaunas Zalgiris",
        "away_team": "Real Madrid"
      }
    ]
  },
  "message": "Team names standardized successfully"
}
```

## Configuration Options

### Similarity Thresholds

**RapidFuzz Solution:**
```python
# Adjust threshold (0-100)
standardizer._find_best_match(team_name, sport, threshold=75)
```

**N-gram Solution:**
```python
# Adjust threshold (0.0-1.0)
matcher = NGramTeamMatcher(n=3, threshold=0.6)
```

**TF-IDF Solution:**
```python
# Adjust threshold and n-gram range
matcher = TFIDFTeamMatcher(threshold=0.6, ngram_range=(1, 3))
```

### Normalization Rules

All solutions include customizable text normalization:
- Remove common prefixes (FC, BC, Club, etc.)
- Remove special characters
- Handle common words (Real, de, la, etc.)
- Case normalization

## Performance Comparison

| Solution | Speed | Accuracy | Memory | Dependencies |
|----------|-------|----------|---------|--------------|
| RapidFuzz | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | rapidfuzz |
| N-gram | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Built-in only |
| TF-IDF | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | scikit-learn |

## Advanced Features

### 1. **Hybrid Approach**
Combine multiple methods for better accuracy:
```python
from tfidf_solution import HybridTeamMatcher

hybrid = HybridTeamMatcher()
score = hybrid.calculate_hybrid_similarity("Team A", "Team B")
```

### 2. **Batch Processing**
Process multiple teams at once:
```python
teams_to_process = [
    ("Kaunas Zalgiris", "basketball"),
    ("Real Madrid", "soccer"),
    ("Barcelona", "soccer")
]

results = []
for team, sport in teams_to_process:
    result = standardizer.standardize_team_name(team, sport)
    results.append(result)
```

### 3. **Custom API Response Processing**
Modify the `process_api_response` function to handle your specific API structure:

```python
def custom_process_response(self, api_response):
    # Your custom logic here
    # Look for team names in your specific JSON structure
    pass
```

## Testing

Run the included test examples:

```bash
# Test RapidFuzz solution
python team_name_standardizer.py

# Test N-gram solution
python ngram_solution.py

# Test TF-IDF solution
python tfidf_solution.py
```

## Best Practices

1. **Start with RapidFuzz solution** - it provides the best balance of accuracy and performance
2. **Set appropriate thresholds** - too low causes false matches, too high misses valid matches
3. **Monitor and adjust** - review matches and adjust normalization rules as needed
4. **Use sport-specific matching** - always include sport category for better accuracy
5. **Backup your teams map** - regularly backup the canonical teams database

## Troubleshooting

### Common Issues

1. **No matches found:**
   - Lower the similarity threshold
   - Check if sport categories match
   - Verify team name normalization

2. **False positive matches:**
   - Increase the similarity threshold
   - Improve normalization rules
   - Add more specific team identifiers

3. **Performance issues:**
   - Use TF-IDF for large datasets
   - Implement caching for frequently accessed teams
   - Consider preprocessing team names

### Logging and Monitoring

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

Monitor standardization results and adjust thresholds based on your specific use case.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - feel free to use and modify as needed.

---

## Contact

For questions or support, please create an issue in the repository. 