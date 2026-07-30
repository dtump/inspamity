# Inspamity: AI-Powered Spam Detection at the Edge

## 🚀 Welcome to Inspamity!

Tired of the never-ending battle with increasingly sophisticated spam? Frustrated with conventional spam filters that can't keep up with modern phishing attempts? **Inspamity** brings sanity back to your inbox by combining the power of AI with the speed and reliability of rspamd!

Inspamity harnesses cutting-edge AI to analyze emails with human-like understanding, catching even the most cunning spam that traditional rule-based systems miss. By seamlessly integrating with rspamd, it delivers this intelligence without sacrificing performance or adding complexity to your email infrastructure.

## 🤔 Why Another Implementation?

While rspamd already offers a GPT plugin, Inspamity was born from a different vision. I wanted to create a more versatile solution that wasn't tied to a single email filtering system. By designing Inspamity as a standalone tool with a clean interface, it can be integrated not just with rspamd, but with any email filtering system that can execute external scripts.

Additionally, I had specific ideas about email pre-processing that I wanted to implement. This custom approach allows for more control over how emails are parsed and analyzed before they're sent to the AI model, potentially improving detection accuracy while reducing unnecessary API usage.

## 📋 Components

### email_ai_interface.py

This script acts as the bridge between your MTA or existing spam filter and AI-powered analysis. It:

- Receives raw email content via stdin or file
- Processes the email content using advanced AI techniques
- Evaluates the likelihood of the email being spam
- Returns a JSON response with:
  - `is_spam`: "yes" or "no" classification
  - `confidence`: Confidence from 0-100 in the selected `is_spam` classification
  - `reason`: Human-readable explanation for the classification

### cli_toolbox.py

A convenient command-line tool that lets you:

- Test emails against the AI detection engine directly from your terminal
- Analyze email files: `cli_toolbox.py /path/to/email.eml`
- Get detailed analysis reports with detection confidence and reasoning

Perfect for testing, debugging, or manual verification of suspicious emails.

## 🔧 Installation

### Step 1: Install Inspamity

```bash
# Create the installation directory
sudo mkdir -p /usr/local/inspamity

# Clone the repository (or copy your files)
sudo git clone https://github.com/dtump/inspamity.git /usr/local/inspamity

# Set executable permissions
sudo chmod 0755 /usr/local/inspamity/email_ai_interface.py
sudo chmod 0755 /usr/local/inspamity/cli_toolbox.py

# Create a virtual environment and install dependencies
sudo python3 -m venv /usr/local/inspamity/.venv
sudo /usr/local/inspamity/.venv/bin/pip install /usr/local/inspamity

# Create system config and private debug locations
sudo install -d -o root -g _rspamd -m 0750 /etc/inspamity
sudo install -d -o _rspamd -g _rspamd -m 0700 /var/local/inspamity
sudo cp /usr/local/inspamity/config.ini.default /etc/inspamity/config.ini
sudo chown root:_rspamd /etc/inspamity/config.ini
sudo chmod 0640 /etc/inspamity/config.ini
```

### Step 2: Install the rspamd integration

```bash
# Copy the Lua script to rspamd's configuration directory
sudo cp /usr/local/inspamity/rspamd/external_ai_test.lua /etc/rspamd/plugins.d/

# Copy the module configuration
sudo cp /usr/local/inspamity/rspamd/external_ai_test.conf /etc/rspamd/modules.d/

# Verify rspamd config, then restart rspamd to apply changes
sudo rspamadm configtest
sudo systemctl restart rspamd
```

### Step 3: Verify Installation

```bash
# Test the CLI tool with a sample email
/usr/local/inspamity/.venv/bin/python3 /usr/local/inspamity/cli_toolbox.py /path/to/test-email.eml

# Check rspamd logs to verify integration
sudo tail -f /var/log/rspamd/rspamd.log
```

### Step 4: Enable debugging

Debug mode can save raw email, processed email, AI output, and error logs. Treat these files as private mail data.

```bash
# The installation step above creates this directory; these commands are safe to re-run.
sudo install -d -o _rspamd -g _rspamd -m 0700 /var/local/inspamity
```

After this, set `debug_mode = true` in `/etc/inspamity/config.ini` if you really need debug artifacts. Inspamity creates new debug files with mode `0600`.

## ⚙️ Configuration

Copy `config.ini.default` to `/etc/inspamity/config.ini` for system-wide production use and edit it. Keep it readable only by root and the rspamd runtime user because it contains provider API keys:

```bash
sudo chown root:_rspamd /etc/inspamity/config.ini
sudo chmod 0640 /etc/inspamity/config.ini
sudo -u _rspamd test -r /etc/inspamity/config.ini
```

```ini
[settings]
# AI provider: anthropic, openai, or mistral
provider = anthropic
# Save private debug artifacts under debug_directory when true
debug_mode = false
debug_directory = /var/local/inspamity

[anthropic]
api_key = your_api_key_here
model = claude-haiku-4-5-latest
temperature = 0.0
timeout = 20.0

[openai]
api_key = your_api_key_here
model = gpt-5.6-luna
# GPT-5-class models do not support temperature; leave it unset for those models.
# temperature = 0.0
timeout = 20.0

[mistral]
api_key = your_api_key_here
model = mistral-large-2512
# Inference endpoint: global or eu. The us endpoint is configurable but not available yet.
endpoint = global
max_tokens = 256
temperature = 0.0
timeout = 20.0
```

### Supported Providers

