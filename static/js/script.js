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
    
    const formData = new FormData(this);
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('hidden');
    
    try {
        const response = await fetch('/process_claim', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Update UI with extracted info
            document.getElementById('res-name').textContent = formData.get('name');
            document.getElementById('res-type').textContent = formData.get('claim_type');
            document.getElementById('res-facility').textContent = formData.get('medical_facility');
            document.getElementById('res-amount').textContent = '$' + formData.get('total_claim_amount');
            document.getElementById('res-treatment-date').textContent = formData.get('date');
            document.getElementById('res-disease').textContent = result.extracted_disease;
            document.getElementById('res-billed-expense').textContent = '$' + result.actual_expense;
            
            // Place the AI report
            document.getElementById('res-analysis').innerHTML = result.output;

            // Update Header UI based on Decision
            const header = document.getElementById('res-header');
            const iconContainer = document.getElementById('res-icon');
            const statusTitle = document.getElementById('res-status-title');
            
            if (result.output.includes("DECISION: ACCEPTED")) {
                header.className = "bg-gradient-to-r from-emerald-500 to-teal-600 p-8 text-center text-white";
                iconContainer.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
                statusTitle.textContent = "Claim Accepted";
            } else if (result.output.includes("DECISION: REJECTED") || result.output.includes("REJECTION:")) {
                header.className = "bg-gradient-to-r from-red-500 to-rose-600 p-8 text-center text-white";
                iconContainer.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
                statusTitle.textContent = "Claim Rejected";
            } else {
                // Default blue
                header.className = "bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-center text-white";
                iconContainer.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
                statusTitle.textContent = "Claim Processed";
            }
            
            // Populate PDF Template
            document.getElementById('pdf-res-name').textContent = formData.get('name');
            document.getElementById('pdf-res-type').textContent = formData.get('claim_type');
            document.getElementById('pdf-res-facility').textContent = formData.get('medical_facility');
            document.getElementById('pdf-res-amount').textContent = '$' + formData.get('total_claim_amount');
            document.getElementById('pdf-res-treatment-date').textContent = formData.get('date');
            document.getElementById('pdf-res-disease').textContent = result.extracted_disease;
            document.getElementById('pdf-res-billed-expense').textContent = '$' + result.actual_expense;
            document.getElementById('pdf-res-status').textContent = statusTitle.textContent;
            document.getElementById('pdf-res-analysis').innerHTML = result.output;
            
            showSection('result');
        } else {
            alert("Error: " + (result.message || "Unknown error"));
        }
    } catch (error) {
        console.error("Error processing claim:", error);
        alert("An error occurred while processing your claim.");
    } finally {
        loadingOverlay.classList.add('hidden');
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

// PDF Download Logic
document.getElementById('download-report').addEventListener('click', function() {
    const element = document.getElementById('pdf-template');
    element.classList.remove('hidden'); // Show temporarily for capture
    
    const opt = {
        margin: [0.5, 0.5],
        filename: 'PolicyOracle_Claim_Report.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2, 
            useCORS: true,
            letterRendering: true,
            scrollX: 0,
            scrollY: 0
        },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };
    
    html2pdf().set(opt).from(element).save().then(() => {
        element.classList.add('hidden'); // Hide again
    });
});