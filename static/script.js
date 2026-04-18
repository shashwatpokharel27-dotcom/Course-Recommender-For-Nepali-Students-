// --- 1. INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("Fetching suggestions...");

    try {
        const response = await fetch('/suggestions');
        if (!response.ok) throw new Error("Failed to fetch");

        const data = await response.json();

        const inputConfigs = [
            { id: 'interest', chips: 'interest-chips', key: 'interest' },
            { id: 'goal', chips: 'goal-chips', key: 'career goal' },
            { id: 'skills', chips: 'skills-chips', key: 'skills' }
        ];

        inputConfigs.forEach(config => {
            if (data[config.key]) {
                setupAutocomplete(config, data[config.key]);
            }
        });

    } catch (err) {
        console.error("Error:", err);
    }
});


// --- 2. MAIN AUTOCOMPLETE FUNCTION ---
function setupAutocomplete(config, categoryData) {
    const input = document.getElementById(config.id);
    const chipContainer = document.getElementById(config.chips);

    if (!input || !chipContainer) return;

    const allValues = categoryData.all || [];
    const topValues = categoryData.top || allValues.slice(0, 5);

    // Create suggestion box
    const suggestionBox = document.createElement('div');
    suggestionBox.className = 'suggestion-box';
    input.parentNode.appendChild(suggestionBox);

    // --- SHOW DEFAULT TOP VALUES ---
    renderSuggestions(topValues, suggestionBox, input);

    // --- INPUT EVENT (DYNAMIC FILTER) ---
    input.addEventListener('input', () => {
        const query = input.value.toLowerCase().trim();

        if (query === "") {
            renderSuggestions(topValues, suggestionBox, input);
            return;
        }

        const filtered = allValues.filter(item =>
            item.toLowerCase().includes(query)
        ).slice(0, 8); // limit results

        renderSuggestions(filtered, suggestionBox, input);
    });

    // --- CHIP GENERATION (TOP VALUES) ---
    chipContainer.innerHTML = '';
    topValues.forEach(val => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.innerText = val;

        chip.onclick = () => {
            input.value = val;
            suggestionBox.innerHTML = '';
            setActiveChip(chipContainer, chip);
        };

        chipContainer.appendChild(chip);
    });

    // Hide suggestions when clicked outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestionBox.contains(e.target)) {
            suggestionBox.innerHTML = '';
        }
    });
}


// --- 3. RENDER SUGGESTIONS ---
function renderSuggestions(list, container, input) {
    container.innerHTML = '';

    list.forEach(item => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.innerText = item;

        div.onclick = () => {
            input.value = item;
            container.innerHTML = '';
        };

        container.appendChild(div);
    });
}


// --- 4. CHIP ACTIVE STATE ---
function setActiveChip(container, activeChip) {
    container.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    activeChip.classList.add('active');
}


// --- 5. FORM SUBMISSION ---
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
            throw new Error(data.detail || "Prediction failed");
        }

        cardsWrapper.innerHTML = '';
        eligibilityInfo.innerText =
            `Found ${data.eligible_courses_count} courses. Matches for your profile:`;

        data.recommendations.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'result-card';

            const score = rec.confidence || rec.score || 0;

            card.innerHTML = `
                <div class="course-info">
                    <div class="course-name">${rec.course}</div>
                    <div class="meta-info">AI Analysis Score</div>
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