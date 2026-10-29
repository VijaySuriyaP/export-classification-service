const API = `${window.location.protocol}//${window.location.hostname}:8000`;
const form = document.getElementById('classify-form');
const output = document.getElementById('result');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

form.addEventListener('submit', async event => {
  event.preventDefault();
  output.textContent = 'Submitting…';
  const payload = {
    client_request_id: crypto.randomUUID(),
    product_description: document.getElementById('description').value,
    materials: [document.getElementById('materials').value],
    intended_use: document.getElementById('use').value || null,
    destination_country: document.getElementById('country').value,
    client_id: document.getElementById('client').value
  };
  try {
    const submitted = await fetch(`${API}/v1/classify`, {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)});
    const body = await submitted.json();
    if (!submitted.ok) throw new Error(JSON.stringify(body, null, 2));
    output.textContent = JSON.stringify(body, null, 2);
    for (let attempt = 0; attempt < 120; attempt++) {
      await sleep(500);
      const response = await fetch(`${API}/v1/runs/${body.run_id}`);
      const result = await response.json();
      output.textContent = JSON.stringify(result, null, 2);
      if (['completed','failed_escalated'].includes(result.status)) break;
    }
  } catch (error) {
    output.textContent = `Request failed: ${error.message}`;
  }
});
