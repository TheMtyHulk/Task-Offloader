async function fetchData() {
            try {
                const response = await fetch('/computed_at_count');
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        async function createPieChart() {
            const data = await fetchData();
            const ctx = document.getElementById('myPieChart').getContext('2d');
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Cloud', 'Edge'],
                    datasets: [{
                        data: [data.cloud, data.edge],
                        backgroundColor: ['#36A2EB', '#FF6384'],
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Task Distribution'
                        }
                    }
                }
            });
        }

createPieChart();

async function fetchFileData() {
    try {
        const response = await fetch('/file_sizes_with_time');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching file data:', error);
    }
}

async function createBarChart() {
    const data = await fetchFileData();
    const ctx = document.getElementById('myBarChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(file => file.filename),
            datasets: [{
                label: 'File Size (MB)',
                data: data.map(file => file.sizeInMB),
                backgroundColor: '#36A2EB',
            }, {
                label: 'Time to Complete (seconds)',
                data: data.map(file => parseFloat(file.timeToComplete)),
                backgroundColor: '#FF6384',
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'File Sizes and Time to Complete'
                }
            }
        }
    });
}
createBarChart();
async function fetchLineChartData() {
    try {
        const response = await fetch('/file_sizes_with_time');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching line chart data:', error);
    }
}

async function createLineChart() {
    const data = await fetchLineChartData();
    const ctx = document.getElementById('myLineChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(file => file.sizeInMB),
            datasets: [{
                label: 'Tasks Over Time',
                data: data.map(file => parseFloat(file.timeToComplete)),
                borderColor: '#36A2EB',
                fill: false,
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'File Size (MB)'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Time to Complete (seconds)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Tasks Over Time'
                }
            }
        }
    });
}

createLineChart();



