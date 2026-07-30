local rspamd_logger = require "rspamd_logger"
local ucl = require "ucl"

local options = rspamd_config:get_all_opt("external_ai_test") or {}
local high_spam_confidence = math.min(
    math.max(tonumber(options.high_spam_confidence) or 95, 0),
    100
)

local function check_with_external_script(task)
    local result = task:get_metric_result()

    if result then
        local score = result.score
        local action = result.action
        rspamd_logger.debug(task, "Score/action before AI check: score=%s, action=%s", score, action)

        -- Skip if already rejected
        if action == 'reject' then
            rspamd_logger.infox(task, "Skipping external check for already rejected message")
            return
        end
    end

    local python_path = "/usr/local/inspamity/.venv/bin/python3"
    local script_path = "/usr/local/inspamity/email_ai_interface.py"
    local raw_content = task:get_content() -- Full email including headers
    local content_str = tostring(raw_content)  -- Convert userdata to string

    -- Create a temporary file for the email content
    local tmp_file = os.tmpname()
    local file = io.open(tmp_file, "w")
    if not file then
        rspamd_logger.errx(task, "Failed to write temporary file: %s", tmp_file)
        return
    end
    file:write(content_str)  -- Write the string content instead
    file:close()

    -- Execute the script with explicit Python 3, capturing stdout and stderr
    local cmd = string.format("%s %s %s 2>&1", python_path, script_path, tmp_file)
    local handle = io.popen(cmd, "r")
    if not handle then
        rspamd_logger.errx(task, "Failed to execute script: %s", script_path)
        os.remove(tmp_file)
        return
    end

    local result_stdout = handle:read("*a") or ""
    local success, exit_type, exit_code = handle:close()
    os.remove(tmp_file) -- Clean up immediately after execution

    -- Log execution details
    rspamd_logger.debugx(task, "Executed %s, exit code: %s, output: %s", cmd, exit_code or "unknown", result_stdout)

    -- Check for execution errors
    if not success or (exit_code and exit_code ~= 0) then
        rspamd_logger.errx(task, "Script failed with exit code: %s, output: %s", exit_code or "unknown", result_stdout)
        return
    end

    -- Process the result
    if result_stdout and #result_stdout > 0 then
        local parser = ucl.parser()
        local ok, err = parser:parse_string(result_stdout)
        if not ok then
            rspamd_logger.errx(task, "Failed to parse JSON: %s, output: %s", err, result_stdout)
            return
        end

        local json_result = parser:get_object()
        local is_spam = (json_result.is_spam == "yes")
        local confidence = tonumber(json_result.confidence or 0) or 0
        local reason = json_result.reason or "No reason provided"

        -- Calculate score (confidence/10, range 0-10)
        local score = math.min(math.max(confidence / 10, 0), 10)
        if not is_spam then
            score = -score
        end

        rspamd_logger.debugx(
            task,
            "External check result: is_spam=%s, confidence=%s, score=%s, reason='%s'",
            json_result.is_spam,
            confidence,
            score,
            reason
        )

        -- Preserve the existing dynamic score and reason.
        task:insert_result("EXTERNAL_AI_TEST", score, reason)

        -- Emit zero-score verdict symbols so local rspamd policy can
        -- distinguish spam from ham without treating EXTERNAL_AI_TEST
        -- presence as a spam signal.
        local confidence_option = string.format("confidence=%s", confidence)
        if is_spam then
            task:insert_result("EXTERNAL_AI_SPAM", 1.0, confidence_option)
            if confidence >= high_spam_confidence then
                task:insert_result("EXTERNAL_AI_SPAM_HIGH", 1.0, confidence_option)
            end
        else
            task:insert_result("EXTERNAL_AI_HAM", 1.0, confidence_option)
        end
    else
        rspamd_logger.errx(task, "Script returned no output")
    end
end

-- Register the scoring symbol as a postfilter.
local external_ai_id = rspamd_config:register_symbol({
    name = "EXTERNAL_AI_TEST",
    callback = check_with_external_script,
    type = "postfilter", -- This ensures it runs after other filters
    priority = 1,
    score = 1.0   -- Set a non-zero base score to enable dynamic scoring
})

-- These child symbols are informational. Their configured score is zero;
-- the weight supplied to insert_result does not change the message score.
for _, symbol in ipairs({
    "EXTERNAL_AI_SPAM",
    "EXTERNAL_AI_SPAM_HIGH",
    "EXTERNAL_AI_HAM",
}) do
    rspamd_config:register_symbol({
        name = symbol,
        parent = external_ai_id,
        type = "virtual",
        score = 0.0,
        flags = "empty",
        group = "external_ai",
    })
end
