# Team Name Standardizer

A Python-based solution for standardizing team names across different sports betting APIs, featuring fuzzy matching and automatic team addition.

## Features

- **Pure Python Implementation**: No external dependencies needed for the core functionality
- **Smart Fuzzy Matching**: Uses multiple algorithms to find the best matches for team names
- **Auto-add Capability**: Automatically adds new teams when no good match is found
- **Configurable Thresholds**: Adjustable similarity thresholds for matching and auto-adding
- **Interactive Test Interface**: Web-based tool for testing and visualizing the standardization process
- **Cloud Storage Integration**: Compatible with Google Cloud Storage for persistence

## How It Works

The standardizer uses a multi-algorithm fuzzy matching approach to find the best canonical name for each team:

1. **Text Normalization**: Handles abbreviations, removes special characters, and normalizes whitespace
2. **City Abbreviation Expansion**: Recognizes common abbreviations like "LA" → "Los Angeles"
3. **Multiple Fuzzy Matching Algorithms**:
   - Levenshtein distance ratio
   - Jaro similarity
   - N-gram Jaccard similarity
   - Token sort ratio
   - Token set ratio
   - Sequence matching

Team names are matched against a database of canonical names. If no good match is found (below the auto-add threshold), the system can automatically add the new team to the database.

## Getting Started

### Installation

```bash
git clone https://github.com/yourusername/team-name-standardizer.git
cd team-name-standardizer
pip install -r requirements.txt
```

### Running the Test Interface

```bash
python test_interface.py
```

Then open your browser to http://localhost:5000

## Usage

### Basic Usage

```python
from pure_python_solution import PurePythonTeamStandardizer

# Initialize the standardizer
standardizer = PurePythonTeamStandardizer(
    threshold=0.75,            # 75% similarity for matching
    auto_add_threshold=0.60    # Below 60% similarity = add new team
)

# Load existing teams data
standardizer.load_teams_from_file("teams.json")

# Standardize a team name
result = standardizer.standardize_team_name(
    team_name="LA Lakers",
    sport="basketball",
    auto_add=True,
    return_details=True
)

print(f"Standardized name: {result[0]}")
print(f"Match details: {result[1]}")
```

### Processing API Responses

```python
# Process an entire API response
processed_data = standardizer.process_api_response(
    api_response=response_json,
    auto_save=True   # Save any new teams
)
```

## Configuration

You can adjust the following parameters:

- `threshold`: Minimum similarity score for fuzzy matching (default: 0.75)
- `auto_add_threshold`: Similarity score below which to auto-add teams (default: 0.60)
- `cloud_storage_bucket`: Optional Google Cloud Storage bucket for persistence

## Testing

The project includes several test files:

- `test_solutions.py`: Unit tests for the core functionality
- `test_auto_add.py`: Tests for the auto-add feature
- `simple_auto_add_test.py`: Simple demonstration of auto-add functionality
- `test_real_data.py`: Tests with real-world data

## Files

- `pure_python_solution.py`: Main implementation with no external dependencies
- `team_name_standardizer.py`: Original implementation
- `tfidf_solution.py`: TF-IDF based implementation (requires scikit-learn)
- `ngram_solution.py`: N-gram based implementation
- `test_interface.py`: Web-based test interface using Flask

## License

This project is licensed under the MIT License - see the LICENSE file for details. 