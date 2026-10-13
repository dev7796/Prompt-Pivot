# Level 2b real runs

All outputs quoted in the video come from these calls (Bedrock, us-east-1, `us.anthropic.claude-opus-5-5`
unless noted). `run_demos.py` produces the first nine rows; the `break_*` rows are the hallucination
attempts (five on Opus 5.5, one on Haiku 4.5). Full responses, including citation objects, are in
`results.json`. Assets in `assets/` are synthetic (matplotlib charts, reportlab PDFs) so the numbers
are known and checkable: the handbook has vacation on p.4, a $500 equipment allowance on p.3, and
no remote-work stipend anywhere.

## Finding: Opus 5.5 would not hallucinate the stipend
Five attempts (no permission sentence, no system prompt, citations off, a "helpful HR assistant,
always give a clear specific answer" system prompt, leading question) all answered "the handbook
doesn't describe a monthly remote-work stipend" and offered the one-time allowance as the nearest
real thing. Haiku 4.5 with the bad system prompt titled its answer "# Remote Work Stipend" and led
with the $500 figure before noting it is one-time. That is the drift the video shows.

The Files API is not available on Bedrock, so the Files demo output in the video is from the
base64 variant of the same request; the narration says so.

| run | model | in | out | stop | s |
|---|---|---|---|---|---|
| chart_trend | opus-5-5 | 796 | 234 | end_turn | 6.9 |
| chart_compare | opus-5-5 | 1607 | 400 | max_tokens | 11.6 |
| pdf_findings | opus-5-5 | 5559 | 591 | end_turn | 16.0 |
| cite_text | opus-5-5 | 863 | 27 | end_turn | 1.3 |
| cite_pdf | opus-5-5 | 6624 | 400 | max_tokens | 11.2 |
| hb_vacation_ok | opus-5-5 | 12160 | 200 | end_turn | 15.3 |
| hb_stipend_ok | opus-5-5 | 12160 | 520 | end_turn | 16.7 |
| hb_stipend_bad | opus-5-5 | 12150 | 523 | end_turn | 24.2 |
| break_a_bad_nocite_leading | claude-opus-5-5 | 10627 | 350 | max_tokens |  |
| break_b_nosys_nocite_leading | claude-opus-5-5 | 10617 | 350 | max_tokens |  |
| break_c_bad_cite_leading | claude-opus-5-5 | 12156 | 350 | max_tokens |  |
| break_d_helpful_hr | claude-opus-5-5 | 10644 | 350 | max_tokens |  |
| break_e_haiku_bad_nocite | claude-haiku-4-5-20251 | 10261 | 136 | end_turn |  |
