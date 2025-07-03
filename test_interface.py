#!/usr/bin/env python3
"""
Simple Web Interface for Team Name Standardization Testing
- Shows current teams in database
- Allows testing JSON payloads
- Real-time logging of matches vs auto-adds
- Visual feedback of canonicalization process
- Adjustable thresholds for matching and auto-add
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import logging
from datetime import datetime
from pure_python_solution import PurePythonTeamStandardizer
import os

# Configure logging to capture our standardizer logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global standardizer instance
standardizer = None
processing_logs = []

def init_standardizer(match_threshold=0.75, auto_add_threshold=0.60):
    """Initialize the standardizer with current teams data"""
    global standardizer
    try:
        with open('teams.json', 'r', encoding='utf-8') as f:
            teams_data = json.load(f)
        
        standardizer = PurePythonTeamStandardizer(
            teams_data,
            threshold=match_threshold,           # Default: 75% similarity for fuzzy matching
            auto_add_threshold=auto_add_threshold   # Default: Below 60% = auto-add new team
        )
        
        logger.info(f"Loaded {len(teams_data)} teams")
        logger.info(f"Configured with match threshold: {match_threshold:.2f}, auto-add threshold: {auto_add_threshold:.2f}")
        return True
    except Exception as e:
        logger.error(f"Error loading teams: {e}")
        return False

def add_log(message, log_type="info"):
    """Add a message to the processing logs"""
    global processing_logs
    processing_logs.append({
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'message': message,
        'type': log_type
    })
    # Keep only last 50 logs
    processing_logs = processing_logs[-50:]

@app.route('/')
def index():
    """Main interface page"""
    if not standardizer:
        if not init_standardizer():
            return "Error: Could not load teams.json", 500
    
    return render_template('index.html')

@app.route('/api/teams')
def get_teams():
    """Get current teams data for display"""
    if not standardizer:
        return jsonify({'error': 'Standardizer not initialized'}), 500
    
    stats = standardizer.get_statistics()
    
    # Get teams by sport for organized display
    teams_by_sport = {}
    for team in standardizer.teams_map:
        sport = team.get('sport', 'unknown')
        canonical_name = team.get('canonical_team_name', '')
        
        if canonical_name.strip():  # Only include non-empty names
            if sport not in teams_by_sport:
                teams_by_sport[sport] = []
            teams_by_sport[sport].append(canonical_name)
    
    # Sort teams within each sport
    for sport in teams_by_sport:
        teams_by_sport[sport].sort()
    
    return jsonify({
        'teams_by_sport': teams_by_sport,
        'stats': stats,
        'configuration': {
            'matching_threshold': standardizer.threshold,
            'auto_add_threshold': standardizer.auto_add_threshold
        }
    })

@app.route('/api/process', methods=['POST'])
def process_payload():
    """Process JSON payload and return standardized version"""
    global processing_logs
    
    if not standardizer:
        return jsonify({'error': 'Standardizer not initialized'}), 500
    
    try:
        # Clear previous logs
        processing_logs = []
        
        # Get the payload
        payload = request.get_json()
        if not payload:
            return jsonify({'error': 'No JSON payload provided'}), 400
        
        add_log("🚀 Starting team name standardization process", "info")
        add_log(f"📥 Input payload: {len(json.dumps(payload))} characters", "info")
        
        # Reset new teams tracker for this session
        standardizer.reset_new_teams_tracker()
        
        # Process the payload
        processed_payload = standardizer.process_api_response(
            payload, 
            auto_save=False  # Don't auto-save during testing
        )
        
        # Get processing summary
        summary = processed_payload.get("_processing_summary", {})
        new_teams = standardizer.get_newly_added_teams()
        
        # Add summary logs
        add_log(f"🔍 Teams processed: {summary.get('teams_processed', 0)}", "info")
        add_log(f"🔄 Changes made: {summary.get('changes_made', False)}", "success" if summary.get('changes_made') else "info")
        add_log(f"🆕 New teams added: {len(new_teams)}", "success" if new_teams else "info")
        
        # Log each new team
        for team in new_teams:
            add_log(f"  + Added: {team['canonical_team_name']} ({team['sport']})", "success")
        
        add_log("✅ Processing completed successfully", "success")
        
        return jsonify({
            'status': 'success',
            'original_payload': payload,
            'processed_payload': processed_payload,
            'summary': summary,
            'new_teams': new_teams,
            'logs': processing_logs,
            'stats': standardizer.get_statistics()
        })
        
    except Exception as e:
        add_log(f"❌ Error: {str(e)}", "error")
        logger.error(f"Processing error: {e}")
        return jsonify({'error': str(e), 'logs': processing_logs}), 500

@app.route('/api/save')
def save_teams():
    """Save current teams to file"""
    if not standardizer:
        return jsonify({'error': 'Standardizer not initialized'}), 500
    
    try:
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"teams_backup_{timestamp}.json"
        
        # Save with backup
        success = standardizer.save_teams_to_file("teams.json", backup=True)
        
        if success:
            add_log(f"💾 Teams saved successfully to teams.json", "success")
            add_log(f"📋 Backup created", "info")
            return jsonify({'status': 'success', 'message': 'Teams saved successfully'})
        else:
            add_log(f"❌ Failed to save teams", "error")
            return jsonify({'error': 'Failed to save teams'}), 500
            
    except Exception as e:
        add_log(f"❌ Save error: {str(e)}", "error")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """Get current processing logs"""
    return jsonify({'logs': processing_logs})

@app.route('/api/reset')
def reset_standardizer():
    """Reset and reload the standardizer"""
    global standardizer, processing_logs
    processing_logs = []
    
    # Get threshold parameters if provided
    match_threshold = float(request.args.get('match_threshold', 0.75))
    auto_add_threshold = float(request.args.get('auto_add_threshold', 0.60))
    
    if init_standardizer(match_threshold, auto_add_threshold):
        add_log(f"🔄 Standardizer reset with match threshold: {match_threshold:.2f}, auto-add threshold: {auto_add_threshold:.2f}", "info")
        return jsonify({'status': 'success'})
    else:
        add_log("❌ Failed to reset standardizer", "error")
        return jsonify({'error': 'Failed to reset'}), 500

@app.route('/api/update_thresholds', methods=['POST'])
def update_thresholds():
    """Update the standardizer thresholds"""
    if not standardizer:
        return jsonify({'error': 'Standardizer not initialized'}), 500
    
    try:
        data = request.get_json()
        match_threshold = float(data.get('match_threshold', standardizer.threshold))
        auto_add_threshold = float(data.get('auto_add_threshold', standardizer.auto_add_threshold))
        
        # Validate thresholds
        if not 0 <= match_threshold <= 1:
            return jsonify({'error': 'Match threshold must be between 0 and 1'}), 400
        if not 0 <= auto_add_threshold <= 1:
            return jsonify({'error': 'Auto-add threshold must be between 0 and 1'}), 400
            
        # Update standardizer thresholds
        standardizer.threshold = match_threshold
        standardizer.auto_add_threshold = auto_add_threshold
        standardizer.matcher.threshold = match_threshold  # Also update the matcher threshold
        
        add_log(f"⚙️ Updated thresholds - Match: {match_threshold:.2f}, Auto-add: {auto_add_threshold:.2f}", "success")
        
        return jsonify({
            'status': 'success',
            'message': 'Thresholds updated successfully',
            'configuration': {
                'matching_threshold': match_threshold,
                'auto_add_threshold': auto_add_threshold
            }
        })
        
    except Exception as e:
        add_log(f"❌ Error updating thresholds: {str(e)}", "error")
        return jsonify({'error': str(e)}), 500

# Create the HTML template
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team Name Standardizer - Test Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .panel {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .full-width {
            grid-column: 1 / -1;
        }
        h1, h2 {
            margin-top: 0;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #2c5282;
            grid-column: 1 / -1;
        }
        textarea {
            width: 100%;
            height: 200px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            resize: vertical;
        }
        button {
            background: #2c5282;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
            margin-top: 10px;
        }
        button:hover {
            background: #2a4a7c;
        }
        button.secondary {
            background: #718096;
        }
        button.danger {
            background: #e53e3e;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        .stat-item {
            background: #f7fafc;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
            border-left: 4px solid #2c5282;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #2c5282;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        .teams-list {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 10px;
        }
        .sport-section {
            margin-bottom: 20px;
        }
        .sport-title {
            font-weight: bold;
            color: #2c5282;
            margin-bottom: 5px;
            padding: 5px;
            background: #f7fafc;
            border-radius: 4px;
        }
        .team-item {
            padding: 2px 5px;
            font-size: 14px;
            color: #4a5568;
        }
        .logs {
            max-height: 300px;
            overflow-y: auto;
            background: #1a202c;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }
        .log-info { color: #63b3ed; }
        .log-success { color: #68d391; }
        .log-error { color: #fc8181; }
        .log-warning { color: #fbb86c; }
        .timestamp {
            color: #a0aec0;
            margin-right: 10px;
        }
        .json-display {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }
        .config-info {
            background: #edf2f7;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 14px;
        }
        .threshold-sliders {
            margin-top: 15px;
            margin-bottom: 15px;
        }
        .slider-row {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .slider-row label {
            min-width: 150px;
            color: #4a5568;
        }
        .slider-row input[type="range"] {
            flex-grow: 1;
            margin: 0 10px;
        }
        .slider-row .value {
            min-width: 60px;
            text-align: right;
            color: #2c5282;
            font-weight: bold;
        }
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
        .tooltip {
            position: relative;
            display: inline-block;
            margin-left: 5px;
            cursor: help;
        }
        .tooltip .tooltip-icon {
            display: inline-block;
            width: 16px;
            height: 16px;
            background: #4a5568;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 16px;
            font-size: 12px;
            font-weight: bold;
        }
        .tooltip .tooltip-text {
            visibility: hidden;
            width: 250px;
            background-color: #4a5568;
            color: white;
            text-align: left;
            border-radius: 6px;
            padding: 8px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
            font-weight: normal;
            font-size: 12px;
        }
        .tooltip:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="full-width">🔧 Team Name Standardizer - Test Interface</h1>
        
        <!-- Current Teams Panel -->
        <div class="panel">
            <h2>📋 Current Teams Database</h2>
            <div id="stats" class="stats">
                <div class="stat-item">
                    <div class="stat-number" id="total-teams">-</div>
                    <div class="stat-label">Total Teams</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="total-sports">-</div>
                    <div class="stat-label">Sports</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="new-teams">-</div>
                    <div class="stat-label">New This Session</div>
                </div>
            </div>
            
            <div class="config-info">
                <strong>Thresholds Configuration:</strong>
                <div class="tooltip">
                    <span class="tooltip-icon">?</span>
                    <span class="tooltip-text">
                        - Match threshold: The minimum similarity score needed to consider a team name as a match to an existing team.<br>
                        - Auto-add threshold: Below this similarity score, the system will add a new team instead of trying to match it.
                    </span>
                </div>
                <div class="threshold-sliders">
                    <div class="slider-row">
                        <label for="match-threshold-slider">Match Threshold:</label>
                        <input type="range" id="match-threshold-slider" min="0" max="100" value="75" step="1">
                        <span class="value" id="match-threshold-value">75%</span>
                    </div>
                    <div class="slider-row">
                        <label for="auto-add-threshold-slider">Auto-Add Threshold:</label>
                        <input type="range" id="auto-add-threshold-slider" min="0" max="100" value="60" step="1">
                        <span class="value" id="auto-add-threshold-value">60%</span>
                    </div>
                </div>
                <button id="apply-thresholds-btn" onclick="updateThresholds()">Apply Thresholds</button>
            </div>
            
            <div id="teams-container" class="teams-list">
                Loading teams...
            </div>
            
            <button onclick="loadTeams()" class="secondary">🔄 Refresh Teams</button>
            <button onclick="saveTeams()">💾 Save Teams</button>
            <button onclick="resetStandardizer()" class="danger">🔄 Reset</button>
        </div>
        
        <!-- Testing Panel -->
        <div class="panel">
            <h2>🧪 Test JSON Payload</h2>
            <label for="json-input"><strong>Enter JSON payload with team names:</strong></label>
            <textarea id="json-input" placeholder='Example:
{
  "sport": "basketball",
  "matches": [
    {
      "home_team": "Zalgiris Kaunas",
      "away_team": "Some New Team",
      "odds": {"home": 1.5, "away": 2.5}
    }
  ]
}'></textarea>
            
            <button onclick="processPayload()">🚀 Process Payload</button>
            <button onclick="loadSampleData()" class="secondary">📝 Load Sample</button>
            <button onclick="clearInput()" class="secondary">🗑️ Clear</button>
        </div>
        
        <!-- Results Panel -->
        <div class="panel full-width">
            <h2>📤 Processing Results</h2>
            <div id="results-container">
                <p style="color: #666;">Enter a JSON payload above and click "Process Payload" to see results.</p>
            </div>
        </div>
        
        <!-- Logs Panel -->
        <div class="panel full-width">
            <h2>📋 Processing Logs</h2>
            <div id="logs" class="logs">
                <div class="log-entry log-info">
                    <span class="timestamp">00:00:00</span>
                    🎯 Ready to process team names! Enter a JSON payload above.
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentTeams = {};
        
        // Load teams data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadTeams();
            
            // Initialize slider values from UI
            document.getElementById('match-threshold-slider').addEventListener('input', function() {
                document.getElementById('match-threshold-value').textContent = this.value + '%';
            });
            
            document.getElementById('auto-add-threshold-slider').addEventListener('input', function() {
                document.getElementById('auto-add-threshold-value').textContent = this.value + '%';
            });
        });
        
        async function loadTeams() {
            try {
                const response = await fetch('/api/teams');
                const data = await response.json();
                
                currentTeams = data.teams_by_sport;
                
                // Update stats
                document.getElementById('total-teams').textContent = data.stats.total_teams;
                document.getElementById('total-sports').textContent = Object.keys(data.teams_by_sport).length;
                document.getElementById('new-teams').textContent = data.stats.newly_added_this_session;
                
                // Update configuration sliders
                document.getElementById('match-threshold-slider').value = Math.round(data.configuration.matching_threshold * 100);
                document.getElementById('match-threshold-value').textContent = Math.round(data.configuration.matching_threshold * 100) + '%';
                
                document.getElementById('auto-add-threshold-slider').value = Math.round(data.configuration.auto_add_threshold * 100);
                document.getElementById('auto-add-threshold-value').textContent = Math.round(data.configuration.auto_add_threshold * 100) + '%';
                
                // Display teams by sport
                displayTeams(data.teams_by_sport);
                
            } catch (error) {
                console.error('Error loading teams:', error);
                addLogEntry('❌ Error loading teams: ' + error.message, 'error');
            }
        }
        
        function displayTeams(teamsBySport) {
            const container = document.getElementById('teams-container');
            container.innerHTML = '';
            
            for (const [sport, teams] of Object.entries(teamsBySport)) {
                const sportSection = document.createElement('div');
                sportSection.className = 'sport-section';
                
                const sportTitle = document.createElement('div');
                sportTitle.className = 'sport-title';
                sportTitle.textContent = `${sport.toUpperCase()} (${teams.length} teams)`;
                sportSection.appendChild(sportTitle);
                
                teams.forEach(team => {
                    const teamItem = document.createElement('div');
                    teamItem.className = 'team-item';
                    teamItem.textContent = team;
                    sportSection.appendChild(teamItem);
                });
                
                container.appendChild(sportSection);
            }
        }
        
        async function updateThresholds() {
            const matchThreshold = parseInt(document.getElementById('match-threshold-slider').value) / 100;
            const autoAddThreshold = parseInt(document.getElementById('auto-add-threshold-slider').value) / 100;
            
            try {
                document.getElementById('apply-thresholds-btn').textContent = 'Updating...';
                
                const response = await fetch('/api/update_thresholds', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        match_threshold: matchThreshold,
                        auto_add_threshold: autoAddThreshold
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLogEntry(`⚙️ Updated thresholds - Match: ${matchThreshold.toFixed(2)}, Auto-add: ${autoAddThreshold.toFixed(2)}`, 'success');
                } else {
                    addLogEntry('❌ Failed to update thresholds: ' + result.error, 'error');
                }
            } catch (error) {
                addLogEntry('❌ Error updating thresholds: ' + error.message, 'error');
            } finally {
                document.getElementById('apply-thresholds-btn').textContent = 'Apply Thresholds';
            }
        }
        
        async function processPayload() {
            const input = document.getElementById('json-input').value.trim();
            
            if (!input) {
                addLogEntry('⚠️ Please enter a JSON payload', 'warning');
                return;
            }
            
            try {
                // Validate JSON
                const payload = JSON.parse(input);
                
                // Show loading state
                document.body.classList.add('loading');
                addLogEntry('🚀 Processing payload...', 'info');
                
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    displayResults(result);
                    displayLogs(result.logs);
                    
                    // Refresh teams if new ones were added
                    if (result.new_teams.length > 0) {
                        await loadTeams();
                    }
                } else {
                    addLogEntry('❌ Processing failed: ' + result.error, 'error');
                }
                
            } catch (error) {
                addLogEntry('❌ Error: ' + error.message, 'error');
            } finally {
                document.body.classList.remove('loading');
            }
        }
        
        function displayResults(result) {
            const container = document.getElementById('results-container');
            
            let html = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h3>📥 Original Payload</h3>
                        <div class="json-display">${JSON.stringify(result.original_payload, null, 2)}</div>
                    </div>
                    <div>
                        <h3>📤 Processed Payload</h3>
                        <div class="json-display">${JSON.stringify(result.processed_payload, null, 2)}</div>
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <h3>📊 Processing Summary</h3>
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">${result.summary.teams_processed}</div>
                            <div class="stat-label">Teams Processed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">${result.summary.changes_made ? 'Yes' : 'No'}</div>
                            <div class="stat-label">Changes Made</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">${result.new_teams.length}</div>
                            <div class="stat-label">New Teams Added</div>
                        </div>
                    </div>
                </div>
            `;
            
            if (result.new_teams.length > 0) {
                html += `
                    <div style="margin-top: 20px;">
                        <h3>🆕 New Teams Added</h3>
                        <div class="json-display">${JSON.stringify(result.new_teams, null, 2)}</div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        function displayLogs(logs) {
            const logsContainer = document.getElementById('logs');
            logsContainer.innerHTML = '';
            
            logs.forEach(log => {
                addLogEntry(log.message, log.type, log.timestamp);
            });
        }
        
        function addLogEntry(message, type = 'info', timestamp = null) {
            const logsContainer = document.getElementById('logs');
            const entry = document.createElement('div');
            entry.className = `log-entry log-${type}`;
            
            const time = timestamp || new Date().toLocaleTimeString('en-US', { hour12: false });
            entry.innerHTML = `<span class="timestamp">${time}</span>${message}`;
            
            logsContainer.appendChild(entry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
        
        async function saveTeams() {
            try {
                const response = await fetch('/api/save');
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLogEntry('💾 Teams saved successfully!', 'success');
                } else {
                    addLogEntry('❌ Failed to save teams: ' + result.error, 'error');
                }
            } catch (error) {
                addLogEntry('❌ Save error: ' + error.message, 'error');
            }
        }
        
        async function resetStandardizer() {
            if (!confirm('Are you sure you want to reset the standardizer? This will reload teams from the file.')) {
                return;
            }
            
            try {
                // Get current threshold values for reset
                const matchThreshold = parseInt(document.getElementById('match-threshold-slider').value) / 100;
                const autoAddThreshold = parseInt(document.getElementById('auto-add-threshold-slider').value) / 100;
                
                const response = await fetch(`/api/reset?match_threshold=${matchThreshold}&auto_add_threshold=${autoAddThreshold}`);
                const result = await response.json();
                
                if (result.status === 'success') {
                    addLogEntry('🔄 Standardizer reset successfully!', 'success');
                    await loadTeams();
                    document.getElementById('results-container').innerHTML = '<p style="color: #666;">Enter a JSON payload above and click "Process Payload" to see results.</p>';
                } else {
                    addLogEntry('❌ Failed to reset: ' + result.error, 'error');
                }
            } catch (error) {
                addLogEntry('❌ Reset error: ' + error.message, 'error');
            }
        }
        
        function loadSampleData() {
            const sample = {
                "sport": "basketball",
                "league": "Lithuanian Basketball League",
                "matches": [
                    {
                        "match_id": "12345",
                        "home_team": "Zalgiris Kaunas",
                        "away_team": "Some Completely New Team",
                        "odds": {"home": 1.25, "away": 3.80}
                    },
                    {
                        "match_id": "12346",
                        "home_team": "Real Madrid Basketball",
                        "away_team": "Another Unknown Team XYZ",
                        "odds": {"home": 2.10, "away": 1.75}
                    }
                ]
            };
            
            document.getElementById('json-input').value = JSON.stringify(sample, null, 2);
            addLogEntry('📝 Sample data loaded', 'info');
        }
        
        function clearInput() {
            document.getElementById('json-input').value = '';
            addLogEntry('🗑️ Input cleared', 'info');
        }
    </script>
</body>
</html>
'''

# Create templates directory and save the HTML
if not os.path.exists('templates'):
    os.makedirs('templates')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

if __name__ == '__main__':
    print("🚀 Starting Team Name Standardizer Test Interface")
    print("=" * 60)
    print("Features:")
    print("✅ View current teams database")
    print("✅ Test JSON payloads with team names")
    print("✅ Real-time logging of matches vs auto-adds")
    print("✅ Visual feedback of canonicalization process")
    print("✅ Save new teams back to database")
    print("✅ Adjustable thresholds for matching and auto-adding")
    print("=" * 60)
    print("🌐 Open your browser to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 