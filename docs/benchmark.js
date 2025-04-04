/**
 * Agent Data Readiness Benchmark JavaScript
 * Handles data loading, table interactions, modals, and the agent blindness simulator
 */

// Global variables
let benchmarkData = null;
let radarChart = null;

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Load benchmark data
    fetchBenchmarkData();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize the simulator
    initializeSimulator();
    
    // Update pioneers count
    document.getElementById('pioneers-count').textContent = '237';
});

/**
 * Fetch benchmark data from JSON file
 */
async function fetchBenchmarkData() {
    try {
        const response = await fetch('data/benchmark.json');
        benchmarkData = await response.json();
        
        // Update the UI with the data
        updateMetricsSection();
        populateDatasetTable();
        
        console.log('Benchmark data loaded successfully', benchmarkData);
    } catch (error) {
        console.error('Error loading benchmark data:', error);
    }
}

/**
 * Set up event listeners for interactive elements
 */
function setupEventListeners() {
    // Table sorting
    document.querySelectorAll('th[data-sort]').forEach(header => {
        header.addEventListener('click', function() {
            sortTable(this.dataset.sort);
        });
    });
    
    // Modal close button
    const modalClose = document.getElementById('modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }
    
    // Close modal when clicking outside
    const modalOverlay = document.getElementById('dataset-modal');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(event) {
            if (event.target === this) {
                closeModal();
            }
        });
    }
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeModal();
        }
    });
}

/**
 * Update the metrics section with actual data
 */
function updateMetricsSection() {
    if (!benchmarkData) return;
    
    const avgScoreElement = document.getElementById('avg-score');
    if (avgScoreElement) {
        avgScoreElement.textContent = `${benchmarkData.overall_average}/100`;
        
        // Set color class based on score
        avgScoreElement.className = 'metric-value';
        if (benchmarkData.overall_average >= 70) {
            avgScoreElement.classList.add('score-high');
        } else if (benchmarkData.overall_average >= 50) {
            avgScoreElement.classList.add('score-medium');
        } else {
            avgScoreElement.classList.add('score-low');
        }
    }
}

/**
 * Populate the dataset table with data
 */
function populateDatasetTable() {
    if (!benchmarkData || !benchmarkData.datasets) return;
    
    const tableBody = document.getElementById('dataset-table-body');
    if (!tableBody) return;
    
    // Clear existing content
    tableBody.innerHTML = '';
    
    // Add a row for each dataset
    benchmarkData.datasets.forEach(dataset => {
        const row = document.createElement('tr');
        row.dataset.id = dataset.id;
        
        // Determine the readiness level and critical issue
        const readinessLevel = getReadinessLevel(dataset.assessment.overall_score);
        const criticalIssue = getCriticalIssue(dataset.assessment.dimension_scores);
        
        // Create impact message based on dataset type
        let impactMessage = '';
        switch(dataset.id) {
            case 'financial-market-data':
                impactMessage = 'Your agents are making trading decisions on data that could be 15 minutes stale during high volatility';
                break;
            case 'ecommerce-transactions':
                impactMessage = 'Your agents are recommending products at incorrect prices, eroding customer trust';
                break;
            case 'covid19-data':
                impactMessage = 'Your agents are missing critical trend changes in public health data';
                break;
            case 'nyc-taxi':
                impactMessage = 'Your fare predictions are off by up to 85% during major events';
                break;
            default:
                impactMessage = 'Your agents are making decisions on potentially stale or invalid data';
        }
        
        // Add dataset info to row
        row.innerHTML = `
            <td data-name="${dataset.name}">${dataset.name}</td>
            <td data-industry="${dataset.industry}">
                <span class="badge badge-${dataset.industry.toLowerCase().replace(/\s+/g, '-')}">${dataset.industry}</span>
            </td>
            <td data-score="${dataset.assessment.overall_score}" class="${getScoreClass(dataset.assessment.overall_score)}">
                ${dataset.assessment.overall_score}/10
            </td>
            <td data-critical="${criticalIssue}">${criticalIssue}</td>
            <td>${impactMessage}</td>
            <td>
                <button class="btn btn-sm btn-primary view-details" data-id="${dataset.id}">View Details</button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners to the detail buttons
    document.querySelectorAll('.view-details').forEach(button => {
        button.addEventListener('click', function() {
            const datasetId = this.dataset.id;
            openDatasetModal(datasetId);
        });
    });
}

/**
 * Sort the dataset table by the specified column
 */
function sortTable(column) {
    const table = document.getElementById('dataset-table');
    if (!table) return;
    
    const header = table.querySelector(`th[data-sort="${column}"]`);
    if (!header) return;
    
    // Get current sort direction
    const currentDirection = header.classList.contains('sort-asc') ? 'asc' : 
                              header.classList.contains('sort-desc') ? 'desc' : '';
    
    // Determine new sort direction
    const direction = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Update header classes
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    header.classList.add(`sort-${direction}`);
    
    // Get all rows and convert to array for sorting
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    
    // Sort the rows
    rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-${column}]`).dataset[column];
        const bValue = b.querySelector(`td[data-${column}]`).dataset[column];
        
        // Handle numeric values
        if (column === 'score') {
            return direction === 'asc' ? 
                parseFloat(aValue) - parseFloat(bValue) : 
                parseFloat(bValue) - parseFloat(aValue);
        }
        
        // String comparison
        return direction === 'asc' ? 
            aValue.localeCompare(bValue) : 
            bValue.localeCompare(aValue);
    });
    
    // Re-append rows in the new order
    const tbody = table.querySelector('tbody');
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Open the dataset detail modal for the specified dataset
 */
