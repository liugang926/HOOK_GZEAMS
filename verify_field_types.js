// Verify field types API
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
  console.log('=== Field Type Verification ===\n');

  // Step 1: Login
  console.log('1. Logging in...');
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
  console.log('   Token obtained:', token ? token.substring(0, 20) + '...' : 'N/A');

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
  console.log('\n3. Checking special fields...');
  const imageField = fields.find(f =>
    f.field_name === 'images' || f.fieldName === 'images' || f.code === 'images'
  );
  const attachmentField = fields.find(f =>
    f.field_name === 'attachments' || f.fieldName === 'attachments' || f.code === 'attachments'
  );

  if (imageField) {
    const type = imageField.field_type || imageField.fieldType;
    console.log(`   ✓ images field: ${type}`);
    if (type === 'image') {
      console.log('      Status: CORRECT ✓');
    } else {
      console.log('      Status: WRONG (expected: image)');
    }
  } else {
    console.log('   ✗ images field: NOT FOUND');
  }

  if (attachmentField) {
    const type = attachmentField.field_type || attachmentField.fieldType;
    console.log(`   ✓ attachments field: ${type}`);
    if (type === 'file') {
      console.log('      Status: CORRECT ✓');
    } else {
      console.log('      Status: WRONG (expected: file)');
    }
  } else {
    console.log('   ✗ attachments field: NOT FOUND');
  }

  // Step 4: List all fields with their types
  console.log('\n4. All fields with their types:');
  fields.forEach(f => {
    const name = f.field_name || f.fieldName || f.code || '?';
    const type = f.field_type || f.fieldType || '?';
    console.log(`   - ${name}: ${type}`);
  });

  console.log('\n=== Verification Complete ===');
}

main().catch(console.error);
