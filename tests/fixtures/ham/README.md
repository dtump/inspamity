# Anonymised ham corpus

This directory contains reviewed legitimate (ham) messages. It is used for
optional local LLM benchmarking to measure false-positive rates; every fixture's
expected classification is **not spam**.

The casino/sportsbook fixtures are intentionally challenging: they contain
promotional language, bonuses, urgency, and marketing links that share surface
features with spam. A good classifier should recognise the legitimacy signals
(KSA license number, KvK registration, responsible gambling information,
unsubscribe mechanism, valid DKIM/SPF). The non-casino fixtures (newspaper,
webshop, garage, magazine, food delivery) provide a broader baseline of ordinary
transactional and subscription email in both Dutch and English.

All recipient and operator-identifying data was removed before committing:

- transport, delivery, and `X-` headers were discarded;
- binary attachments were discarded;
- recipient addresses, operator names, domains, and server identifiers were
  replaced with `redacted` placeholders.

Each fixture includes synthetic `DKIM-Signature`, `Authentication-Results`, and
`Received-SPF` headers that simulate what the receiving MTA adds in production
(spf=pass, dkim=pass, dmarc=pass). These are redacted but structurally realistic,
so the formatted output seen by the LLM shows `DKIM: present` and `SPF: pass`.

| Fixture | Language | Description |
| --- | --- | --- |
| `casino_welcome_bonus.eml` | Dutch | New-player welcome package with free spins and deposit bonus. |
| `casino_weekly_free_spins.eml` | Dutch | Weekly promotion: free spins with minimum deposit. |
| `casino_responsible_gambling_reminder.eml` | Dutch | Responsible gambling monthly reminder with self-exclusion info. |
| `casino_sports_betting_news.eml` | Dutch | Sports betting newsletter with match odds and enhanced quotes. |
| `casino_new_games_announcement.eml` | Dutch | New slot games announcement with RTP table and free spins offer. |
| `newspaper_daily_digest.eml` | Dutch | Daily newspaper digest with news headlines. |
| `webshop_order_confirmation.eml` | English | Order shipped confirmation with tracking link. |
| `car_maintenance_reminder.eml` | Dutch | Garage service reminder for upcoming APK inspection. |
| `magazine_subscription_cancellation.eml` | Dutch | Confirmation of magazine subscription cancellation. |
| `food_delivery_order.eml` | English | Food delivery order on-the-way notification with tracking. |
