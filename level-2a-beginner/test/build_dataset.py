"""Build 200 realistic support messages with ground-truth labels.
Deterministic (seeded) so the dataset is reproducible. Mix of styles: short, long, typos,
caps, polite, angry, mixed-intent (label = the primary ask)."""
import json, random

random.seed(20261013)

BILLING = [
    "I was charged twice this month.", "Why is my invoice $49 when the plan says $29?", "charged for a seat I removed last week",
    "Can I get a refund for the annual plan? Only used it two days.", "My card was declined but you still show the payment as pending??",
    "Please send me the receipt for March.", "The VAT on my invoice is wrong, we're a registered business in Germany.",
    "I cancelled in June and you're still billing me", "how do i update my credit card", "Double charge on 10/02, order #88213 and #88214 are identical",
    "Need an invoice with our PO number on it", "You charged my old card instead of the new one I added.", "Is the student discount still available?",
    "i want to downgrade to the free plan, why is there no button", "Was billed in USD, I'm in Canada, expected CAD.",
    "Refund please. Didn't authorize this renewal.", "What does the 'usage overage' line on my bill mean?", "Our finance team needs a W-9 before they'll pay.",
    "The promo code SAVE20 didn't apply at checkout", "Pro-rated charge after upgrading seems way too high",
    "hey quick q, do you do yearly billing? how much is it", "Payment failed 3 times, card is fine everywhere else.", "Why did my price go up without notice?",
    "I need to change the billing email to accounts@ourco.com", "Can you split one invoice across two cost centers?",
    "WHY AM I BEING CHARGED FOR 12 USERS WE HAVE 8", "cancel my subscription effective immediately and confirm no further charges",
    "Does the enterprise tier include the API or is that extra $?", "Receipt says 'Acme Labs' but our company is 'Acme Laboratories Inc', can you fix for tax",
    "Trial ended and I got billed before I could decide. Not cool.", "I'd like to switch from monthly to annual, is there a discount?",
    "Credit note for last month's outage as promised by your rep?", "my invoice pdf won't download, 404", "Can we pay by wire instead of card?",
    "Charged $0.00 then $199.00 a minute later, is that normal?", "Where do I find my payment history?", "You refunded $20, I was charged $40.",
    "Is there a nonprofit rate?", "Renewal is next week, can you pause instead of cancelling?", "I think someone used my card on your site, I don't have an account",
    "Add-on 'priority support' appeared on my bill, I never added it", "Do you charge per API call or per seat?", "Please remove the late fee, the ACH was delayed by our bank",
    "Our contract says $1,200/yr but the invoice is $1,440", "Need to update tax exemption certificate", "Why two line items for the same product?",
    "stop charging me!!! i have emailed 3 times", "Can I get the invoice in EUR?", "Is the first month free for new teams?", "Billing portal shows a $0 balance but my card was charged",
    "When does the annual plan renew exactly?", "I upgraded mid-cycle, how is the proration calculated?", "Refund status for ticket #4410?",
    "The 'manage subscription' link in the email goes to a login loop (I just want to cancel)", "please charge the company card not my personal one",
    "Plan says unlimited projects but I was charged for 'extra projects'", "Our card expires next month, will you email a reminder?", "Can you backdate the invoice to Q3 for our books?",
    "Are prices going up in January? Saw a banner.", "I got a 'payment overdue' email but autopay is on", "What's the cost difference between Team and Business?",
    "Charged after deleting my account", "Invoice #10233 missing from the portal", "Does the free tier ever expire?",
    "I need a quote for 50 seats", "Why is there a $1 'verification' charge?", "Refund took 12 days, bank says nothing received", "Discount for paying 2 years up front?",
    "You billed the wrong entity, we have two workspaces", "Can I get itemized usage with my invoice?",
]
BUG = [
    "The export button crashes the app.", "Dashboard shows a blank page after login on Safari", "Uploads over 10MB fail silently",
    "search returns nothing even for exact matches since yesterday", "Getting 500 errors on /api/reports every few minutes",
    "The mobile app logs me out every time I rotate the phone", "Dark mode makes the chart labels invisible", "CSV import drops the last row",
    "Notifications arrive twice", "Can't type in the comment box on Firefox, cursor jumps to the start", "Date picker shows 31st for February",
    "My saved filters disappeared after the update", "Keyboard shortcut Cmd+K opens two dialogs", "Password reset link says expired immediately",
    "The PDF export has overlapping text on page 2", "Timezone is off by one hour in the calendar view", "App freezes when I paste a long URL",
    "Images in shared links show as broken thumbnails", "Sorting by name is case-sensitive, lowercase names go to the bottom", "Webhook fires but the payload is empty {}",
    "error: 'undefined is not a function' when clicking Save", "Progress bar stuck at 99% for an hour", "Autosave overwrote my changes with an older version",
    "2FA code is never accepted, tried 5 codes", "Table header doesn't scroll with the table", "Emoji in project names break the breadcrumb",
    "The API returns 200 but the record isn't created", "Zoom out on the canvas and everything disappears", "Chrome extension icon greyed out after today's update",
    "spinner forever on the billing page (not a billing question, the page just won't load)", "Drag and drop reorders the wrong item", "Copy-paste from Excel loses formatting and merges cells",
    "Login with Google redirects to a 404", "Audio in recordings is 2 seconds behind the video", "The 'mark all read' button only marks the first 20",
    "Deleted item still shows in search results", "Text overlaps the sidebar on a 13 inch screen", "Export to Excel gives a corrupted file that won't open",
    "Rate limit error even though I made 3 requests", "Avatar upload rotates my photo 90 degrees", "Can't scroll the settings page on iPad",
    "Invite email contains a link to localhost", "API key regenerate button does nothing", "Sync between two devices stops after a few minutes",
    "Charts show last week's data labelled as this week", "Tab key skips the password field", "Markdown preview renders tables as plain text",
    "Hitting Enter submits the form before I've picked a date", "Comments on archived items throw 'permission denied' even for admins", "The app uses 100% CPU when idle",
    "Push notifications stopped on Android 15", "Pagination jumps from page 3 to page 7", "Integration with Slack posts to the wrong channel sometimes",
    "Can't delete a tag that has zero items", "Session expires after 5 minutes instead of the configured 8 hours", "Printing a report cuts off the right margin",
    "The undo button undoes two actions at once", "Dropdown closes before I can pick an option on touch screens", "File names with accents get garbled on download",
    "Getting 'network error' on a perfectly good connection, only your app", "Status page says all good but nothing loads for anyone in our office", "Trash can't be emptied, 'something went wrong'",
    "Columns I hid come back after refresh", "Hovering a tooltip makes the whole row flicker", "Numbers over 1,000 lose the comma in exports",
    "Shared link requires login even though 'anyone with link' is on", "Form validation says my email is invalid, it's a .io domain", "Clicking Back after saving creates a duplicate",
    "The new editor eats the first character I type", "App crashes on launch after iOS update, reinstall didn't help",
]
OTHER = [
    "Do you have an office in Berlin?", "Are you hiring frontend engineers?", "What's your SLA for the enterprise plan?",
    "Can I use your logo in my presentation?", "Is there a Linux desktop app?", "What's the difference between a workspace and a team?",
    "Do you integrate with Notion?", "Where can I find the API docs?", "how do i invite a teammate", "Is my data stored in the EU?",
    "Do you have a reseller program?", "What languages is the UI available in?", "Can I export all my data if I leave?",
    "Who do I talk to about a partnership?", "Is there a Zapier connector?", "What's your uptime over the last year?",
    "Can two people edit a document at the same time?", "Do you offer training sessions for new teams?", "Where is your privacy policy?",
    "I'm a journalist writing about remote work tools, could someone comment?", "Can I change my username?", "Is the roadmap public?",
    "Do you support SSO with Okta?", "How do I set up a custom domain?", "What file types can I upload?", "Is there a keyboard shortcuts cheat sheet?",
    "Can I get a demo for my team of 30?", "Do you have a status page?", "I love the product, just wanted to say thanks!", "Is there a dark mode?",
    "How do I archive a project without deleting it?", "What's the max number of collaborators?", "Can I schedule a report to email weekly?",
    "Do you have SOC 2?", "Are you planning a Windows ARM build?", "How do I change the language to Spanish?", "Can I merge two accounts?",
    "What happens to my data if you shut down?", "Is there an affiliate program?", "Does the mobile app work offline?",
    "Can I set different permissions per folder?", "Where do I report a security vulnerability?", "Do you have templates for sprint planning?",
    "How long do you keep deleted items?", "Can I import from Trello?", "Is there a public API rate limit?", "Who owns the content I upload?",
    "We're a university, do you have an education program?", "Can I white-label the client portal?", "What browsers do you support?",
    "I'd like to unsubscribe from marketing emails (not cancel my account)", "How do I transfer ownership of a workspace?", "Can your rep call me tomorrow at 3pm?",
    "Any plans for a Figma plugin?", "Do you store passwords in plain text? (asking for our security review)", "Is there a limit on file storage?",
    "How do I enable audit logs?", "Can I pin a comment?", "What time zone does the activity log use?", "I'm looking for the GDPR DPA document",
]

def noisy(s, r):
    """Apply a random style mutation to make the set realistic."""
    k = r.random()
    if k < 0.12: return s.lower()
    if k < 0.18: return s.upper()
    if k < 0.30: return s.rstrip(".?!") + "..."
    if k < 0.40: return "Hi, " + s[0].lower() + s[1:]
    if k < 0.50: return s + " Thanks."
    if k < 0.58: return s.replace("the ", "teh ", 1) if "the " in s else s.replace("you", "u", 1)
    if k < 0.66: return s + " This is urgent, we have a launch tomorrow."
    return s

items = [(m, "BILLING") for m in BILLING] + [(m, "BUG") for m in BUG] + [(m, "OTHER") for m in OTHER]
random.shuffle(items)
items = items[:200]
r = random.Random(7)
data = [{"id": i + 1, "message": noisy(m, r), "label": lab} for i, (m, lab) in enumerate(items)]
json.dump(data, open("test/messages_200.json", "w"), indent=1)
from collections import Counter
print(len(data), Counter(d["label"] for d in data))
