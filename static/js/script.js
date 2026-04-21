function showSection(sectionId) {
    const landing = document.getElementById('landing-section');
    const form = document.getElementById('claim-form');
    const result = document.getElementById('result-section');
            
    // Hide all
    [landing, form, result].forEach(el => el.classList.add('hidden'));

    if (sectionId === 'landing') {
        landing.classList.remove('hidden');
        form.classList.remove('hidden');
    } else if (sectionId === 'result') {
        result.classList.remove('hidden');
    }
            
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.getElementById('insuranceForm').addEventListener('submit', function(e) {
    e.preventDefault();
            
    // Simulation of data processing
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    // Update result UI
    document.getElementById('res-name').textContent = data.name;
    document.getElementById('res-type').textContent = data.claim_type;
    document.getElementById('res-facility').textContent = data.medical_facility;
    document.getElementById('res-amount').textContent = '$' + parseFloat(data.total_claim_amount).toLocaleString();
    document.getElementById('res-id').textContent = 'PO-' + Math.floor(10000 + Math.random() * 90000);

    // Change section
    showSection('result');
});