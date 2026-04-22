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

document.getElementById('insuranceForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show Loading Overlay
    const loader = document.getElementById('loading-overlay');
    loader.classList.remove('hidden');
            
    const formData = new FormData(this);

    try {
        const response = await fetch('/process_claim', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success') {
            // Update Submission Details
            document.getElementById('res-name').textContent = formData.get('name');
            document.getElementById('res-type').textContent = formData.get('claim_type');
            document.getElementById('res-facility').textContent = formData.get('medical_facility');
            document.getElementById('res-amount').textContent = '$' + parseFloat(formData.get('total_claim_amount')).toLocaleString();
            document.getElementById('res-id').textContent = 'ID: PO-' + Math.floor(10000 + Math.random() * 90000);

            // Update AI Extracted Data
            document.getElementById('res-disease').textContent = result.disease || 'Not Detected';
            document.getElementById('res-billed-expense').textContent = '$' + (result.bill_expense || 0).toLocaleString();

            // Update AI Analysis
            const analysisContainer = document.getElementById('res-analysis');
            analysisContainer.innerHTML = result.analysis;

            // Visual indicator for Decision (Green for accepted, Red for rejected)
            const header = document.getElementById('res-header');
            const iconContainer = document.getElementById('res-icon');
            
            if (result.analysis.toLowerCase().includes('accepted')) {
                header.className = 'bg-gradient-to-r from-emerald-600 to-teal-600 p-8 text-center text-white';
                document.getElementById('res-status-title').textContent = 'Claim Accepted';
                iconContainer.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            } else {
                header.className = 'bg-gradient-to-r from-rose-600 to-pink-600 p-8 text-center text-white';
                document.getElementById('res-status-title').textContent = 'Claim Rejected';
                iconContainer.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
            }

            // Change section
            showSection('result');
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        console.error('Submission Error:', error);
        alert('An error occurred while processing your claim. Please try again.');
    } finally {
        // Hide Loading Overlay
        loader.classList.add('hidden');
    }
});

// File Upload UI Update
const fileInput = document.getElementById('file-input');
const fileChosen = document.getElementById('file-chosen');
const filePrompt = document.getElementById('file-prompt');
const dropZone = document.getElementById('drop-zone');

if (fileInput) {
    fileInput.addEventListener('change', function() {
        if (this.files && this.files.length > 0) {
            const fileName = this.files[0].name;
            fileChosen.textContent = 'Selected: ' + fileName;
            fileChosen.classList.remove('hidden');
            filePrompt.textContent = 'Change file?';
            dropZone.classList.add('bg-blue-50/50', 'border-blue-400');
            dropZone.classList.remove('border-slate-200');
        } else {
            fileChosen.classList.add('hidden');
            filePrompt.textContent = 'Click to upload or drag & drop';
            dropZone.classList.remove('bg-blue-50/50', 'border-blue-400');
            dropZone.classList.add('border-slate-200');
        }
    });
}