| Provider | Default Model | Config Section |
|----------|--------------|----------------|
| Anthropic | `claude-haiku-4-5-latest` | `[anthropic]` |
| OpenAI | `gpt-5.6-luna` | `[openai]` |
| Mistral | `mistral-large-2512` (Mistral Large 3) | `[mistral]` |

Set `provider` in `[settings]` to switch between them. Only the selected provider's API key is required.

For Mistral, `endpoint` defaults to `global`. Set it to `eu` to keep inference processing in
EU/EFTA data centers. The `us` endpoint can also be configured, but Mistral currently lists it as
coming soon. Regional endpoints may offer a different subset of models than the global endpoint.
`max_tokens` defaults to `256`; this allows enough room for a complete JSON response while remaining
a generation limit rather than a request to produce that many tokens.

### rspamd Integration

By default, the rspamd Lua script is configured to:
- Run after all other checks (type postfilter)
- Skip emails already marked as spam
- Apply a score based on the AI's confidence level
- Emit zero-score verdict symbols for local policy and composite rules
- Log detailed information for debugging

The plugin preserves `EXTERNAL_AI_TEST` as its scoring symbol and adds these
informational symbols:

- `EXTERNAL_AI_SPAM` for every spam verdict;
- `EXTERNAL_AI_SPAM_HIGH` when a spam verdict meets `high_spam_confidence`;
- `EXTERNAL_AI_HAM` for every ham verdict.

All three verdict symbols have score zero and cannot change the message action
by themselves. Their `confidence=<number>` option can be inspected in rspamd
logs and scan output. They allow site-specific composites to require an AI
verdict together with independent rspamd evidence instead of making the AI the
sole decision maker.

`high_spam_confidence` defaults to `95` when omitted. Values are clamped to the
AI response range of 0 through 100. Adjust it in
`/etc/rspamd/modules.d/external_ai_test.conf`; no plugin source edit is needed.

## 📊 How It Works

1. When rspamd processes an email, it passes the content to `external_ai_test.lua`
2. The Lua script executes `email_ai_interface.py` and passes the raw email via stdin
3. The Python script analyzes the email using AI techniques and returns a JSON response
4. Based on the response, rspamd adjusts the spam score accordingly
5. The plugin emits a zero-score spam or ham verdict symbol for local policy
6. Detailed logging provides insights into the decision-making process

## 🧪 Testing and spam corpus

The regular test suite includes an anonymised, reviewed corpus of 20 distinct
spam campaigns in `tests/fixtures/spam/`. It exercises email parsing and
formatting without calling an LLM, and verifies that recipient and mail-server
identifiers are not present in the committed fixtures:

```bash
.venv/bin/pytest -v
```

For an opt-in local provider benchmark, create the ignored `config.ini` in the
project root with only these required settings:

```ini
[settings]
provider = openai

[openai]
api_key = your_api_key_here
model = your_model_id
```

Replace `openai` and `[openai]` with `anthropic`, `[anthropic]`, or `mistral`,
`[mistral]` to benchmark another supported provider.

`timeout`, `temperature`, and `max_tokens` are optional; the benchmark needs none of them. The
project's `config.ini` is ignored by Git, and `/etc/inspamity/config.ini`, when
present, takes precedence over it.

Run five fixtures by default:

```bash
INSPAMITY_RUN_LIVE_LLM=1 .venv/bin/pytest -m live_llm -v --durations=1 --log-cli-level=INFO
```

`--durations=1` only reports the single slowest test; it does not control the
number of API calls. `--log-cli-level=INFO` displays one line per LLM response
with its spam classification, confidence, reason, and duration. The default
benchmark makes five API calls. For a more representative run, increase the
number of corpus fixtures (up to 20), for example:

```bash
INSPAMITY_RUN_LIVE_LLM=1 INSPAMITY_LIVE_LLM_FIXTURE_COUNT=20 \
  .venv/bin/pytest -m live_llm -v --durations=20 --log-cli-level=INFO
```

If Mistral returns malformed or truncated JSON, the logged error includes its finish reason and a
bounded preview of the raw model response to make the failure diagnosable.

The live tests expect every reviewed fixture to be classified as spam. They are
skipped unless `INSPAMITY_RUN_LIVE_LLM=1` is set, so they never run in CI.

## 🐛 Troubleshooting

- Check rspamd logs for errors: `sudo tail -f /var/log/rspamd/rspamd.log`
- Test email processing directly: `/usr/local/inspamity/.venv/bin/python3 /usr/local/inspamity/email_ai_interface.py email.eml`
- Verify permissions on all scripts and directories:
  - `/etc/inspamity` should be `0750 root:_rspamd`
  - `/etc/inspamity/config.ini` should be `0640 root:_rspamd`
  - `/var/local/inspamity` should be `0700 _rspamd:_rspamd`
- Ensure all dependencies are properly installed

## 📜 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

### What this means:

- ✅ You are free to use, modify, and distribute this software
- ✅ You can use it within your organization, including commercial use
- ✅ If you modify the code, you must share those modifications back
- ❌ You cannot create closed-source commercial derivatives
- ❌ You cannot include this in proprietary software packages

The AGPL-3.0 is specifically designed to ensure that improvements to the code remain free and open. If someone wants to build upon Inspamity for commercial purposes, they must contribute their changes back to the community.

For the full license text, see the [LICENSE](LICENSE) file or visit: https://www.gnu.org/licenses/agpl-3.0.en.html

---

Brought to you by Dick Tump
