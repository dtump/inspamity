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
  - `confidence`: A score from 0-100 indicating certainty
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

# Set proper permissions
sudo chmod +x /usr/local/inspamity/email_ai_interface.py
sudo chmod +x /usr/local/inspamity/cli_toolbox.py

# Create a virtual environment and install dependencies
sudo python3 -m venv /usr/local/inspamity/.venv
sudo /usr/local/inspamity/.venv/bin/pip install /usr/local/inspamity
```

### Step 2: Install the rspamd integration

```bash
# Copy the Lua script to rspamd's configuration directory
sudo cp /usr/local/inspamity/rspamd/external_ai_test.lua /etc/rspamd/plugins.d/

# Create /etc/rspamd/modules.d/external_ai_test.conf
echo -e 'external_ai_test {\n   enabled = true;\n}' | sudo tee /etc/rspamd/modules.d/external_ai_test.conf

# Restart rspamd to apply changes
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

```bash
# Make directory for debugging data
mkdir /var/local/inspamity

# Make _rspamd owner of this directory
chown _rspamd: /var/local/inspamity
```

After this, enable debugging in the config.ini

## ⚙️ Configuration

By default, the rspamd Lua script is configured to:
- Run after all other checks (type postfilter)
- Skip emails already marked as spam
- Apply a score based on the AI's confidence level
- Log detailed information for debugging

You can adjust these settings by editing `/etc/rspamd/local.d/external_ai_test.lua` to fit your needs.

## 📊 How It Works

1. When rspamd processes an email, it passes the content to `external_ai_test.lua`
2. The Lua script executes `email_ai_interface.py` and passes the raw email via stdin
3. The Python script analyzes the email using AI techniques and returns a JSON response
4. Based on the response, rspamd adjusts the spam score accordingly
5. Detailed logging provides insights into the decision-making process

## 🐛 Troubleshooting

- Check rspamd logs for errors: `sudo tail -f /var/log/rspamd/rspamd.log`
- Test email processing directly: `/usr/local/inspamity/.venv/bin/python3 /usr/local/inspamity/email_ai_interface.py email.eml`
- Verify permissions on all scripts and directories
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
