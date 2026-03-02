import { test, expect } from '@playwright/test';

test('Check business objects via API', async ({ request }) => {
  // First login to get token
  const loginResponse = await request.post('http://localhost:8000/api/auth/login/', {
    data: {
      username: 'admin',
      password: 'admin123'
    }
  });

  const loginData = await loginResponse.json();
  console.log('Login response:', JSON.stringify(loginData, null, 2));

  const token = loginData.data?.token || loginData.token;
  console.log('Token:', token ? 'Received' : 'Not received');

  if (!token) {
    console.error('Failed to get authentication token');
    return;
  }

  // Get all business objects
  const boResponse = await request.get('http://localhost:8000/api/system/business-objects/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  console.log('\n=== Business Objects Response ===');
  console.log('Status:', boResponse.status());
  const boData = await boResponse.json();
  console.log('Data:', JSON.stringify(boData, null, 2));

  // Check for AssetTransfer specifically
  const assetTransfer = boData.data?.results?.find((obj: any) => obj.code === 'AssetTransfer');
  console.log('\n=== AssetTransfer Business Object ===');
  console.log('Found:', assetTransfer ? 'YES' : 'NO');
  if (assetTransfer) {
    console.log('Details:', JSON.stringify(assetTransfer, null, 2));
  }

  // Try to get page layouts for AssetTransfer
  const layoutResponse = await request.get('http://localhost:8000/api/system/page-layouts/by-object/AssetTransfer/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  console.log('\n=== Page Layouts for AssetTransfer ===');
  console.log('Status:', layoutResponse.status());
  const layoutData = await layoutResponse.json();
  console.log('Data:', JSON.stringify(layoutData, null, 2));
});
