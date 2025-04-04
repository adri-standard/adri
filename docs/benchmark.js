document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    function activateTab(tabId) {
        // Deactivate all tabs
        tabButtons.forEach(button => button.classList.remove('active'));
        tabPanes.forEach(pane => pane.classList.remove('active'));
        
        // Activate the requested tab
        const activeButton = document.querySelector(`.tab-button[data-tab="${tabId}"]`);
        const activePane = document.getElementById(tabId + '-tab');
        
        if (activeButton && activePane) {
            activeButton.classList.add('active');
            activePane.classList.add('active');
        }
    }
    
    // Add click handlers to all tab buttons
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            activateTab(this.getAttribute('data-tab'));
        });
    });
    
    // Make the activateTab function available globally for anchor links
    window.activateTab = activateTab;
    
    // Simulator functionality (placeholder)
    const toggleSwitch = document.getElementById('quality-signals-toggle');
    if (toggleSwitch) {
        toggleSwitch.addEventListener('change', function() {
            // Update simulator visualization based on toggle state
            const simulatorContainer = document.querySelector('.simulator-container');
            if (simulatorContainer) {
                if (this.checked) {
                    simulatorContainer.classList.add('quality-enabled');
                    simulatorContainer.classList.remove('quality-disabled');
                } else {
                    simulatorContainer.classList.add('quality-disabled');
                    simulatorContainer.classList.remove('quality-enabled');
                }
            }
        });
    }
    
    // Scenario selection (placeholder)
    const scenarioSelect = document.getElementById('scenario-select');
    if (scenarioSelect) {
        scenarioSelect.addEventListener('change', function() {
            // Update simulator based on selected scenario
            const scenario = this.value;
            console.log('Selected scenario:', scenario);
            // Would implement actual scenario switching logic here
        });
    }
    
    // Dataset sorting (placeholder)
    const tableHeaders = document.querySelectorAll('th[data-sort]');
    tableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortBy = this.getAttribute('data-sort');
            console.log('Sort by:', sortBy);
            // Would implement actual sorting logic here
        });
    });
    
    // Populate the dataset table (placeholder)
    const sampleDatasets = [
        {
            name: 'NYC Taxi Trip Data',
            industry: 'Transportation',
            score: 31,
            critical: 'Freshness',
            consequences: 'Agent makes recommendations using outdated fare data',
            action: 'View Details'
        },
        {
            name: 'COVID-19 Dataset',
            industry: 'Public Health',
            score: 42,
            critical: 'Completeness',
            consequences: 'Agent cannot distinguish missing values from zero values',
            action: 'View Details'
        },
        {
            name: 'Financial Market Data',
            industry: 'Finance',
            score: 18,
            critical: 'Freshness',
            consequences: 'Agent makes trading decisions on stale market information',
            action: 'View Details'
        },
        {
            name: 'E-commerce Transactions',
            industry: 'Retail',
            score: 28,
            critical: 'Validity',
            consequences: 'Agent applies incorrect tax rates due to invalid region codes',
            action: 'View Details'
        }
    ];
    
    const datasetTableBody = document.getElementById('dataset-table-body');
    if (datasetTableBody) {
        sampleDatasets.forEach(dataset => {
            const row = document.createElement('tr');
            
            // Determine score class for coloring
            let scoreClass = 'score-low';
            if (dataset.score >= 70) {
                scoreClass = 'score-high';
            } else if (dataset.score >= 40) {
                scoreClass = 'score-medium';
            }
            
            row.innerHTML = `
                <td>${dataset.name}</td>
                <td><span class="badge badge-${dataset.industry.toLowerCase().replace(' ', '-')}">${dataset.industry}</span></td>
                <td class="${scoreClass}">${dataset.score}/100</td>
                <td>${dataset.critical}</td>
                <td>${dataset.consequences}</td>
                <td><button class="btn btn-sm btn-outline dataset-detail-btn" data-dataset="${dataset.name}">View Details</button></td>
            `;
            
            datasetTableBody.appendChild(row);
        });
    }
    
    // Set up dataset detail modal functionality
    const datasetButtons = document.querySelectorAll('.dataset-detail-btn');
    const modalOverlay = document.getElementById('dataset-modal');
    const modalClose = document.getElementById('modal-close');
    
    if (datasetButtons.length > 0 && modalOverlay && modalClose) {
        // Open modal when detail button is clicked
        datasetButtons.forEach(button => {
            button.addEventListener('click', function() {
                const datasetName = this.getAttribute('data-dataset');
                
                // In a real implementation, you would fetch the dataset details here
                // and populate the modal with that data
                
                // For now, just set the dataset name
                document.getElementById('modal-dataset-name').textContent = datasetName;
                
                // Show the modal
                modalOverlay.classList.add('active');
            });
        });
        
        // Close modal when close button is clicked
        modalClose.addEventListener('click', function() {
            modalOverlay.classList.remove('active');
        });
        
        // Close modal when clicking outside of content
        modalOverlay.addEventListener('click', function(event) {
            if (event.target === modalOverlay) {
                modalOverlay.classList.remove('active');
            }
        });
    }
});
