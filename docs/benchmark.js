document.addEventListener('DOMContentLoaded', function() {
  // Load benchmark data from the JSON file
  async function loadBenchmarkData() {
    try {
      const response = await fetch('data/benchmark.json');
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error loading benchmark data:', error);
      return null;
    }
  }
  
  // Initialize charts when data is loaded
  loadBenchmarkData().then(data => {
    if (!data) return;
    
    // Update text elements
    document.getElementById('last-updated').textContent = data.updated;
    document.getElementById('overall-score').textContent = data.overall_average;
    document.getElementById('submissions-count').textContent = data.submissions;
    
    // Create industry comparison chart
    const industryCtx = document.getElementById('industryChart').getContext('2d');
    new Chart(industryCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(data.industries),
        datasets: [{
          label: 'Overall ADRI Score',
          data: Object.values(data.industries),
          backgroundColor: 'rgba(52, 152, 219, 0.7)',
          borderColor: 'rgb(52, 152, 219)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'ADRI Score (0-100)'
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'ADRI Scores by Industry'
          }
        }
      }
    });
    
    // Create dimension comparison chart
    const dimensionCtx = document.getElementById('dimensionChart').getContext('2d');
    new Chart(dimensionCtx, {
      type: 'radar',
      data: {
        labels: Object.keys(data.dimensions).map(d => d.charAt(0).toUpperCase() + d.slice(1)),
        datasets: [{
          label: 'Average Dimension Scores',
          data: Object.values(data.dimensions),
          backgroundColor: 'rgba(46, 204, 113, 0.2)',
          borderColor: 'rgb(46, 204, 113)',
          borderWidth: 2,
          pointBackgroundColor: 'rgb(46, 204, 113)'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            angleLines: {
              display: true
            },
            suggestedMin: 0,
            suggestedMax: 20
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'Average Scores by Dimension'
          }
        }
      }
    });
  });
});
