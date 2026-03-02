/**
 * MSW request handlers for API mocking
 */

import { http, HttpResponse } from 'msw'
import { mockBusinessObjects, mockFieldDefinitions, mockPageLayouts } from '../fixtures'

export const handlers = [
  // Business Objects API
  http.get('/api/system/business-objects/', () => {
    return HttpResponse.json({
      success: true,
      data: {
        results: mockBusinessObjects,
        count: mockBusinessObjects.length
      }
    })
  }),

  http.get('/api/system/business-objects/:id/', ({ params }) => {
    const obj = mockBusinessObjects.find(b => b.id === params.id)
    if (!obj) {
      return HttpResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Business object not found' } },
        { status: 404 }
      )
    }
    return HttpResponse.json({ success: true, data: obj })
  }),

  // Field Definitions API
  http.get('/api/system/field-definitions/', () => {
    return HttpResponse.json({
      success: true,
      data: {
        results: mockFieldDefinitions,
        count: mockFieldDefinitions.length
      }
    })
  }),

  http.get('/api/system/field-definitions/:id/', ({ params }) => {
    const field = mockFieldDefinitions.find(f => f.id === params.id)
    if (!field) {
      return HttpResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Field not found' } },
        { status: 404 }
      )
    }
    return HttpResponse.json({ success: true, data: field })
  }),

  // Page Layouts API
  http.get('/api/system/page-layouts/', () => {
    return HttpResponse.json({
      success: true,
      data: {
        results: mockPageLayouts,
        count: mockPageLayouts.length
      }
    })
  }),

  http.get('/api/system/page-layouts/:id/', ({ params }) => {
    const layout = mockPageLayouts.find(l => l.id === params.id)
    if (!layout) {
      return HttpResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Layout not found' } },
        { status: 404 }
      )
    }
    return HttpResponse.json({ success: true, data: layout })
  }),

  // Error Scenarios
  http.get('/api/system/error-500/', () => {
    return HttpResponse.json(
      { success: false, error: { code: 'SERVER_ERROR', message: 'Internal server error' } },
      { status: 500 }
    )
  })
]
