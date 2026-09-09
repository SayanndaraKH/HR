"""
Cambodian Payroll & Tax Calculation Engine
Calculates standard proration, overtime, NSSF (ប.ស.ស), and resident progressive salary tax (ពន្ធលើប្រាក់បៀវត្ស).
"""

KHR_PER_USD = 4100.0  # Standard indicative exchange rate

def calculate_cambodia_salary_tax(taxable_salary_usd):
    """
    Calculate Cambodian Salary Tax on Monthly Resident Income (in USD).
    Brackets in KHR:
      0 - 1,500,000 KHR: 0%
      1,500,001 - 2,000,000 KHR: 5% (less 75,000 KHR)
      2,000,001 - 8,500,000 KHR: 10% (less 175,000 KHR)
      8,500,001 - 12,500,000 KHR: 15% (less 600,000 KHR)
      > 12,500,000 KHR: 20% (less 1,225,000 KHR)
    """
    salary_khr = taxable_salary_usd * KHR_PER_USD
    
    if salary_khr <= 1500000:
        tax_khr = 0.0
    elif salary_khr <= 2000000:
        tax_khr = (salary_khr * 0.05) - 75000
    elif salary_khr <= 8500000:
        tax_khr = (salary_khr * 0.10) - 175000
    elif salary_khr <= 12500000:
        tax_khr = (salary_khr * 0.15) - 600000
    else:
        tax_khr = (salary_khr * 0.20) - 1225000
        
    tax_usd = max(0.0, tax_khr / KHR_PER_USD)
    return round(tax_usd, 2)

def calculate_nssf(base_salary_usd):
    """
    NSSF (National Social Security Fund - ប.ស.ស) Pension Scheme:
    Employee contributes 2% of contributory wage, with maximum wage ceiling of 1,200,000 KHR (~$292.68).
    Maximum deduction is approx $5.85 USD / month.
    """
    ceiling_usd = 1200000 / KHR_PER_USD  # ~$292.68
    contributory_wage = min(base_salary_usd, ceiling_usd)
    nssf_usd = contributory_wage * 0.02
    return round(nssf_usd, 2)

def compute_employee_payroll(base_salary, worked_days=26, standard_days=26, ot_hours=0.0, 
                             bonus=0.0, allowance=0.0, absent_days=0.0, late_minutes=0,
                             advance_salary=0.0, other_deductions=0.0, ot_rate=1.5):
    """
    Complete payroll computation for an employee.
    """
    standard_days = max(1, standard_days)
    daily_rate = base_salary / standard_days
    hourly_rate = daily_rate / 8.0
    
    # Overtime
    ot_amount = round(hourly_rate * ot_hours * ot_rate, 2)
    
    # Prorated base for worked days
    actual_base = round((min(worked_days, standard_days) / standard_days) * base_salary, 2)
    
    # Gross
    gross_salary = round(actual_base + ot_amount + bonus + allowance, 2)
    
    # Absent deduction (if not already factored in worked days)
    absent_deduction = round(daily_rate * absent_days, 2)
    
    # Late deduction: e.g. $0.05 per late minute or flat after grace period
    late_deduction = round((late_minutes / 60.0) * hourly_rate, 2) if late_minutes > 15 else 0.0
    
    # NSSF
    nssf_deduction = calculate_nssf(base_salary)
    
    # Taxable Salary for Cambodia: Gross minus NSSF (and family relief if applicable)
    taxable_amount = max(0.0, gross_salary - nssf_deduction)
    salary_tax = calculate_cambodia_salary_tax(taxable_amount)
    
    # Total Deductions
    total_deductions = round(absent_deduction + late_deduction + nssf_deduction + salary_tax + advance_salary + other_deductions, 2)
    
    # Net Salary
    net_salary = round(max(0.0, gross_salary - total_deductions), 2)
    
    return {
        'base_salary': round(base_salary, 2),
        'standard_work_days': standard_days,
        'worked_days': worked_days,
        'daily_rate': round(daily_rate, 2),
        'hourly_rate': round(hourly_rate, 2),
        'ot_hours': ot_hours,
        'ot_rate': ot_rate,
        'ot_amount': ot_amount,
        'bonus': round(bonus, 2),
        'allowance': round(allowance, 2),
        'gross_salary': gross_salary,
        'absent_days': absent_days,
        'absent_deduction': absent_deduction,
        'late_minutes': late_minutes,
        'late_deduction': late_deduction,
        'nssf_deduction': nssf_deduction,
        'salary_tax': salary_tax,
        'advance_salary': round(advance_salary, 2),
        'other_deductions': round(other_deductions, 2),
        'total_deductions': total_deductions,
        'net_salary': net_salary,
        'net_salary_khr': round(net_salary * KHR_PER_USD, 0)
    }
