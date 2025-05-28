/**
 * Agent Data Readiness Index - Simulator JavaScript
 * Handles the Agent Blindness Simulator without external dependencies
 */

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the simulator
    initializeSimulator();
});

/**
 * Initialize the Agent Blindness Simulator
 */
function initializeSimulator() {
    const scenarioSelect = document.getElementById('scenario-select');
    const qualityToggle = document.getElementById('quality-signals-toggle');
    const decisionPath = document.getElementById('decision-path');
    const decisionOutcome = document.getElementById('decision-outcome');
    
    if (!scenarioSelect || !qualityToggle || !decisionPath || !decisionOutcome) {
        return;
    }
    
    // Set up event listeners
    scenarioSelect.addEventListener('change', updateSimulation);
    qualityToggle.addEventListener('change', updateSimulation);
    
    // Initial simulation update
    updateSimulation();
    
    /**
     * Update the simulation based on selected scenario and toggle state
     */
    function updateSimulation() {
        const scenario = scenarioSelect.value;
        const qualitySignalsEnabled = qualityToggle.checked;
        
        // Update decision path visualization
        decisionPath.innerHTML = '';
        decisionPath.className = 'decision-path';
        decisionPath.classList.add(`scenario-${scenario}`);
        
        // Create a simple visualization
        const pathContainer = document.createElement('div');
        pathContainer.className = 'path-container';
        
        // Create different visualizations based on quality signals enabled/disabled
        if (qualitySignalsEnabled) {
            pathContainer.innerHTML = `
                <div class="path-node start">Start</div>
                <div class="path-arrow"></div>
                <div class="path-node check">Check Data Quality</div>
                <div class="path-arrow"></div>
                <div class="path-node">Get Freshness Score</div>
                <div class="path-arrow"></div>
                <div class="path-node decision">Decide: ${getScenarioDecision(scenario, true)}</div>
            `;
            pathContainer.classList.add('quality-enabled');
        } else {
            pathContainer.innerHTML = `
                <div class="path-node start">Start</div>
                <div class="path-arrow"></div>
                <div class="path-node">Use Data As-Is</div>
                <div class="path-arrow"></div>
                <div class="path-node">Make Prediction</div>
                <div class="path-arrow"></div>
                <div class="path-node decision error">Wrong Decision: ${getScenarioDecision(scenario, false)}</div>
            `;
            pathContainer.classList.add('quality-disabled');
        }
        
        decisionPath.appendChild(pathContainer);
        
        // Update outcome description
        updateOutcomeDescription(scenario, qualitySignalsEnabled);
        
        // Update explanation text
        const explanation = document.getElementById('simulator-explanation');
        if (explanation) {
            if (qualitySignalsEnabled) {
                explanation.innerHTML = '<p>With quality signals, the agent can make informed decisions about data reliability.</p>';
            } else {
                explanation.innerHTML = '<p>Without quality signals, the agent cannot determine if data is fresh enough for decision making.</p>';
            }
        }
    }
    
    /**
     * Get scenario-specific decision text
     */
    function getScenarioDecision(scenario, qualityEnabled) {
        if (qualityEnabled) {
            switch (scenario) {
                case 'nyc-taxi':
                    return 'Fetch Fresh Data';
                case 'financial':
                    return 'Request Real-Time Prices';
                case 'covid19':
                    return 'Use Recent Dataset';
                case 'ecommerce':
                    return 'Update Pricing Data';
                default:
                    return 'Get Fresh Data';
            }
        } else {
            switch (scenario) {
                case 'nyc-taxi':
                    return 'Use Stale Trip Data';
                case 'financial':
                    return 'Use Old Market Data';
                case 'covid19':
                    return 'Use Outdated Statistics';
                case 'ecommerce':
                    return 'Apply Wrong Pricing';
                default:
                    return 'Use Stale Data';
            }
        }
    }
    
    /**
     * Update the outcome description based on scenario and quality signals
     */
    function updateOutcomeDescription(scenario, qualityEnabled) {
        let outcome = '';
        
        if (qualityEnabled) {
            switch (scenario) {
                case 'nyc-taxi':
                    outcome = `<div class="alert alert-success">
                        <strong>Correct Decision:</strong> Agent detects that trip data is 48 hours old and requests a fresh dataset before predicting fare amounts, resulting in accurate fare estimates during a major event.
                    </div>`;
                    break;
                case 'financial':
                    outcome = `<div class="alert alert-success">
                        <strong>Correct Decision:</strong> Agent checks market data freshness, finds it's 15 minutes old during high volatility, and requests real-time quotes before making trading recommendations.
                    </div>`;
                    break;
                case 'covid19':
                    outcome = `<div class="alert alert-success">
                        <strong>Correct Decision:</strong> Agent identifies that the COVID-19 dataset is from last week and requests the most recent data before generating trend analysis, capturing a major change in case rates.
                    </div>`;
                    break;
                case 'ecommerce':
                    outcome = `<div class="alert alert-success">
                        <strong>Correct Decision:</strong> Agent detects that product pricing data is outdated (pre-sale) and refreshes the information before making purchase recommendations, saving customers money.
                    </div>`;
                    break;
                default:
                    outcome = `<div class="alert alert-success">
                        <strong>Correct Decision:</strong> Agent detects data quality issues and takes appropriate action to ensure reliable results.
                    </div>`;
            }
        } else {
            switch (scenario) {
                case 'nyc-taxi':
                    outcome = `<div class="alert alert-danger">
                        <strong>Critical Error:</strong> Agent uses 48-hour old trip data during a major event with changed traffic patterns, causing fare predictions to be off by 85% and riders to be charged incorrectly.
                    </div>`;
                    break;
                case 'financial':
                    outcome = `<div class="alert alert-danger">
                        <strong>Critical Error:</strong> Agent uses 15-minute old market prices during high volatility, resulting in trading recommendations based on outdated information and potential financial losses of $127,000+.
                    </div>`;
                    break;
                case 'covid19':
                    outcome = `<div class="alert alert-danger">
                        <strong>Critical Error:</strong> Agent analyzes week-old COVID-19 data without knowing it's outdated, missing a major trend change and providing incorrect public health recommendations.
                    </div>`;
                    break;
                case 'ecommerce':
                    outcome = `<div class="alert alert-danger">
                        <strong>Critical Error:</strong> Agent uses pre-sale pricing data without knowing a site-wide sale has started, recommending products at higher prices than currently available and losing customer trust.
                    </div>`;
                    break;
                default:
                    outcome = `<div class="alert alert-danger">
                        <strong>Critical Error:</strong> Agent uses stale data without awareness, leading to incorrect decisions and poor outcomes.
                    </div>`;
            }
        }
        
        decisionOutcome.innerHTML = outcome;
    }
}

// Smooth scrolling for anchor links
document.addEventListener('click', function(e) {
    // Check if clicked element is an anchor link
    if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#')) {
        e.preventDefault();
        const targetId = e.target.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
});
