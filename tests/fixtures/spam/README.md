# Anonymised spam corpus

This directory contains 20 reviewed spam messages from July 2026.  It is a
small, intentionally varied regression corpus for email parsing and optional
local LLM benchmarking; every fixture's expected classification is **spam**.

The source messages were selected as single representatives of their campaign.
Near-identical deliveries (including messages differing only in recipient,
transport headers, timestamps, or tracking identifiers) were excluded.

All recipient and mail-server data was removed before committing the fixtures:

- transport, authentication, delivery, and `X-` headers were discarded;
- binary attachments were discarded;
- recipient addresses, domains, names, and server IP addresses were replaced
  in decoded headers and text/HTML MIME parts.

| Fixture | Review rationale |
| --- | --- |
| `advance_fee_confidential_transaction.eml` | Vague lucrative confidential-transaction offer to undisclosed recipients. |
| `advance_fee_fake_donation.eml` | Unsolicited EUR 4.5 million donation with a generic reply address. |
| `advance_fee_fake_police_notice.eml` | Impersonates police/Europol to solicit a response. |
| `advance_fee_fintrac_funds.eml` | FINTRAC-held-funds impersonation with an unrelated sender/reply address. |
| `advance_fee_lottery_winner.eml` | Unsolicited lottery award and direct reply request. |
| `phishing_benu_security_update.eml` | BENU security impersonation from an unrelated domain. |
| `phishing_bitvavo_address_check.eml` | Bitvavo lookalike domain requesting an address check. |
| `phishing_cloud_storage_payment.eml` | Generic cloud-payment suspension threat with unrelated links. |
| `phishing_cloud_storage_renewal.eml` | Fake cloud-renewal expiry threat from an unrelated domain. |
| `phishing_coinmerce_mica.eml` | Coinmerce/MiCA verification lure pointing to an unrelated target. |
| `phishing_fake_card_transaction.eml` | Fake card transaction/security-alert social engineering. |
| `phishing_fake_cjib_fine.eml` | CJIB fine impersonation with unrelated sender and payment link. |
| `phishing_fake_coinbase_deposit.eml` | Unsolicited 18 BTC deposit notification with unrelated link. |
| `phishing_fake_document_signature.eml` | Urgent document-signature impersonation. |
| `phishing_fake_domain_termination.eml` | Fake domain termination/renewal notice. |
| `phishing_fake_rvo_subsidy.eml` | RVO subsidy lure from an unrelated sender. |
| `phishing_icloud_billing.eml` | Fake iCloud billing suspension with a short action deadline. |
| `phishing_raiffeisen_pushtan.eml` | Raiffeisen pushTAN impersonation with unrelated links. |
| `spam_wordpress_credential_injection.eml` | WordPress login message whose credentials contain crypto bait. |
| `unsolicited_prescription_drugs.eml` | Unsolicited prescription-drug sales link. |
