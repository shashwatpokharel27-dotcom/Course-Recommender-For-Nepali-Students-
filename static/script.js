// --- 1. INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("🚀 Initialization: Fetching suggestions from FastAPI...");

    try {
        const response = await fetch('/suggestions');
        if (!response.ok) throw new Error(`Server returned status: ${response.status}`);

        const data = await response.json();
        console.log("📦 Suggestion Catalog Loaded:", data);

        // Map form IDs to the exact keys returned by your FastAPI JSON
        const inputConfigs = [
            { id: 'interest', chips: 'interest-chips', key: 'interest' },
            { id: 'goal', chips: 'goal-chips', key: 'career goal' }, // Matches 'career goal' space key
            { id: 'skills', chips: 'skills-chips', key: 'skills' }
        ];

        inputConfigs.forEach(config => {
            if (data[config.key]) {
                setupAutocomplete(config, data[config.key]);
            } else {
                console.error(`❌ Error: Key "${config.key}" not found in suggestions JSON.`);
            }
        });

    } catch (err) {
        console.error("❌ Critical Initialization Error:", err);
    }
});


// --- 2. MAIN AUTOCOMPLETE LAYER ---
function setupAutocomplete(config, categoryData) {
    const input = document.getElementById(config.id);
    const chipContainer = document.getElementById(config.chips);

    if (!input || !chipContainer) return;

    const allValues = categoryData.all || [];
    const topValues = categoryData.top || allValues.slice(0, 5);

    // Create custom dropdown box container dynamically
    const suggestionBox = document.createElement('div');
    suggestionBox.className = 'suggestion-box hidden'; // Kept hidden on initial load
    input.parentNode.appendChild(suggestionBox);

    // Show suggestions when user focuses inside the input field
    input.addEventListener('focus', () => {
        const query = input.value.toLowerCase().trim();
        suggestionBox.classList.remove('hidden');
        
        if (query === "") {
            renderSuggestions(topValues, suggestionBox, input, chipContainer);
        } else {
            const filtered = allValues.filter(item =>
                item.toLowerCase().includes(query)
            ).slice(0, 8);
            renderSuggestions(filtered, suggestionBox, input, chipContainer);
        }
    });

    // Filter list context interactively on keystroke input
    input.addEventListener('input', () => {
        const query = input.value.toLowerCase().trim();

        if (query === "") {
            renderSuggestions(topValues, suggestionBox, input, chipContainer);
            return;
        }

        const filtered = allValues.filter(item =>
            item.toLowerCase().includes(query)
        ).slice(0, 8);

        renderSuggestions(filtered, suggestionBox, input, chipContainer);
    });

    // Populate the quick-select chip UI bar
    chipContainer.innerHTML = '';
    topValues.forEach(val => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.innerText = val;

        chip.onclick = () => {
            input.value = val;
            suggestionBox.innerHTML = '';
            suggestionBox.classList.add('hidden');
            setActiveChip(chipContainer, chip);
        };

        chipContainer.appendChild(chip);
    });

    // Close dropdown boxes securely when user clicks outside the element zone
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestionBox.contains(e.target)) {
            suggestionBox.innerHTML = '';
            suggestionBox.classList.add('hidden');
        }
    });
}


// --- 3. RENDER SUGGESTION ENGINE ---
function renderSuggestions(list, container, input, chipContainer) {
    container.innerHTML = '';
    
    if (list.length === 0) {
        const noResult = document.createElement('div');
        noResult.className = 'suggestion-item';
        noResult.style.color = 'var(--text-muted)';
        noResult.style.cursor = 'default';
        noResult.innerText = "No matches found";
        container.appendChild(noResult);
        return;
    }

    list.forEach(item => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.innerText = item;

        div.onclick = () => {
            input.value = item;
            container.innerHTML = '';
            container.classList.add('hidden');

            // Synchronize chip highlight state if selected via drop list option
            matchChipToValue(chipContainer, item);
        };

        container.appendChild(div);
    });
}


// --- 4. CHIP ACTIVE STATE UTILITIES ---
function setActiveChip(container, activeChip) {
    container.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    activeChip.classList.add('active');
}

function matchChipToValue(container, value) {
    container.querySelectorAll('.chip').forEach(chip => {
        if (chip.innerText.toLowerCase() === value.toLowerCase()) {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });
}


// --- 5. FORM SUBMISSION PIPELINE ---
window.latestRecommendations = [];

document.getElementById('recommenderForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error-message');
    const cardsWrapper = document.getElementById('cards-wrapper');
    const eligibilityInfo = document.getElementById('eligibility-info');

    errorDiv.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    submitBtn.disabled = true;

    const payload = {
        stream: document.getElementById('stream').value,
        gpa: parseFloat(document.getElementById('gpa').value),
        interest: document.getElementById('interest').value,
        career_goal: document.getElementById('goal').value,
        skills: document.getElementById('skills').value,
        budget_amount: parseInt(document.getElementById('budget').value)
    };

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Prediction system execution failed");
        }

        cardsWrapper.innerHTML = '';
        window.latestRecommendations = data.recommendations;
        
        // Render Action Banner Context Information
        eligibilityInfo.innerHTML = `
            <p style="margin-bottom: 1rem; color: var(--text-muted);">Found ${data.recommendations.length} ideal career paths for your profile:</p>
            <div class="action-banner" style="
                background: rgba(99, 102, 241, 0.08); 
                border-left: 4px solid #6366f1; 
                padding: 12px 16px; 
                border-radius: 8px; 
                margin-bottom: 1.5rem; 
                font-size: 0.9rem; 
                line-height: 1.4;
                color: #4f46e5;
                font-weight: 500;
                animation: fadeIn 0.5s ease-out;
            ">
                💡 <strong>What's next?</strong> Pick a course below to see the essential books, you should read <em>before</em> your first day of college!
            </div>
        `;

        // Render newly maximized match recommendation row elements
        data.recommendations.forEach((rec, index) => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.setAttribute('onclick', `handleCardClick(${index})`);

            const score = rec.confidence || rec.score || 0;

            card.innerHTML = `
                <div class="course-info" style="text-align: left;">
                    <div class="course-name" style="color: #1e1b4b; font-weight: 800;">${rec.course.toUpperCase()}</div> 
                    <div class="meta-info" style="color: var(--primary); font-weight: 600; margin-top: 8px; font-size: 1.05rem;">View Books before starting course →</div>
                </div>
                <div class="confidence-badge">${Math.round(score)}% Match</div>
            `;

            cardsWrapper.appendChild(card);
        });

        loadingDiv.classList.add('hidden');
        resultsDiv.classList.remove('hidden');

    } catch (error) {
        loadingDiv.classList.add('hidden');
        errorDiv.classList.remove('hidden');
        errorDiv.innerText = error.message;
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Generate AI Recommendations";
    }
});


// --- 6. GLOBAL ROUTER REDIRECT ---
window.handleCardClick = function(index) {
    const selectedData = window.latestRecommendations[index];
    if (selectedData) {
        localStorage.setItem('selectedCourse', selectedData.course.toUpperCase());
        localStorage.setItem('courseBooks', JSON.stringify(selectedData.books || []));
        window.location.href = '/books';
    }
};