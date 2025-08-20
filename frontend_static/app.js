const form = document.getElementById('text-form');
const modeEl = document.getElementById('mode');
const toneField = document.getElementById('tone-field');
const toneEl = document.getElementById('tone');
const textEl = document.getElementById('text');
const textHelpEl = document.getElementById('text-help');
const submitBtn = document.getElementById('submit-btn');
const errorEl = document.getElementById('error');
const resultPanel = document.getElementById('result-panel');
const resultEl = document.getElementById('result');
const usageFloating = document.getElementById('usage-floating');
const usagePromptEl = document.getElementById('usage-prompt');
const usageCompletionEl = document.getElementById('usage-completion');
const usageTotalEl = document.getElementById('usage-total');
const copyBtn = document.getElementById('copy-btn');

modeEl.addEventListener('change', () => {
  const showTone = modeEl.value === 'rephrase';
  toneField.style.display = showTone ? 'block' : 'none';
});

copyBtn.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(resultEl.textContent);
    copyBtn.textContent = 'Copied!';
    setTimeout(() => (copyBtn.textContent = 'Copy'), 1000);
  } catch (_) {}
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validateLength()) { return; }
  clearError();
  setBusy(true);
  resultPanel.style.display = 'none';
  usageFloating.style.display = 'none';

  const payload = {
    mode: modeEl.value,
    text: textEl.value,
  };
  if (modeEl.value === 'rephrase') {
    payload.tone = toneEl.value;
  }

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      const message = data?.detail || 'Request failed. Please try again.';
      throw new Error(message);
    }

    // Render result
    let rendered = '';
    let isJsonRendered = false;
    if (modeEl.value === 'extract_json') {
      try {
        if (typeof data.result === 'string') {
          const obj = JSON.parse(data.result);
          rendered = JSON.stringify(obj, null, 2);
          isJsonRendered = true;
        } else {
          rendered = JSON.stringify(data.result, null, 2);
          isJsonRendered = true;
        }
      } catch (_) {
        rendered = String(data.result);
        isJsonRendered = false;
      }
    } else {
      rendered = String(data.result);
    }

    resultEl.textContent = rendered;
    if (isJsonRendered) {
      resultEl.classList.add('mono');
    } else {
      resultEl.classList.remove('mono');
    }
    resultPanel.style.display = 'block';

    // Usage
    usagePromptEl.textContent = data?.usage?.prompt_tokens ?? 0;
    usageCompletionEl.textContent = data?.usage?.completion_tokens ?? 0;
    usageTotalEl.textContent = data?.usage?.total_tokens ?? 0;
    usageFloating.style.display = 'block';
  } catch (err) {
    showError(err.message || 'Something went wrong.');
  } finally {
    setBusy(false);
  }
});

function setBusy(busy) {
  submitBtn.disabled = busy;
  submitBtn.textContent = busy ? 'Running…' : 'Run';
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.style.display = 'block';
}

function clearError() {
  errorEl.textContent = '';
  errorEl.style.display = 'none';
}

// Live length validation
textEl.addEventListener('input', validateLength);
validateLength();

function validateLength() {
  const len = textEl.value.length;
  const max = 5000;
  const min = 1;
  const valid = len >= min && len <= max;
  textHelpEl.textContent = `${len} / ${max}`;
  textHelpEl.classList.toggle('error', !valid);
  submitBtn.disabled = !valid;
  return valid;
}
