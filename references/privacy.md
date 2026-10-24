# Client privacy

The user's rule: client website URLs, Pixel IDs, GTM IDs, Google tag IDs and every other credential are blurred
wherever they appear — and the client contact's name and photo. HyperFrames' own blur treats a whole video layer,
so region blur is baked into the screen footage itself (its guidance for hiding a region: a separate asset).

## What to hide
**Always (automatic patterns in `ocr_redact.swift`):**
| Kind | Examples |
|---|---|
| Google Tag Manager | `GTM-XXXXXXX` (web + server containers), account/container numbers in URLs/headers |
| Google tags | GA4 `G-…`, Google tag `GT-…`, Ads `AW-…` and `AW-…/label`, Floodlight `DC-…`, GA4 property numbers |
| Google Ads | customer IDs `123-456-7890` and bare 10-digit, conversion IDs/labels, conversion action resource names |
| Pixels | Meta/Facebook pixel & dataset IDs (15–16 digits), TikTok `C…` (20 chars), Snapchat UUIDs, Pinterest tag, LinkedIn partner ID, Microsoft UET tag (short IDs: caught when labelled "… ID:") |
| Tokens & keys | Meta access tokens `EAA…`, Stripe `sk_/pk_/rk_live…`, `whsec_`, Google API `AIza…`, OAuth `ya29.`, AWS `AKIA…`, GitHub `ghp_…`, Slack `xox…`, Shopify `shpat_…`, JWTs `eyJ…`, any 28+ char token with digits, values after "API key / access token / secret / password" |
| Client web | every URL/domain/slug containing a client term (site, staging, old platform, payment gateway, server-side endpoint such as `*.stape.io`), and every other `https://` URL |
| People | phone numbers, emails (his own too), IP addresses, any 9+ digit number (order IDs, user IDs, account numbers) |
| Named people | from `redact_terms.json → names`: full name and each part; at line start (WhatsApp list, chat header) the profile photo and preview line too |
| Edge lines | text cut by the top/bottom edge containing ID-like characters (OCR can't read half lines; viewers can) + a 28 px blur strip along the bottom edge |

**Check by eye — patterns can't see these:** desktop notification banners (WhatsApp/Slack/mail popups with other
people's messages), other clients in chat lists or project sidebars, invoices/bank/payment screens, real customer
data in GA4 DebugView / Tag Assistant / dataLayer (emails, phones, addresses, order details), QR codes, other
people's faces/avatars in group chats, a second client mentioned in passing (the first project had Fitness First
ME in the same chat). Ask the user about business info he may want public or not (his prices in a proposal, a
client's company name in titles — he kept "IN2 Fitness" in the intro title but wanted the contact's name hidden).

**Talking-head videos** (no screen file): nothing is OCR'd — look at the camera sheets for papers, a phone
screen, a monitor or whiteboard behind him.

`privacy_report.py` writes `PRIVACY_REPORT.md` (what was blurred, how often, masked values, first/last time) —
include it with every delivery.

## redact_terms.json (per project, in work/)
```json
{
  "client_terms": ["in2fitness", "in2-fitness", "sentinelscope", "stape.io"],
  "names": ["Client Contact Name"]
}
```
Find terms in the transcript, the screen sheets and the OCR output itself: after the first OCR pass, list the most
frequent `url` / `number` / `longtoken` hits and every domain you see, and add any client-related term you missed
(old platforms, payment gateways, sister brands, server-side subdomains). Re-run OCR after changing terms.

## How the blur is made (and the leaks that shaped it)
1. Address bar, tabs and bookmarks are cropped off the screen recording before anything else.
2. OCR (Apple Vision, accurate) on every 5th frame of the edited screen footage (≈0.14 s/frame, 3 in parallel)
   and every frame of the intro's screen clip.
3. `redact_bake.py`: each detection held ±7 frames; the same token found in two samples ≤ 1 s apart → the whole
   area it **swept through** is blurred for the frames between. (A straight-line guess lagged an eased scroll and
   left two Google Ads IDs half visible in a shipped render — never go back to interpolation.)
4. Boxes padded by text height (capped, so tall name+avatar boxes don't eat the sidebar), downsampled 10× and
   gaussian-blurred — unreadable at any zoom.
5. Pitfalls already fixed in the scripts: `ls` with 17k paths overflows (use `find`); paths contain spaces
   (split lists on newlines); Vision boxes for a match inside a multi-line block can sit on the wrong line (the
   whole block is blurred then); avatar offsets must convert height units to width units.

## Verify before every delivery
- OCR summary: count of hits per kind and the top texts (`ocr/body.jsonl`) — anything client-related missing?
- Frames **between** OCR samples (n % 5 = 2) at moments with known IDs: GTM tag lists, Ads conversion pages,
  pixel fields, reports with ID tables, WhatsApp chats.
- **Fast scrolls**: find moments with large activity in `activity.jsonl` over pages full of IDs and check 3–4
  consecutive frames at 1:1 crops.
- The bottom edge while documents scroll.
- Then the same spots in the **rendered** file (zooms scale the blur; it must still be unreadable).
If any ID is readable: fix, re-bake, re-render, re-check. Do not hand over the earlier file.
