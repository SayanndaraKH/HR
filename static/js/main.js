// HRMS JavaScript Controller

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // 2. Modal open/close listeners
    const modalOpenButtons = document.querySelectorAll('[data-modal-target]');
    modalOpenButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-modal-target');
            const modal = document.getElementById(targetId);
            if (modal) {
                modal.classList.add('active');
            }
        });
    });

    const modalCloseButtons = document.querySelectorAll('[data-modal-close]');
    modalCloseButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Close modal on background click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });

    // 3. Quick Table Instant Search (Client side filter if input has class .table-search)
    const tableSearchInput = document.querySelector('.table-search');
    if (tableSearchInput) {
        tableSearchInput.addEventListener('keyup', function() {
            const query = this.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.searchable-table tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    // 4. Payroll Quick Adjustment Modal dynamic filler
    const payrollEditBtns = document.querySelectorAll('.btn-edit-payroll');
    payrollEditBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const payrollId = btn.dataset.payrollId;
            const empName = btn.dataset.empName;
            const bonus = btn.dataset.bonus || 0;
            const allowance = btn.dataset.allowance || 0;
            const advance = btn.dataset.advance || 0;
            const other = btn.dataset.other || 0;
            const notes = btn.dataset.notes || '';

            const modal = document.getElementById('modal-edit-payroll');
            if (modal) {
                modal.querySelector('#modal-payroll-emp-name').textContent = empName;
                modal.querySelector('#modal-payroll-id').value = payrollId;
                modal.querySelector('#modal-payroll-bonus').value = bonus;
                modal.querySelector('#modal-payroll-allowance').value = allowance;
                modal.querySelector('#modal-payroll-advance').value = advance;
                modal.querySelector('#modal-payroll-other').value = other;
                modal.querySelector('#modal-payroll-notes').value = notes;
                
                const form = modal.querySelector('form');
                form.action = `/payroll/${payrollId}/edit`;

                modal.classList.add('active');
            }
        });
    });

    // 5. Leave Action Modal filler
    const leaveActionBtns = document.querySelectorAll('.btn-leave-action');
    leaveActionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const leaveId = btn.dataset.leaveId;
            const empName = btn.dataset.empName;
            const action = btn.dataset.action; // approve or reject

            const modal = document.getElementById('modal-leave-action');
            if (modal) {
                modal.querySelector('#leave-action-id').value = leaveId;
                modal.querySelector('#leave-action-type').value = action;
                modal.querySelector('#leave-action-emp').textContent = empName;
                
                const title = action === 'approve' ? 'អនុម័តច្បាប់ឈប់សម្រាក (Approve Leave)' : 'បដិសេធច្បាប់ឈប់សម្រាក (Reject Leave)';
                modal.querySelector('#leave-modal-title').textContent = title;

                const submitBtn = modal.querySelector('#leave-submit-btn');
                if (action === 'approve') {
                    submitBtn.className = 'btn btn-success';
                    submitBtn.textContent = 'យល់ព្រមអនុម័ត';
                } else {
                    submitBtn.className = 'btn btn-danger';
                    submitBtn.textContent = 'បដិសេធចោល';
                }

                const form = modal.querySelector('form');
                form.action = `/attendance/leaves/${leaveId}/action`;

                modal.classList.add('active');
            }
        });
    });
});
