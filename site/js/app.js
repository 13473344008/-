/* English UI copy is centralized for future locale dictionaries. No runtime dependencies. */
(() => {
  'use strict';
  const copy = {
    title: 'Product Record Not Found', missing: 'No batch number was provided.',
    invalid: 'Invalid batch number.', batchError: 'This batch record could not be loaded.',
    productError: 'The product record for this batch could not be loaded.',
    fields: { product_code: 'Product Code', product_name: 'Product Name', product_name_zh: 'Chinese Name',
      category: 'Category', country_of_origin: 'Country of Origin', manufacturer: 'Manufacturer',
      batch: 'Batch Number', production_date: 'Production Date', expiry_date: 'Expiry Date', status: 'Status',
      record_updated: 'Record Updated', record_type: 'Record Type', name: 'Name', type: 'Type', origin: 'Origin',
      description: 'Description', raw_material_batch: 'Raw Material Batch', raw_material_origin: 'Batch Raw Material Origin',
      package_size: 'Package Size', package_type: 'Package Type', inner_material: 'Inner Material',
      storage_conditions: 'Storage Conditions', shelf_life: 'Shelf Life', certificate_number: 'Certificate Number',
      valid_from: 'Valid From', valid_until: 'Valid Until' }
  };
  const app = document.getElementById('app');
  const forbiddenCodeCharacter = /[^A-Za-z0-9_-]/;
  const object = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const list = value => Array.isArray(value) ? value : [];
  const valueText = value => (typeof value === 'string' && value.trim() && !['undefined', 'null', 'NaN'].includes(value.trim())) || (typeof value === 'number' && Number.isFinite(value)) ? String(value) : '—';
  const escapeHtml = value => valueText(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const validCode = value => typeof value === 'string' && value.length > 0 && !forbiddenCodeCharacter.test(value);
  const badge = value => `<span class="badge">${escapeHtml(value)}</span>`;
  const fields = (input, keys) => {
    const data = object(input);
    return `<dl class="fields">${keys.map(key => `<div class="field"><dt>${copy.fields[key]}</dt><dd>${key === 'status' ? badge(data[key]) : escapeHtml(data[key])}</dd></div>`).join('')}</dl>`;
  };
  // Allow only local raster assets; no remote URLs, SVG, traversal or active URL schemes.
  const asset = (path, alt) => typeof path === 'string' && /^\/?assets\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_-]+\.(?:png|jpe?g|webp|gif)$/i.test(path)
    ? `<img class="asset" src="/${escapeHtml(path.replace(/^\//, ''))}" alt="${escapeHtml(alt)}" loading="lazy">` : '';
  const section = (number, title, content, wide = false) => `<section class="section${wide ? ' wide' : ''}"><h2><span>${number}</span>${title}</h2>${content}</section>`;
  function showError(message) {
    app.innerHTML = `<div class="error" role="alert"><p class="eyebrow">RECORD LOOKUP</p><h1>${copy.title}</h1><p>${escapeHtml(message)}</p></div>`;
  }
  function render(product, batch) {
    const identity = object(product.identity);
    const inspection = list(batch.inspection);
    const certifications = list(product.certifications);
    const columns = [['name','Parameter'],['specification','Specification'],['result','Result'],['unit','Unit'],['status','Status']];
    const inspectionTable = inspection.length ? `<table aria-label="Quality Inspection"><thead><tr>${columns.map(([,label]) => `<th scope="col">${label}</th>`).join('')}</tr></thead><tbody>${inspection.map(item => `<tr>${columns.map(([key,label]) => `<td data-label="${label}"><span>${key === 'status' ? badge(object(item)[key]) : escapeHtml(object(item)[key])}</span></td>`).join('')}</tr>`).join('')}</tbody></table>` : '<p>No inspection data provided.</p>';
    app.innerHTML = `<div class="hero"><div><p class="eyebrow">PRODUCT & BATCH RECORD</p><h1>${escapeHtml(identity.product_name)}</h1><p class="chinese" lang="zh">${escapeHtml(identity.product_name_zh)}</p><div class="hero-meta"><div><small>BATCH NUMBER</small><strong>${escapeHtml(batch.batch)}</strong></div><div><small>STATUS</small>${badge(batch.status)}</div></div><p class="intro-note">Test template only. Production details and inspection results have not been supplied. Empty fields do not imply verification or compliance.</p></div>${asset(identity.product_image, identity.product_name)}</div>
    <div class="record-grid">
    ${section('01','Product Identity', fields(identity,['product_code','product_name','product_name_zh','category','country_of_origin']) + `<p>${escapeHtml(object(product.description).short_description)}</p>`)}
    ${section('02','Batch Information',fields(batch,['batch','record_type','production_date','expiry_date','status','record_updated']))}
    ${section('03','Raw Material',fields(product.raw_material,['name','type','origin','description']) + fields(batch.raw_material_traceability,['raw_material_batch','raw_material_origin']))}
    ${section('04','Manufacturing Process',`<ol class="process">${list(product.manufacturing_process).map(step => `<li>${escapeHtml(step)}</li>`).join('')}</ol><p>Reference process for this template; not a verified batch production log.</p>`)}
    ${section('05','Quality Inspection','<p>TEST RECORD · No real COA results supplied. NOT_TESTED means no test result is recorded.</p>' + inspectionTable,true)}
    ${section('06','Packaging & Storage',fields(product.packaging,['package_size','package_type','inner_material','storage_conditions','shelf_life']),true)}
    ${section('07','Certifications',`<p>Template entries only. These names do not confirm certification of the product or manufacturer.</p><div class="certificates">${certifications.map(item => { const cert = object(item); return `<article class="certificate"><h3>${escapeHtml(cert.name)}</h3>${fields(cert,['certificate_number','valid_from','valid_until','status'])}${asset(cert.image,cert.name)}</article>`; }).join('') || '<p>No certification information provided.</p>'}</div>`,true)}
    ${section('08','Manufacturer',fields(identity,['manufacturer']),true)}</div>`;
    app.querySelectorAll('img').forEach(img => img.addEventListener('error', () => {
      const fallback = document.createElement('p');
      fallback.className = 'asset-fallback';
      fallback.textContent = 'Image unavailable.';
      img.replaceWith(fallback);
    }));
  }
  async function readJson(path) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(path, { signal: controller.signal, cache: 'no-store' });
      if (!response.ok) throw new Error('Record response was not successful.');
      const data = await response.json();
      if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('Invalid record shape.');
      return data;
    } finally { clearTimeout(timer); }
  }
  async function start() {
    try {
      const params = new URLSearchParams(location.search);
      let batchCode = params.get('batch');
      // Frontend compatibility only: server must explicitly support /b/{code} fallback.
      if (location.pathname.startsWith('/b/')) {
        try { batchCode = decodeURIComponent(location.pathname.slice(3)); } catch { return showError(copy.invalid); }
        if (params.has('batch')) return showError(copy.invalid);
      }
      if (params.getAll('batch').length > 1) return showError(copy.invalid);
      if (batchCode === null || batchCode === '') return showError(copy.missing);
      if (!validCode(batchCode)) return showError(copy.invalid);
      let batch;
      try {
        batch = await readJson(`/batches/${batchCode}.json`);
        if (batch.batch !== batchCode || !validCode(batch.product_code) || !['test','commercial'].includes(batch.record_type)) throw new Error('Invalid batch identity.');
      } catch (error) { console.warn('Batch loading failed:', error); return showError(copy.batchError); }
      let product;
      try {
        product = await readJson(`/products/${batch.product_code}.json`);
        if (object(product.identity).product_code !== batch.product_code || valueText(object(product.identity).product_name) === '—') throw new Error('Invalid product identity.');
      } catch (error) { console.warn('Product loading failed:', error); return showError(copy.productError); }
      render(product,batch);
    } catch (error) { console.warn('Record rendering failed:', error); showError(copy.batchError); }
    finally { app.setAttribute('aria-busy','false'); }
  }
  start();
})();