function openDatasetModal(datasetId) {
    if (!benchmarkData || !benchmarkData.datasets) return;
    
    // Find the dataset
    const dataset = benchmarkData.datasets.find(d => d.id === datasetId);
    if (!dataset) return;
    
    // Update modal content
    document.getElementById('modal-dataset-name').textContent = dataset.name;
    
    const modalIndustry = document.getElementById('modal-industry');
    modalIndustry.textContent = dataset.industry;
    modalIndustry.className = `badge badge-${dataset.industry.toLowerCase().replace(/\s+/g, '-')}`;
    
    const modalFormat = document.getElementById('modal-format');
    modalFormat.textContent = dataset.format;
    modalFormat.className = `badge badge-${dataset.format.toLowerCase()}`;
    
    const modalScore = document.getElementById('modal-score');
    modalScore.textContent = `${dataset.assessment.overall_score}/10`;
    modalScore.className = getScoreClass(dataset.assessment.overall_score);
    
    // Set dimension scores
    const dimensions = ['validity', 'completeness', 'freshness', 'consistency', 'plausibility'];
    dimensions.forEach(dim => {
        const score = dataset.assessment.dimension_scores[dim];
        const element = document.getElementById(`modal-${dim}`);
        if (element) {
            element.textContent = `${score}/20`;
            element.className = getScoreClass(score / 2); // Scale to match overall score
        }
    });
    
    // Set report link
    document.getElementById('modal-report-link').href = `../benchmark_results/${dataset.id}_report.html`;
    
    // Update impact text based on the dataset's critical issues
    updateImpactText(dataset);
    
    // Create or update radar chart
    createRadarChart('radar-chart', dataset.assessment.dimension_scores);
    
    // Show the modal
    document.getElementById('dataset-modal').classList.add('active');
}

/**
 * Close the dataset detail modal
 */
function closeModal() {
    document.getElementById('dataset-modal').classList.remove('active');
}

/**
 * Create or update the radar chart
 */
