function startScraping() {
    const urlInput = document.getElementById('urlInput');
    const useTor = document.getElementById('useTor');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');

    if (!urlInput.value) {
        showError('Please enter a URL');
        return;
    }

    loading.classList.remove('hidden');
    results.innerHTML = '';

    fetch('/scrape', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            url: urlInput.value,
            use_tor: useTor.checked
        })
    })
    .then(response => response.json())
    .then(data => {
        loading.classList.add('hidden');
        if (data.error) {
            showError(data.error);
        } else {
            displayResults(data);
        }
    })
    .catch(error => {
        loading.classList.add('hidden');
        showError('An error occurred while scraping');
        console.error('Error:', error);
    });
}

function showError(message) {
    const results = document.getElementById('results');
    results.innerHTML = `<div class="error">${message}</div>`;
}

function displayResults(data) {
    const results = document.getElementById('results');
    let html = '';

    for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'object') {
            html += `
                <div class="result-item">
                    <h3>${key}</h3>
                    <p><strong>Category:</strong> ${value.category || 'N/A'}</p>
                    <p><strong>Confidence:</strong> ${(value.confidence * 100).toFixed(2)}%</p>
                    <p><strong>Summary:</strong> ${value.summary || 'N/A'}</p>
                </div>
            `;
        }
    }

    results.innerHTML = html || '<div class="error">No results found</div>';
}
