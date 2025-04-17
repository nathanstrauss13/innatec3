// Initialize charts when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Helper function to get sentiment color
    function getSentimentColor(sentiment) {
        if (sentiment < -0.33) return 'rgba(220, 53, 69, 0.7)'; // Negative - red
        if (sentiment < 0.33) return 'rgba(108, 117, 125, 0.7)'; // Neutral - gray
        return 'rgba(40, 167, 69, 0.7)'; // Positive - green
    }

    // Helper function to calculate sentiment by outlet
    function calculateSentimentByOutlet(articles) {
        const outlets = {};
        
        articles.forEach(article => {
            const outlet = article.source.name;
            if (!outlets[outlet]) {
                outlets[outlet] = {
                    count: 0,
                    totalSentiment: 0
                };
            }
            outlets[outlet].count++;
            outlets[outlet].totalSentiment += article.sentiment;
        });
        
        const outletArray = Object.keys(outlets).map(outlet => ({
            outlet: outlet,
            count: outlets[outlet].count,
            avgSentiment: outlets[outlet].totalSentiment / outlets[outlet].count
        }));
        
        return outletArray.sort((a, b) => b.count - a.count);
    }

    // Get data from template
    var articles1 = window.articles1 || [];
    var articles2 = window.articles2 || null;
    var analysis1 = window.analysis1 || {};
    var analysis2 = window.analysis2 || null;
    var query1 = window.query1 || "";
    var query2 = window.query2 || "";
    
    // Create sentiment scatter plot
    if (articles1.length > 0) {
        var trace1 = {
            x: articles1.map(a => a.publishedAt),
            y: articles1.map(a => a.sentiment),
            text: articles1.map(a => `<b>${a.title}</b><br>Source: ${a.source.name}<br><a href="${a.url}" target="_blank" style="color: #005e30;">Read article →</a>`),
            mode: 'markers',
            type: 'scatter',
            name: query1,
            marker: {
                color: articles1.map(a => getSentimentColor(a.sentiment)),
                size: 10
            },
            hoverinfo: 'text'
        };
        
        var traces = [trace1];
        
        if (articles2 && articles2.length > 0) {
            var trace2 = {
                x: articles2.map(a => a.publishedAt),
                y: articles2.map(a => a.sentiment),
                text: articles2.map(a => `<b>${a.title}</b><br>Source: ${a.source.name}<br><a href="${a.url}" target="_blank" style="color: #00a651;">Read article →</a>`),
                mode: 'markers',
                type: 'scatter',
                name: query2,
                marker: {
                    color: articles2.map(a => getSentimentColor(a.sentiment)),
                    size: 10,
                    opacity: 0.7
                },
                hoverinfo: 'text'
            };
            
            traces.push(trace2);
        }
        
        var layout = {
            title: '',
            xaxis: {
                title: 'Publication Date',
                tickformat: '%b %d, %Y'
            },
            yaxis: {
                title: 'Sentiment Score',
                range: [-1, 1]
            },
            hovermode: 'closest',
            showlegend: true,
            legend: {
                x: 0,
                y: 1.1,
                orientation: 'h'
            },
            margin: {
                l: 50,
                r: 20,
                t: 10,
                b: 50
            },
            autosize: true
        };
        
        Plotly.newPlot('sentimentScatter', traces, layout, {responsive: true});
    }
    
    // Create timeline chart
    if (analysis1.timeline && analysis1.timeline.length > 0) {
        var timelineCtx = document.getElementById('timelineChart').getContext('2d');
        
        var datasets = [{
            label: query1,
            data: analysis1.timeline.map(item => ({
                x: item.date,
                y: item.count
            })),
            borderColor: '#005e30',
            backgroundColor: 'rgba(0, 94, 48, 0.1)',
            borderWidth: 2,
            tension: 0.1,
            fill: true
        }];
        
        if (analysis2 && analysis2.timeline && analysis2.timeline.length > 0) {
            datasets.push({
                label: query2,
                data: analysis2.timeline.map(item => ({
                    x: item.date,
                    y: item.count
                })),
                borderColor: '#00a651',
                backgroundColor: 'rgba(0, 166, 81, 0.1)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            });
        }
        
        new Chart(timelineCtx, {
            type: 'line',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MMM d'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Articles'
                        },
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                const date = new Date(context[0].parsed.x);
                                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Create sources chart
    if (analysis1.sources && analysis1.sources.length > 0) {
        var sourcesCtx = document.getElementById('sourcesChart').getContext('2d');
        
        var topSources1 = analysis1.sources.slice(0, 10);
        var datasets = [{
            label: query1,
            data: topSources1.map(s => s.count),
            backgroundColor: 'rgba(0, 94, 48, 0.7)',
            borderColor: 'rgba(0, 94, 48, 1)',
            borderWidth: 1
        }];
        
        var labels = topSources1.map(s => s.name);
        
        if (analysis2 && analysis2.sources && analysis2.sources.length > 0) {
            var topSources2 = analysis2.sources.slice(0, 10);
            
            // Find unique sources across both queries
            var allSources = new Set([...topSources1.map(s => s.name), ...topSources2.map(s => s.name)]);
            labels = Array.from(allSources);
            
            // Create data arrays with 0 for missing sources
            var data1 = labels.map(label => {
                const source = topSources1.find(s => s.name === label);
                return source ? source.count : 0;
            });
            
            var data2 = labels.map(label => {
                const source = topSources2.find(s => s.name === label);
                return source ? source.count : 0;
            });
            
            datasets = [
                {
                    label: query1,
                    data: data1,
                    backgroundColor: 'rgba(0, 94, 48, 0.7)',
                    borderColor: 'rgba(0, 94, 48, 1)',
                    borderWidth: 1
                },
                {
                    label: query2,
                    data: data2,
                    backgroundColor: 'rgba(0, 166, 81, 0.7)',
                    borderColor: 'rgba(0, 166, 81, 1)',
                    borderWidth: 1
                }
            ];
        }
        
        new Chart(sourcesCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Articles'
                        },
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    // Create sentiment distribution pie charts
    if (articles1.length > 0) {
        var sentimentPieCtx1 = document.getElementById('sentimentPieChart1').getContext('2d');
        
        var positive1 = articles1.filter(a => a.sentiment > 0.2).length;
        var neutral1 = articles1.filter(a => a.sentiment >= -0.2 && a.sentiment <= 0.2).length;
        var negative1 = articles1.filter(a => a.sentiment < -0.2).length;
        
        new Chart(sentimentPieCtx1, {
            type: 'pie',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: [positive1, neutral1, negative1],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.7)',
                        'rgba(108, 117, 125, 0.7)',
                        'rgba(220, 53, 69, 0.7)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(108, 117, 125, 1)',
                        'rgba(220, 53, 69, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const percentage = Math.round((value / articles1.length) * 100);
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        if (articles2 && articles2.length > 0) {
            var sentimentPieCtx2 = document.getElementById('sentimentPieChart2').getContext('2d');
            
            var positive2 = articles2.filter(a => a.sentiment > 0.2).length;
            var neutral2 = articles2.filter(a => a.sentiment >= -0.2 && a.sentiment <= 0.2).length;
            var negative2 = articles2.filter(a => a.sentiment < -0.2).length;
            
            new Chart(sentimentPieCtx2, {
                type: 'pie',
                data: {
                    labels: ['Positive', 'Neutral', 'Negative'],
                    datasets: [{
                        data: [positive2, neutral2, negative2],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.7)',
                            'rgba(108, 117, 125, 0.7)',
                            'rgba(220, 53, 69, 0.7)'
                        ],
                        borderColor: [
                            'rgba(40, 167, 69, 1)',
                            'rgba(108, 117, 125, 1)',
                            'rgba(220, 53, 69, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.raw;
                                    const percentage = Math.round((value / articles2.length) * 100);
                                    return `${context.label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
    
    // Create sentiment by outlet charts
    if (articles1.length > 0) {
        var sentimentByOutlet1 = calculateSentimentByOutlet(articles1);
        var topOutlets1 = sentimentByOutlet1.slice(0, 15);
        
        if (topOutlets1 && topOutlets1.length > 0) {
            new Chart(document.getElementById('sentimentByOutletChart1'), {
                type: 'bar',
                data: {
                    labels: topOutlets1.map(item => `${item.outlet} (${item.count})`),
                    datasets: [{
                        label: 'Average Sentiment',
                        data: topOutlets1.map(item => item.avgSentiment),
                        backgroundColor: topOutlets1.map(item => getSentimentColor(item.avgSentiment)),
                        borderColor: 'rgba(0, 0, 0, 0.1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const sentiment = context.raw;
                                    let label = `Sentiment: ${sentiment.toFixed(2)}`;
                                    if (sentiment < -0.33) {
                                        label += ' (Negative)';
                                    } else if (sentiment < 0.33) {
                                        label += ' (Neutral)';
                                    } else {
                                        label += ' (Positive)';
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                autoSkip: false,
                                maxRotation: 0,
                                padding: 10
                            }
                        },
                        x: {
                            beginAtZero: false,
                            min: -1,
                            max: 1,
                            ticks: {
                                callback: function(value) {
                                    if (value === -1) return 'Negative';
                                    if (value === 0) return 'Neutral';
                                    if (value === 1) return 'Positive';
                                    return '';
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Create sentiment by outlet chart for query2 if it exists
        if (articles2 && articles2.length > 0) {
            var sentimentByOutlet2 = calculateSentimentByOutlet(articles2);
            var topOutlets2 = sentimentByOutlet2.slice(0, 15);
            
            if (topOutlets2 && topOutlets2.length > 0) {
                new Chart(document.getElementById('sentimentByOutletChart2'), {
                    type: 'bar',
                    data: {
                        labels: topOutlets2.map(item => `${item.outlet} (${item.count})`),
                        datasets: [{
                            label: 'Average Sentiment',
                            data: topOutlets2.map(item => item.avgSentiment),
                            backgroundColor: topOutlets2.map(item => getSentimentColor(item.avgSentiment)),
                            borderColor: 'rgba(0, 0, 0, 0.1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const sentiment = context.raw;
                                        let label = `Sentiment: ${sentiment.toFixed(2)}`;
                                        if (sentiment < -0.33) {
                                            label += ' (Negative)';
                                        } else if (sentiment < 0.33) {
                                            label += ' (Neutral)';
                                        } else {
                                            label += ' (Positive)';
                                        }
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                ticks: {
                                    autoSkip: false,
                                    maxRotation: 0,
                                    padding: 10
                                }
                            },
                            x: {
                                beginAtZero: false,
                                min: -1,
                                max: 1,
                                ticks: {
                                    callback: function(value) {
                                        if (value === -1) return 'Negative';
                                        if (value === 0) return 'Neutral';
                                        if (value === 1) return 'Positive';
                                        return '';
                                    }
                                }
                            }
                        }
                    }
                });
            }
        }
    }
    
    // Copy to Claude button functionality
    document.getElementById('copyToClaudeBtn').addEventListener('click', function() {
        var content = '';
        
        // Add query info
        content += `Media Analysis for "${query1}"`;
        if (query2) content += ` vs "${query2}"`;
        content += '\n\n';
        
        // Add date range
        content += `Date Range: ${analysis1.date_range.start} to ${analysis1.date_range.end}\n\n`;
        
        // Add coverage metrics
        content += '## Coverage Metrics\n\n';
        content += `${query1}: ${analysis1.total_articles} articles, Avg. Sentiment: ${analysis1.avg_sentiment.toFixed(2)}\n`;
        if (analysis2) {
            content += `${query2}: ${analysis2.total_articles} articles, Avg. Sentiment: ${analysis2.avg_sentiment.toFixed(2)}\n`;
        }
        content += '\n';
        
        // Add top sources
        content += '## Top Sources\n\n';
        analysis1.sources.slice(0, 5).forEach(source => {
            content += `- ${source.name}: ${source.count} articles\n`;
        });
        content += '\n';
        
        // Add top topics
        content += '## Top Topics\n\n';
        analysis1.topics.slice(0, 10).forEach(topic => {
            content += `- ${topic.topic}: ${topic.count} mentions\n`;
        });
        content += '\n';
        
        // Add articles
        content += '## Sample Articles\n\n';
        articles1.slice(0, 5).forEach(article => {
            content += `- "${article.title}" (${article.source.name}, ${article.publishedAt.split('T')[0]})\n`;
            content += `  Sentiment: ${article.sentiment.toFixed(2)}, URL: ${article.url}\n\n`;
        });
        
        // Add full JSON data
        content += '## Full JSON Data\n\n';
        content += '```json\n';
        const fullData = {
            query1: query1,
            query2: query2,
            analysis1: analysis1,
            analysis2: analysis2,
            articles1: articles1,
            articles2: articles2
        };
        content += JSON.stringify(fullData, null, 2);
        content += '\n```\n';
        
        // Copy to clipboard
        navigator.clipboard.writeText(content).then(function() {
            // Open Claude in a new tab
            window.open('https://claude.ai/chat', '_blank');
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            alert('Failed to copy to clipboard. Please try again.');
        });
    });
    
    // Share button functionality
    document.getElementById('shareBtn').addEventListener('click', function() {
        // Get the current URL
        const currentUrl = window.location.href;
        
        // Copy to clipboard
        navigator.clipboard.writeText(currentUrl).then(function() {
            // Create a temporary element to show success message
            const successMsg = document.createElement('div');
            successMsg.textContent = 'Link copied to clipboard!';
            successMsg.style.position = 'fixed';
            successMsg.style.bottom = '20px';
            successMsg.style.left = '50%';
            successMsg.style.transform = 'translateX(-50%)';
            successMsg.style.backgroundColor = 'var(--primary-color)';
            successMsg.style.color = 'white';
            successMsg.style.padding = '10px 20px';
            successMsg.style.borderRadius = '4px';
            successMsg.style.zIndex = '1000';
            successMsg.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
            
            // Add to body
            document.body.appendChild(successMsg);
            
            // Remove after 3 seconds
            setTimeout(function() {
                successMsg.style.opacity = '0';
                successMsg.style.transition = 'opacity 0.5s ease';
                setTimeout(function() {
                    document.body.removeChild(successMsg);
                }, 500);
            }, 3000);
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            alert('Failed to copy link to clipboard. Please try again.');
        });
    });
});