function createRadarChart(canvasId, dimensionScores) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // If chart already exists, destroy it
    if (radarChart) {
        radarChart.destroy();
    }
    
    // Create new chart
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Validity', 'Completeness', 'Freshness', 'Consistency', 'Plausibility'],
            datasets: [{
                label: 'Dimension Scores',
                data: [
                    dimensionScores.validity,
                    dimensionScores.completeness,
                    dimensionScores.freshness,
                    dimensionScores.consistency,
                    dimensionScores.plausibility
                ],
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                borderColor: 'rgb(52, 152, 219)',
                pointBackgroundColor: 'rgb(52, 152, 219)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(52, 152, 219)'
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { display: true },
                    suggestedMin: 0,
                    suggestedMax: 20
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

/**
 * Update the impact text and failure scenarios based on the dataset
 */
function updateImpactText(dataset) {
    // Find the lowest scoring dimension
    const dimensions = Object.entries(dataset.assessment.dimension_scores);
    dimensions.sort((a, b) => a[1] - b[1]);
    const lowestDimension = dimensions[0][0];
    
    let impactText = '';
    let failureScenarios = [];
    
    // Customize text based on the lowest dimension
    switch (lowestDimension) {
        case 'validity':
            impactText = `AI agents working with this ${dataset.format} cannot reliably determine if the data meets basic quality standards. Without clear validation rules and standards, agents may use data that doesn't conform to expected formats or ranges.`;
            failureScenarios = [
                'Agent processes malformed data leading to incorrect calculations',
                'Invalid values are treated as legitimate data points',
                'Agent cannot distinguish between valid and invalid formats'
            ];
            break;
        case 'completeness':
            impactText = `AI agents using this ${dataset.format} lack clear signals about missing data. Without completeness metadata, agents cannot distinguish between "data doesn't exist" and "data wasn't collected."`;
            failureScenarios = [
                'Agent treats missing values as zero or negative indicators',
                'Patterns in missing data are not detected or communicated',
                'Agent makes decisions with incomplete information without knowing'
            ];
            break;
        case 'freshness':
            impactText = `AI agents accessing this ${dataset.format} cannot determine how recent or stale the information is. Without freshness signals, agents may use outdated information for time-sensitive decisions.`;
            failureScenarios = [
                'Agent uses outdated pricing information to make purchasing decisions',
                'Time-sensitive recommendations are made with stale data',
                'Agent cannot prioritize more recent information over older data'
            ];
            break;
        case 'consistency':
            impactText = `AI agents working with this ${dataset.format} lack signals about the internal consistency of the data. Without consistency checks, agents cannot detect contradictory information or logical inconsistencies.`;
            failureScenarios = [
                'Agent fails to identify contradictory data points',
                'Inconsistent data across related fields leads to conflicting recommendations',
                'Agent cannot reconcile information from different parts of the dataset'
            ];
            break;
        case 'plausibility':
            impactText = `AI agents using this ${dataset.format} cannot distinguish between plausible and implausible values. Without plausibility signals, agents may treat extreme outliers or unlikely scenarios as normal data.`;
            failureScenarios = [
                'Agent treats statistical outliers as valid data points',
                'Implausible combinations of values affect decision-making',
                'Agent cannot identify scenarios that are technically valid but practically impossible'
            ];
            break;
    }
    
    // Update the modal with customized text
    document.getElementById('modal-impact-text').textContent = impactText;
    
    // Update failure scenarios
    const scenariosList = document.getElementById('modal-failure-scenarios');
    scenariosList.innerHTML = '';
    failureScenarios.forEach(scenario => {
        const li = document.createElement('li');
        li.textContent = scenario;
        scenariosList.appendChild(li);
    });
    
    // Update recommendations
    const recommendationsList = document.getElementById('modal-recommendations');
    recommendationsList.innerHTML = '';
    
    const recommendations = getRecommendations(dataset, lowestDimension);
    recommendations.forEach(recommendation => {
        const li = document.createElement('li');
        li.textContent = recommendation;
        recommendationsList.appendChild(li);
    });
}

/**
 * Get appropriate recommendations based on the dataset and dimension
 */
function getRecommendations(dataset, lowestDimension) {
    switch (lowestDimension) {
        case 'validity':
            return [
                'Implement explicit data type and format definitions',
                'Add validation rules that can be queried by agents',
                'Include valid range information for numeric fields',
                'Communicate validation results in machine-readable format'
            ];
        case 'completeness':
            return [
                'Add explicit completeness metadata for each field',
                'Distinguish between "not collected" and "not applicable"',
                'Provide completeness scores at dataset and field levels',
                'Include expected value counts for collection periods'
            ];
        case 'freshness':
            return [
                'Add explicit timestamps for data collection and update',
                'Include freshness SLAs that agents can query',
                'Provide time-to-live metadata for time-sensitive fields',
                'Implement version control with update history'
            ];
        case 'consistency':
            return [
                'Implement cross-field consistency rules',
                'Provide consistency check results in agent-accessible format',
                'Define and enforce referential integrity constraints',
                'Include logical validation between related datasets'
            ];
        case 'plausibility':
            return [
                'Add statistical distribution metadata for numeric fields',
                'Implement outlier detection with clear flagging',
                'Provide confidence scores for unusual data points',
                'Include domain-specific plausibility rules'
            ];
        default:
            return [
                'Implement comprehensive data quality metadata',
                'Add agent-accessible quality scores',
                'Provide explicit context about data collection and processing',
                'Include quality monitoring history'
            ];
    }
}

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

/**
 * Helper function to get readiness level based on score
 */
function getReadinessLevel(score) {
    if (score >= 8.0) return 'Advanced';
    if (score >= 6.5) return 'Proficient';
    if (score >= 5.0) return 'Basic';
    if (score >= 3.5) return 'Limited';
    return 'Inadequate';
}

/**
 * Helper function to determine the critical issue based on dimension scores
 */
function getCriticalIssue(dimensionScores) {
    // Find the lowest scoring dimension
    let lowestScore = Infinity;
    let lowestDimension = '';
    
    Object.entries(dimensionScores).forEach(([dimension, score]) => {
        if (score < lowestScore) {
            lowestScore = score;
            lowestDimension = dimension;
        }
    });
    
    // Map dimension to issue description
    switch (lowestDimension) {
        case 'validity':
            return 'Validity Blindness';
        case 'completeness':
            return 'Completeness Blindness';
        case 'freshness':
            return 'Freshness Blindness';
        case 'consistency':
            return 'Consistency Blindness';
        case 'plausibility':
            return 'Plausibility Blindness';
        default:
            return 'Multiple Blindness Issues';
    }
}

/**
 * Helper function to format a date string
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

/**
 * Helper function to get CSS class based on score
 */
function getScoreClass(score) {
    if (score >= 7.0) return 'score-high';
    if (score >= 5.0) return 'score-medium';
    return 'score-low';
}
