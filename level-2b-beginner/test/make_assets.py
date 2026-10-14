"""Builds the synthetic assets in assets/: two bar charts, a trend chart, a 3-page quarterly report
(table on p.2) and a 6-page employee handbook (vacation p.4, $500 equipment allowance p.3, no stipend).

    uv run --with matplotlib --with reportlab python3 make_assets.py

Synthetic on purpose: the ground truth is known, so every number Claude returns can be checked.
"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

os.makedirs("assets", exist_ok=True)
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
q3 = [42.0, 31.5, 18.2, 9.1]
q4 = [44.1, 33.0, 24.6, 9.4]
for name, vals, title in [("chart_q3.png", q3, "Q3 2026 Revenue by Region ($M)"), ("chart_q4.png", q4, "Q4 2026 Revenue by Region ($M)")]:
    fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
    bars = ax.bar(regions, vals, color=["#3b82f6", "#10b981", "#f59e0b", "#ef4444"])
    ax.set_title(title, fontsize=16); ax.set_ylabel("Revenue ($M)"); ax.set_ylim(0, 50)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.1f}", ha="center", fontsize=12)
    fig.tight_layout(); fig.savefig(f"assets/{name}"); plt.close(fig)
fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
qs = ["Q1", "Q2", "Q3", "Q4"]; rev = [88.2, 94.7, 100.8, 111.1]
ax.plot(qs, rev, marker="o", lw=3, color="#3b82f6"); ax.set_title("2026 Total Revenue ($M)", fontsize=16); ax.set_ylim(80, 115)
for x, y in zip(qs, rev):
    ax.text(x, y + 1, f"{y}", ha="center")
fig.tight_layout(); fig.savefig("assets/chart.png"); plt.close(fig)

ss = getSampleStyleSheet(); H = ss["Heading1"]; H2 = ss["Heading2"]; B = ss["BodyText"]
def P(t, s=B): return Paragraph(t, s)

doc = SimpleDocTemplate("assets/quarterly_report.pdf", pagesize=LETTER, title="Northwind Analytics Q4 2026 Report")
tbl = Table([["Quarter", "Revenue ($M)", "Operating Cost ($M)", "Operating Margin"],
             ["Q1 2026", "88.2", "71.4", "19.0%"], ["Q2 2026", "94.7", "75.1", "20.7%"],
             ["Q3 2026", "100.8", "82.9", "17.8%"], ["Q4 2026", "111.1", "84.3", "24.1%"]])
tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                         ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                         ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]))
doc.build([
    P("Northwind Analytics — Q4 2026 Quarterly Report", H), Spacer(1, 12), P("Executive summary", H2),
    P("Northwind Analytics closed 2026 with its strongest quarter on record. Total revenue reached $111.1 million in Q4, up 10.2% quarter over quarter and 26% year over year. Growth was led by the Asia Pacific region, where the launch of the self-serve analytics tier more than offset softness in enterprise renewals."),
    P("Three themes defined the year. First, self-serve adoption: 61% of new accounts in Q4 started on the self-serve tier, compared with 22% in Q1. Second, infrastructure efficiency: migrating the query engine to the new storage layer reduced compute cost per query by 38%. Third, regional diversification: North America fell from 54% of revenue in Q1 to 40% in Q4 as Europe and Asia Pacific grew."),
    P("Headcount ended the year at 412, up from 365. The company remained free-cash-flow positive in every quarter."), PageBreak(),
    P("Financial results", H2),
    P("The table below summarizes revenue, operating cost and operating margin for each quarter of 2026. Operating margin is operating income divided by revenue."),
    Spacer(1, 8), tbl, Spacer(1, 12),
    P("Operating cost rose only 1.7% from Q3 to Q4 despite the revenue increase, reflecting the full-quarter effect of the storage migration completed in September. Sales and marketing spend was flat; research and development grew 9% with the opening of the Singapore engineering office."),
    P("Deferred revenue grew to $48.3 million, a 31% increase from year end 2025, driven by multi-year self-serve commitments."), PageBreak(),
    P("Regional performance and outlook", H2),
    P("Asia Pacific revenue grew from $18.2 million in Q3 to $24.6 million in Q4, a 35% increase, the fastest regional growth in company history. Europe grew 4.8% to $33.0 million. North America grew 5% to $44.1 million. Latin America was broadly flat at $9.4 million."),
    P("For 2027 the company expects revenue growth of 20% to 24%, with operating margin between 22% and 25%. The primary risks are enterprise renewal rates in North America and currency exposure in Asia Pacific. The company does not provide guidance beyond fiscal 2027."),
])

doc = SimpleDocTemplate("assets/employee_handbook.pdf", pagesize=LETTER, title="Northwind Analytics Employee Handbook")
doc.build([
    P("Northwind Analytics Employee Handbook", H), P("Revised January 2026", B), Spacer(1, 12),
    P("1. Welcome", H2), P("This handbook describes the policies and benefits that apply to all regular employees of Northwind Analytics. It is not a contract of employment. Where local law provides a greater benefit than this handbook, local law applies. Questions about any policy should go to your manager or to People Operations at people@northwind.example."),
    P("2. Working hours", H2), P("Standard working hours are 40 hours per week. Core collaboration hours are 10:00 to 15:00 in your local time zone; outside core hours you may arrange your schedule with your manager. Overtime for non-exempt employees is paid at 1.5 times the base hourly rate for hours over 40 in a week."), PageBreak(),
    P("3. Code of conduct", H2), P("We expect every employee to act with integrity, treat colleagues with respect, and protect customer data. Harassment of any kind is not tolerated. Concerns can be raised with any manager, with People Operations, or anonymously through the ethics hotline. Retaliation against anyone who raises a concern in good faith is prohibited."),
    P("4. Confidentiality", H2), P("Customer data, source code, financial results and product plans are confidential. Do not share them outside the company or with colleagues who do not need them for their work. Confidentiality obligations continue after employment ends."), PageBreak(),
    P("5. Equipment and workspace", H2), P("Every employee receives a company laptop and may choose a monitor, keyboard and headset from the approved catalogue. In addition, each employee receives a one-time equipment allowance of $500 in their first month to furnish a home workspace, for items such as a desk, a chair or lighting. Receipts must be submitted within 60 days. Equipment purchased with the allowance belongs to the employee."),
    P("6. Expenses", H2), P("Reasonable business expenses are reimbursed when submitted with receipts within 30 days. Travel must be booked through the company travel tool. Meals while travelling are reimbursed up to $75 per day."), PageBreak(),
    P("7. Paid time off", H2), P("New employees receive 15 days of paid vacation in their first year of employment, accruing at 1.25 days per month from the start date. After three years of service the entitlement increases to 20 days per year, and after six years to 25 days. Up to 5 unused days may be carried into the following year; carried days must be used by March 31."),
    P("In addition to vacation, all employees receive 10 paid company holidays per year and 8 days of paid sick leave. Sick leave does not carry over."),
    P("Vacation requests of five or more consecutive days should be submitted at least four weeks in advance. Managers approve requests based on team coverage and will not unreasonably refuse."), PageBreak(),
    P("8. Parental leave", H2), P("Primary caregivers receive 16 weeks of fully paid parental leave; secondary caregivers receive 6 weeks. Leave may be taken within 12 months of the birth or adoption. Employees on parental leave continue to accrue vacation and remain eligible for the annual bonus on a pro-rated basis."),
    P("9. Health and retirement", H2), P("The company pays 100% of the employee premium and 75% of dependent premiums for the standard medical, dental and vision plans. Employees may contribute to the 401(k) plan from their first paycheck; the company matches 100% of contributions up to 4% of salary, vesting immediately."), PageBreak(),
    P("10. Performance and compensation", H2), P("Performance reviews take place twice a year, in June and December. Compensation is reviewed annually in January. The annual bonus target is 10% of base salary for individual contributors and 15% for managers, paid in February based on company and individual performance."),
    P("11. Leaving the company", H2), P("Employees are asked to give two weeks' notice. Unused accrued vacation is paid out on the final paycheck where required by local law. Company equipment must be returned within 10 days of the last working day; the equipment allowance purchases from section 5 are not returned."),
])
print("assets written")
