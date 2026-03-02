// Verify field types via API
const http = require('http');

const API_BASE = 'http://localhost:8000/api';

function makeRequest(options) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            data: JSON.parse(data)
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            data: data
          });
        }
      });
    });
    req.on('error', reject);
    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

async function main() {
  console.log('=== Field Type Verification via API ===\n');

  // Step 1: Login
  console.log('1. Logging in as admin...');
  const loginOptions = {
    hostname: 'localhost',
    port: 8000,
    path: '/api/auth/login/',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username: 'admin', password: 'admin123' })
  };

  const loginResult = await makeRequest(loginOptions);
  console.log('   Login status:', loginResult.status);

  if (loginResult.status !== 200) {
    console.log('   Login failed:', JSON.stringify(loginResult.data));
    return;
  }

  const token = loginResult.data.data?.access_token || loginResult.data.access_token;
  console.log('   Token obtained:', token ? token.substring(0, 30) + '...' : 'N/A');

  // Step 2: Get field definitions
  console.log('\n2. Fetching field definitions for Asset...');
  const fieldsOptions = {
    hostname: 'localhost',
    port: 8000,
    path: '/api/system/business-objects/fields/?object_code=Asset',
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  };

  const fieldsResult = await makeRequest(fieldsOptions);
  console.log('   Fields API status:', fieldsResult.status);

  const fields = fieldsResult.data?.data?.fields || fieldsResult.data?.fields || fieldsResult.data?.results || [];
  console.log('   Total fields:', fields.length);

  // Step 3: Check special fields
  console.log('\n3. Special Fields Check:');
  console.log('   ' + '='.repeat(50));

  const specialFields = ['images', 'attachments', 'qrCode'];
  const foundFields = {};

  fields.forEach(f => {
    const name = f.field_name || f.fieldName || f.code || '';
    const type = f.field_type || f.fieldType || '?';

    // Check for special fields
    if (name.toLowerCase().includes('image') && !name.toLowerCase().includes('thumbnail')) {
      foundFields.images = { name, type };
      const status = type === 'image' ? '✓ CORRECT' : '✗ WRONG';
      console.log(`   ${status} - ${name}: ${type}`);
    }

    if (name.toLowerCase().includes('attachment')) {
      foundFields.attachments = { name, type };
      const status = type === 'file' ? '✓ CORRECT' : '✗ WRONG';
      console.log(`   ${status} - ${name}: ${type}`);
    }

    if (name.toLowerCase().includes('qr') && name.toLowerCase().includes('code')) {
      if (!foundFields.qrCode) foundFields.qrCode = [];
      foundFields.qrCode.push({ name, type });
      const status = type === 'qr_code' ? '✓ CORRECT' : '⚠ CHECK';
      console.log(`   ${status} - ${name}: ${type}`);
    }
  });

  // Summary
  console.log('\n   ' + '='.repeat(50));
  console.log('4. Summary:');

  if (foundFields.images && foundFields.images.type === 'image') {
    console.log('   ✓ images field: CORRECT');
  } else if (foundFields.images) {
    console.log(`   ✗ images field: WRONG (${foundFields.images.type})`);
  } else {
    console.log('   ✗ images field: NOT FOUND');
  }

  if (foundFields.attachments && foundFields.attachments.type === 'file') {
    console.log('   ✓ attachments field: CORRECT');
  } else if (foundFields.attachments) {
    console.log(`   ✗ attachments field: WRONG (${foundFields.attachments.type})`);
  } else {
    console.log('   ✗ attachments field: NOT FOUND');
  }

  if (foundFields.qrCode && foundFields.qrCode.length > 0) {
    const allCorrect = foundFields.qrCode.every(f => f.type === 'qr_code');
    console.log(`   ${allCorrect ? '✓' : '⚠'} qr code fields: ${foundFields.qrCode.length} found`);
  } else {
    console.log('   - No QR code fields found');
  }

  console.log('\n=== Verification Complete ===');
}

main().catch(console.error);
