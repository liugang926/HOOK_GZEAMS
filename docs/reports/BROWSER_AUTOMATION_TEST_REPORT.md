# Browser Automation Test Report - Software Licenses Module

## Document Information
| Project | Description |
|---------|-------------|
| Report Version | v1.0 |
| Created Date | 2026-01-25 |
| Test Framework | Puppeteer (Node.js) |
| Test Scope | Frontend Software Licenses Module |

## Test Summary

### Overall Results
| Metric | Count |
|--------|-------|
| Total Tests | 7 |
| PASSED | 3 |
| FAILED | 3 |
| WARNED | 1 |

### Test Results Detail
| Test | Status | Notes |
|------|--------|-------|
| Navigate to homepage | PASS | Frontend loads correctly |
| User login | PASS | Login via direct API call works |
| Login API call | PASS | Backend `/api/auth/login/` returns 200 |
| Software Catalog page | FAIL | Redirects to login (proxy issue) |
| Licenses Management page | FAIL | Redirects to login (proxy issue) |
| Allocations page | FAIL | Redirects to login (proxy issue) |
| Console errors check | WARN | 2 errors due to proxy failure |

## Issues Discovered

### 1. Vite Proxy "Socket Hang Up" Error (Critical)
**Description**: The Vite dev server proxy fails to forward API requests to the Django backend with "socket hang up" errors.

**Symptoms**:
```
[vite] http proxy error: /api/auth/login/
Error: socket hang up
```

**Impact**:
- All API calls through the Vite proxy (port 5173/5174) fail
- Frontend login form cannot authenticate through normal flow
- Frontend initialization API calls (`/api/users/me/`) fail

**Workaround Applied**:
- Test script makes direct API calls to backend (port 8000)
- `CORS_ALLOW_ALL_ORIGINS = True` added to Django settings
- Token stored directly in localStorage via page.evaluate()

**Root Cause**:
The Django development server appears to be closing connections prematurely when receiving requests from the Vite proxy. Direct curl requests to port 8000 work fine, but proxied requests fail.

### 2. Missing Login Endpoint (Fixed)
**Description**: Frontend expected `/api/auth/login/` endpoint which didn't exist.

**Fix Applied**: Added custom `LoginView` in `backend/apps/accounts/urls.py`
```python
class LoginView(APIView):
    """Custom login view that returns the response format expected by the frontend."""
    permission_classes = [AllowAny]
    # ... implementation
```

### 3. CORS Configuration (Fixed)
**Description**: CORS blocked requests from frontend to backend.

**Fixes Applied**:
- Added `CORS_ALLOW_ALL_ORIGINS = True` to `backend/config/settings/base.py`
- Added ports 5173 and 5174 to `CORS_ALLOWED_ORIGINS`
- Added `x-organization-id` to `CORS_ALLOW_HEADERS`

## Test Environment

### Browser Automation
- **Tool**: Puppeteer for Node.js
- **Version**: Latest installed via npm
- **Headless Mode**: False (for debugging)
- **Viewport**: 1280x720

### Services Running
| Service | Port | Status |
|---------|------|--------|
| Frontend (Vite) | 5174 | Running |
| Backend (Django) | 8000 | Running |
| PostgreSQL | 5432 | Running |
| Redis | 6379 | Running |

## Files Modified During Testing

### Backend
1. `backend/config/settings/base.py`
   - Added `CORS_ALLOW_ALL_ORIGINS = True`
   - Added ports 5173/5174 to `CORS_ALLOWED_ORIGINS`
   - Added `USE_X_FORWARDED_HOST`, `USE_X_FORWARDED_PORT`
   - Added `x-organization-id`, `x-csrftoken` to `CORS_ALLOW_HEADERS`

2. `backend/apps/accounts/urls.py`
   - Added custom `LoginView` class
   - Registered `/login/` endpoint

### Frontend
1. `frontend/vite.config.ts`
   - Added proxy event handlers for debugging
   - Added `ws: true`, `secure: false` options

### Test Scripts
1. `run_puppeteer_test.js` - Created Puppeteer browser automation test

## Recommendations

### Immediate Fixes Required
1. **Resolve Vite Proxy Issue**: Investigate why Django development server is dropping connections from Vite proxy
   - Check for middleware that may be rejecting proxy requests
   - Try using Gunicorn or uWSGI instead of Django's runserver
   - Consider using nginx as a reverse proxy

2. **Use Production WSGI Server**: Django's runserver is not recommended for proxy setups
   - Switch to Gunicorn with proper worker configuration
   - This may resolve the "socket hang up" issue

### Future Improvements
1. Add e2e tests with Playwright for better cross-browser support
2. Set up proper CI/CD integration with automated browser tests
3. Add visual regression testing for UI components

## Screenshots

All screenshots saved to: `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\test_screenshots\`
- 01_homepage.png
- 02_credentials_filled.png
- 03_after_login.png
- 04_software_catalog.png
- 05_licenses.png
- 06_allocations.png

## Conclusion

The browser automation testing infrastructure is now functional using Puppeteer. The login endpoint works correctly when called directly. However, the Vite proxy issue prevents normal frontend-backend communication in development. This issue needs to be resolved for proper development workflow.

**Direct API Access**: CONFIRMED WORKING
- `POST http://localhost:8000/api/auth/login/` returns valid JWT token
- User data returned correctly
- Organization data included in response

**Proxy Access**: NOT WORKING
- All requests through `http://localhost:5174/api/*` fail with 500 error
- Root cause: "socket hang up" between Vite proxy and Django backend
